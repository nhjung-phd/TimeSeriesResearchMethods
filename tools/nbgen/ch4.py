from .cells import md, code
from .common import SETUP
from .data_cells import LOADERS

WHICH = {"Finance": "", "RealEstate": "price", "Manufacturing": "demand", "PublicPolicy": "complaints",
         "EnergyEnvironment": "demand", "BusinessMarketing": ""}
HORIZON = {"Finance": 20, "RealEstate": 12, "Manufacturing": 28, "PublicPolicy": 28, "EnergyEnvironment": 28, "BusinessMarketing": 28}

THEORY = r'''
## 1. 핵심 개념·수식

**Zero-shot 예측:** 대상 시계열로 **재학습하지 않고** 사전학습된 모델에 과거 문맥 $y_{1:T}$만 주어 $\hat y_{T+1:T+H}$를 얻는다. 이 노트북은 사전학습 모델이 설치되어 있으면 사용하고, 없으면 기준선만 실행한다(둘을 명확히 구분해 출력).

**롤링 오리진 평가:** 평가 기점 $T_k$를 여러 개 두고 각 기점에서 $H$ 단계 예측을 만든다. 지표는 $\mathrm{MASE}_k=\dfrac{\mathrm{MAE}_k}{\mathrm{MAE}_{\text{naive, in-sample}}}$의 평균.

**지수평활(SES):** $\ell_t=\alpha y_t+(1-\alpha)\ell_{t-1}$, 예측 $\hat y_{T+h}=\ell_T$. $\alpha$는 학습구간 1단계 제곱오차 최소화로 정한다.

**누수(오염) 주의:** 사전학습 말뭉치에 SPY·주택지수 같은 공개 시계열이 포함됐을 수 있다. 그러면 평가 구간이 "사전에 본" 자료일 가능성이 있으며, 이는 zero-shot 성능을 과대평가한다(확인 필요, 모델 카드 참조).
'''

BASELINES = r'''
H = @@H@@
LEVEL = y.astype(float)
n_orig = 6                                           # 롤링 오리진 개수
origins = [len(LEVEL) - H * k for k in range(n_orig, 0, -1)]     # 각 기점까지를 문맥으로 사용
if min(origins) < max(3 * M if M <= 60 else 60, 100):
    origins = [o for o in origins if o >= 100]

def ses_fc(train, h):
    train = np.asarray(train, float)
    def sse(a):
        l = train[0]; e = 0.0
        for v in train[1:]:
            e += (v - l) ** 2; l = a * v + (1 - a) * l
        return e
    a = optimize.minimize_scalar(sse, bounds=(0.01, 0.99), method="bounded").x
    l = train[0]
    for v in train[1:]:
        l = a * v + (1 - a) * l
    return np.repeat(l, h)

METHODS = {"naive": lambda c, h: naive_fc(c, h), "drift": lambda c, h: drift_fc(c, h), "SES": ses_fc}
if 1 < M <= 60:
    METHODS[f"seasonal naive(m={M})"] = lambda c, h, m=M: snaive_fc(c, h, m)
'''

CHRONOS = r'''
# 사전학습 모델(Amazon Chronos). 설치/다운로드에 실패하면 건너뛴다. 오프라인(TSLAB_OFFLINE=1)에서도 건너뜀.
RUN_FOUNDATION = True          # False로 바꾸면 기준선만 실행
FM_NAME = None
if RUN_FOUNDATION and USE_LIVE_DATA and ensure("torch") and ensure("chronos-forecasting", "chronos"):
    try:
        import torch
        from chronos import ChronosPipeline
        pipe = ChronosPipeline.from_pretrained("amazon/chronos-t5-small", device_map="cpu", torch_dtype=torch.float32)
        def chronos_fc(ctx, h):
            ctx = np.asarray(ctx, float)[-512:]
            out = pipe.predict(torch.tensor(ctx), prediction_length=min(h, 64), num_samples=20)     # [1, 샘플, h]
            return np.quantile(out[0].numpy(), 0.5, axis=0)
        METHODS["Chronos-T5-small (zero-shot)"] = chronos_fc; FM_NAME = "Chronos-T5-small (zero-shot)"
        print("사전학습 모델 로드 성공:", FM_NAME)
    except Exception as e:
        print("사전학습 모델 사용 불가 -> 기준선만 실행:", type(e).__name__, str(e)[:120])
else:
    print("사전학습 모델 미사용(오프라인이거나 패키지 없음) -> 기준선만 실행합니다. 결과표의 'zero-shot' 행은 없습니다.")
'''

EVAL = r'''
rows = []
for o in origins:
    ctx, act = LEVEL.iloc[:o].to_numpy(), LEVEL.iloc[o:o + H].to_numpy()
    if len(act) < H: continue
    for name, fn in METHODS.items():
        try:
            f = fn(ctx, H)
        except Exception as e:
            print(name, "실패:", type(e).__name__, str(e)[:80]); continue
        rows.append({"origin": LEVEL.index[o - 1], "method": name, "MAE": mae(act, f),
                     "MASE": mase(act, f, ctx, m=1)})
R = pd.DataFrame(rows)
summary = R.groupby("method")[["MAE", "MASE"]].agg(["mean", "std"]).round(4)
show(summary)
piv = R.pivot(index="origin", columns="method", values="MASE")
piv.plot(figsize=(11, 3.8), marker="o", title=f"롤링 오리진별 MASE (H={H}) | {DATA_KIND}"); plt.tight_layout(); plt.show()
'''

COMPARE = r'''
best_base = R[~R["method"].str.contains("zero-shot")].groupby("method")["MASE"].mean().idxmin()
print("기준선 중 평균 MASE 최소:", best_base)
if FM_NAME is not None:
    d = piv[FM_NAME] - piv[best_base]
    print(f"{FM_NAME} - {best_base}: 평균 MASE 차이={d.mean():.4f}, 기점 {len(d)}개 중 개선 {int((d<0).sum())}개")
    print("기점 수가 적어 유의성 검정은 하지 않는다. 반복 기점·다른 시리즈가 필요하다.")
else:
    print("zero-shot 모델 결과가 없으므로 비교는 기준선 사이에서만 의미가 있다.")
'''

INTERP = r'''
## 3. 결과 해석 작성
1. zero-shot 모델이 **가장 강한 단순 기준선**(보통 계절 나이브/나이브)을 이겼는가? 개선이 6개 기점 중 몇 개에서 나타났는가?
2. 평가 기간이 사전학습 말뭉치에 포함됐을 가능성(오염)과, 이를 줄이려면 어떤 설계가 필요한지(말뭉치 이후 기간, 비공개 자료) 적는다.
3. 분포 외 구간(구조변화, 이벤트)에서 성능이 어떠한지, 예측구간의 보정(coverage)은 확인했는가?
4. 합성자료로 돌렸다면 결과는 **파이프라인 점검**이다.

**제출:** 롤링 오리진 결과표, 기준선 설명, 오염 논의, 한계.
'''

def build(domain, title, question):
    return [
        md(f"# Chapter 4 · {title}\n\n**연구질문:** {question}\n\n> 사전학습 모델(Chronos)은 선택 기능입니다. 설치·다운로드가 안 되면 기준선만으로 끝까지 실행됩니다."),
        md(THEORY), code(SETUP),
        code(LOADERS[domain].replace("@@WHICH@@", WHICH[domain]).replace("@@FORCE@@", "False")),
        md("## 2. 기준선과 사전학습 모델"), code(BASELINES.replace("@@H@@", str(HORIZON[domain]))), code(CHRONOS),
        md("## 3. 롤링 오리진 평가"), code(EVAL), code(COMPARE), md(INTERP)]

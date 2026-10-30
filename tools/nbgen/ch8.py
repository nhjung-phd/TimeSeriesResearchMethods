from .cells import md, code
from .common import SETUP
from .data_cells import LOADERS

WHICH = {"Finance": "", "RealEstate": "price", "Manufacturing": "demand", "PublicPolicy": "complaints",
         "EnergyEnvironment": "demand", "BusinessMarketing": ""}

META = {
 "Finance": dict(mode="logret", goal="예측(평균·변동성) 또는 이벤트 연구", unit="일별 시장 수준 시계열(단일 자산)",
     threats=["수익률의 낮은 예측가능성: 표본 외 R²가 0 근처일 가능성", "레짐 변화와 단일 표본(2015~)의 대표성", "거래비용·슬리피지 없이는 경제적 유의성 주장 불가",
              "데이터 스누핑(많은 시도 중 최고 모형 보고)", "수정주가·상장폐지 편의(실제 자료 사용 시)"], bench="역사평균, 0 예측, 롤링 변동성"),
 "RealEstate": dict(mode="level", goal="예측 + 지역 간 정책 비교(DID 등)", unit="월별 지역 가격지수 또는 거래량",
     threats=["지수의 평활·개정으로 인한 인위적 자기상관", "품질·구성 변화(거래 단위 자료)", "정책 시점과 동시 충격(금리, 세제) 혼재", "지역 간 파급(spillover)으로 SUTVA 위반",
              "소수 처치 지역의 추론"], bench="나이브, 계절 나이브, 드리프트"),
 "Manufacturing": dict(mode="level", goal="수요 예측 / 공정 개선 효과(ITS) / 이상 탐지", unit="일별 제조 수요(합성)",
     threats=["달력 시간이 있는 무료 실제 자료 부재 -> 합성 의존", "이벤트(고장) 수가 적어 지표 불안정", "라벨 시점 정의와 누수", "공정 개선과 동시 변화(원료·인력)"], bench="계절 나이브, 단순 평활"),
 "PublicPolicy": dict(mode="level", goal="건수 예측 또는 정책 개입 평가(ITS·DID·SCM)", unit="일별 민원 건수",
     threats=["정책 시점과 동시 사건(코로나, 제도 변경)", "건수 자료의 과산포·0 과잉", "처치 단위가 하나일 때의 추론 한계", "행정 데이터의 정의·분류 변경"], bench="계절 나이브, 요일 평균"),
 "EnergyEnvironment": dict(mode="level", goal="수요 예측 / 규제 효과", unit="일별 전력수요(합성, 기온 의존)",
     threats=["재분석·모델 값과 실측의 차이", "기온 예보 오차가 예측 성능에 미치는 영향(미래 기온을 안다고 가정하면 낙관)", "기상 체제변화·기후 추세", "규제와 동시 기상 충격"], bench="계절 나이브, 기온 포함 회귀"),
 "BusinessMarketing": dict(mode="level", goal="매출 예측 / 캠페인 효과(DID)", unit="일별 매출",
     threats=["프로모션 표지의 사전/사후 정의 -> 누수", "취소·반품 처리와 이상치", "캠페인 대상 선정의 내생성", "가격·재고·경쟁사 동시 변화"], bench="계절 나이브, 요일 평균"),
}

THEORY = r'''
## 1. 핵심 개념

**연구설계는 질문 → 데이터 → 방법 → 검증의 일관성 문제다.** 아래 표의 네 열이 한 줄로 이어지지 않으면 설계에 결함이 있다.

| 질문 유형 | 대표 방법 | 식별/타당성의 핵심 | 흔한 반려 사유 |
|---|---|---|---|
| 예측 | ARIMA/SARIMA, ML, 사전학습 모델 | 시간순 외표본, 기준선, 누수 차단 | 약한 기준선, 누수, 단일 구간 |
| 인과(개입) | ITS, DID, SCM | 평행추세·동시사건 부재·간섭 없음 | 위약·사전추세 점검 부재 |
| 구조(패널) | FE, RE, TWFE | 시간불변 교란 통제, 군집 추론 | 내생성, 소수 군집 |
| 불확실성/위험 | GARCH 등 | 분포·레짐, 외표본 위험지표 | 단일 표본, 경제적 유의성 부재 |

이 노트북의 **방법 추천 함수는 교육용 규칙(휴리스틱)** 이며 검증된 의사결정 절차가 아니다. 설계자의 판단을 대체하지 않는다.
'''

AUDIT = r'''
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.seasonal import seasonal_decompose

MODE = "@@MODE@@"
series = (np.log(y).diff().dropna() * 100) if MODE == "logret" else y.astype(float)
series = series.rename("target")
print("분석 대상 계열:", "일별 로그수익률(%)" if MODE == "logret" else D["label"], "| 관측 수:", len(series))

profile = {"n": len(series), "freq": FREQ, "m": M}
profile["missing_share"] = float(series.isna().mean())
z = (series - series.median()) / (1.4826 * np.median(np.abs(series - series.median())) + 1e-12)
profile["outlier_share(|robust z|>4)"] = float((np.abs(z) > 4).mean())
x = series.dropna().to_numpy(float)
profile["adf_p"] = float(adfuller(x, autolag="AIC")[1]); profile["kpss_p"] = float(kpss(x, regression="c", nlags="auto")[1])
if M > 1 and 2 * M <= len(series) and M <= 400:
    dec = seasonal_decompose(series.astype(float), model="additive", period=M)
    r_ = dec.resid.dropna(); sr_ = (dec.seasonal + dec.resid).dropna()
    profile["seasonal_strength"] = max(0.0, 1 - float(r_.var()) / float(sr_.var()))
else:
    profile["seasonal_strength"] = float("nan")
h_ = len(x) // 2; profile["levene_p(전후반 분산)"] = float(stats.levene(x[:h_], x[h_:]).pvalue)
def sup_f_mean(v, trim=0.15, step=None):
    v = np.asarray(v, float); n = len(v); step = step or max(1, n // 100); best = (0.0, None)
    for k in range(int(trim * n), int((1 - trim) * n), step):
        a, b = v[:k], v[k:]; rss1 = np.sum((a - a.mean()) ** 2) + np.sum((b - b.mean()) ** 2); rss0 = np.sum((v - v.mean()) ** 2)
        F = (rss0 - rss1) / (rss1 / (n - 2)); best = max(best, (F, k), key=lambda t: t[0])
    return best
F_, k_ = sup_f_mean(x); profile["sup_F_mean_shift"] = float(F_)
print("\n데이터 프로파일:"); show(pd.Series(profile).to_frame("값"), 4)
'''

RECOMMEND = r'''
def recommend_methods(p, goal):
    # 교육용 규칙. 임계값은 관행적 값이며 연구마다 정당화가 필요하다.
    out, warn = [], []
    stationary = (p["adf_p"] < 0.05) and (p["kpss_p"] >= 0.05)
    seasonal = (not np.isnan(p["seasonal_strength"])) and p["seasonal_strength"] > 0.3
    if "예측" in goal or "수요" in goal or "건수" in goal or "매출" in goal:
        out.append("기준선: 나이브" + (" + 계절 나이브" if seasonal else ""))
        out.append("통계모형: " + ("SARIMA" if seasonal else "ARIMA") + (" (차분 필요)" if not stationary else ""))
        out.append("ML: 시차·달력 특성 + Ridge/부스팅 (시간순 CV)")
        if p["levene_p(전후반 분산)"] < 0.05: out.append("분산 불안정 -> 로그변환 또는 GARCH류 고려")
    if "정책" in goal or "효과" in goal or "DID" in goal or "ITS" in goal:
        out.append("개입 평가: ITS(단일 시계열) / DID(비교집단 있음) / SCM(처치 단위 1개, 도너 풀)")
        warn.append("인과 주장에는 평행추세·동시사건 부재·간섭 없음 점검과 위약검정이 필수")
    if p["n"] < 100: warn.append("관측 수가 적어 복잡한 모형은 과적합 위험")
    if p["sup_F_mean_shift"] > 50: warn.append("평균 이동(구조변화) 징후: 구간별 성능과 변화점 처리 필요")
    if p["outlier_share(|robust z|>4)"] > 0.01: warn.append("이상치 비율이 1% 초과: 처리 규칙을 사전에 정의")
    if not stationary: warn.append("정상성 검정이 정상과 부합하지 않음: 차분·추세 모형 비교")
    return out, warn
meta_goal = "@@GOAL@@"
rec, warn = recommend_methods(profile, meta_goal)
print("연구 목적:", meta_goal); print("\n추천(교육용 규칙):"); [print(" -", r) for r in rec]
print("\n경고:"); [print(" -", w) for w in warn]
'''

PIPE = r'''
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def dm_p(d):
    d = np.asarray(d, float); n = len(d)
    if n < 3 or np.std(d) == 0: return np.nan
    st = d.mean() / np.sqrt(np.var(d, ddof=1) / n); return float(2 * (1 - stats.t.cdf(abs(st), n - 1)))

lags = [1, 2, 3] + ([M] if 1 < M <= 60 else [])
X = pd.DataFrame({f"lag_{k}": series.shift(k) for k in lags})
for w in (5, 20): X[f"rm_{w}"] = series.shift(1).rolling(w).mean()
if FREQ in ("D", "B"): X["dow"] = series.index.dayofweek
data = pd.concat([X, series], axis=1).dropna(); XX, yy = data.drop(columns="target"), data["target"]
n = len(data); n_folds = 6; fold = int(max(10, min(90, n // 15))); start = n - n_folds * fold
rows = []
for k in range(n_folds):
    a, b = start + k * fold, start + (k + 1) * fold
    yte = yy.iloc[a:b].to_numpy(); r_ = {"fold": k + 1}
    r_["naive"] = rmse(yte, XX["lag_1"].iloc[a:b])
    if 1 < M <= 60: r_["seasonal naive"] = rmse(yte, XX[f"lag_{M}"].iloc[a:b])
    r_["mean(train)"] = rmse(yte, np.full(len(yte), yy.iloc[:a].mean()))
    for name, mdl in {"Ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
                      "HistGB": HistGradientBoostingRegressor(max_iter=150, learning_rate=0.06, random_state=SEED)}.items():
        mdl.fit(XX.iloc[:a], yy.iloc[:a]); r_[name] = rmse(yte, mdl.predict(XX.iloc[a:b]))
    rows.append(r_)
RES = pd.DataFrame(rows).set_index("fold")
print(f"롤링 오리진 {n_folds}폴드 × {fold}관측 (1단계 예측, 시차는 실제값)"); show(RES)
summary = RES.agg(["mean", "std", "max"]).T; show(summary)
bench = [c for c in ("naive", "seasonal naive", "mean(train)") if c in RES.columns]
best_bench = RES[bench].mean().idxmin(); best_model = RES[["Ridge", "HistGB"]].mean().idxmin()
dd = RES[best_bench] - RES[best_model]
print(f"\n최고 기준선={best_bench} | 최고 모형={best_model} | 평균 개선={dd.mean():.4f} | 개선 폴드 {int((dd>0).sum())}/{len(dd)} | 폴드 t검정 p≈{dm_p(dd):.3f} (폴드 수가 적어 근사)")
'''

DRAFT = r'''
threats = @@THREATS@@
bench_txt = "@@BENCH@@"
imp = (RES[best_bench].mean() - RES[best_model].mean()) / RES[best_bench].mean() * 100
if abs(imp) < 2:
    claim = "기준선과 평균 RMSE 차이가 %.1f%%로 미미해 개선을 주장하기 어렵다." % imp
elif imp > 0:
    claim = "기준선 대비 평균 RMSE가 %.1f%% 낮았으나 폴드 수가 적어 우열은 잠정적이다." % imp
else:
    claim = "모형이 기준선을 이기지 못했다(평균 RMSE 변화 %.1f%%). 이 결과를 정직하게 보고하는 설계가 필요하다." % imp
draft = f"""
# 연구설계서 초안 (자동 생성 · 검토 후 직접 수정)

## Research Question
{question_text}

## Data
- 자료: {D['label']} | DATA_KIND: {DATA_KIND}
- 단위/주기: @@UNIT@@ / {FREQ} (계절 주기 M={M}) | 관측 {profile['n']}개
- 데이터 품질: 결측 {profile['missing_share']:.1%}, 이상치 {profile['outlier_share(|robust z|>4)']:.2%}

## Empirical Strategy
- 목적: {meta_goal}
- 모형 후보: {', '.join(rec[:3])}
- 벤치마크: {bench_txt}
- 검증: 롤링 오리진 {n_folds}폴드, 폴드 크기 {fold}, 누수 차단(시차·롤링은 shift, 학습구간 통계로만 스케일)

## Preliminary Result (이 노트북 실행값)
- 최고 기준선 {best_bench}, 최고 모형 {best_model}. {claim}

## Robustness (예정)
- 학습 창·시차 집합 변경, 하위기간/하위집단, 대체 지표(MAE·MASE), 사전 지정 위약검정(해당 시)

## Main Risks (리뷰어가 공격할 지점)
""" + "\n".join(f"- {t}" for t in threats) + """

## Expected Contribution (보수적 서술)
- 위 결과가 기준선 대비 일관되게 개선될 때에 한해, 특정 자료·기간에서의 예측 개선을 보고한다. 일반화 주장은 하지 않는다.
"""
print(draft)
'''

CHECK = r'''
## 3. 제출 전 점검표
- [ ] 연구질문이 한 문장이며 방법·종속변수·해석 척도가 한 줄로 이어지는가
- [ ] 데이터 출처·라이선스·`DATA_KIND`(실제/합성)를 명시했는가
- [ ] 가장 강한 단순 기준선과 비교했는가 (약한 기준선 금지)
- [ ] 누수 경로(전처리, 미래 특성, 분할)를 하나씩 점검했는가
- [ ] 폴드/구간별 분포를 보고했는가 (평균만 보고하지 않음)
- [ ] 인과 주장 시 식별 가정과 위약검정이 있는가
- [ ] 위 "Main Risks"에 대한 대응이 설계서에 있는가

**제출:** 자동 생성 초안을 본인 연구에 맞게 고친 연구설계서(2쪽 이내), 프로파일 표, 롤링 오리진 결과표, 한계 단락.
'''

def build(domain, title, question):
    m = META[domain]
    q = question.replace('"', "'")
    return [
        md(f"# Chapter 8 · {title}\n\n**연구질문(과제):** {question}\n\n> 위에서 아래로 실행하면 끝까지 동작합니다. 마지막 셀은 실행 결과 숫자로 연구설계서 초안을 자동 작성합니다."),
        md(THEORY), code(SETUP),
        code(LOADERS[domain].replace("@@WHICH@@", WHICH[domain]).replace("@@FORCE@@", "False")),
        md("## 2. 데이터 감사 → 방법 선택 → 파이프라인 → 설계서"),
        code(AUDIT.replace("@@MODE@@", m["mode"])),
        code(RECOMMEND.replace("@@GOAL@@", m["goal"])),
        code(PIPE),
        code(f'question_text = "{q}"\n' + DRAFT.replace("@@THREATS@@", repr(m["threats"])).replace("@@BENCH@@", m["bench"]).replace("@@UNIT@@", m["unit"])),
        md(CHECK)]

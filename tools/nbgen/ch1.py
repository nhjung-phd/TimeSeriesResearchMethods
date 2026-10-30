from .cells import md, code
from .common import SETUP
from .data_cells import LOADERS

WHICH = {"Finance": "", "RealEstate": "price", "Manufacturing": "sensor", "PublicPolicy": "complaints",
         "EnergyEnvironment": "temp", "BusinessMarketing": ""}

THEORY = r'''
## 1. 핵심 개념·수식

**약정상성(weak stationarity):** $E(y_t)=\mu$, $\mathrm{Var}(y_t)=\sigma^2$, $\mathrm{Cov}(y_t,y_{t-k})=\gamma(k)$는 $t$에 의존하지 않는다.

**고전적 분해(가법):** $y_t = T_t + S_t + R_t$. 계절성의 세기는 $F_S=\max\!\left(0,\,1-\dfrac{\mathrm{Var}(R_t)}{\mathrm{Var}(S_t+R_t)}\right)$로 요약한다(0에 가까우면 약함).

**단위근 검정:** ADF의 귀무가설은 *단위근 존재*, KPSS의 귀무가설은 *정상성*이다. 두 검정을 함께 읽는다.

| ADF (H0: 단위근) | KPSS (H0: 정상) | 읽는 법 |
|---|---|---|
| 기각 | 기각 못함 | 정상성과 부합 |
| 기각 못함 | 기각 | 단위근/비정상과 부합 → 차분 고려 |
| 둘 다 기각 | | 추세정상·구조변화·분산 불안정 가능 |
| 둘 다 기각 못함 | | 검정력 부족, 판단 보류 |

**자기상관:** $\rho(k)=\gamma(k)/\gamma(0)$. Ljung–Box $Q=n(n+2)\sum_{k=1}^{h}\dfrac{\hat\rho(k)^2}{n-k}$. 변동성 군집은 $r_t^2$의 자기상관(ARCH-LM)으로 점검한다.
'''

DIAG = r'''
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.seasonal import seasonal_decompose

def stationarity_row(s, label):
    x = pd.Series(s).dropna().to_numpy(dtype=float)
    adf_p = adfuller(x, autolag="AIC")[1]
    kpss_p = kpss(x, regression="c", nlags="auto")[1]
    verdict = ("정상성과 부합" if (adf_p < 0.05 and kpss_p >= 0.05) else
               "비정상 의심(차분 고려)" if (adf_p >= 0.05 and kpss_p < 0.05) else
               "두 검정 불일치/검정력 한계: 판단 보류")
    return {"series": label, "ADF_p": adf_p, "KPSS_p": kpss_p, "읽기": verdict}
'''

PLOT_LEVEL = r'''
fig, ax = plt.subplots(figsize=(11, 4))
y.plot(ax=ax, title=f"{D['label']} | {DATA_KIND}")
ax.set_ylabel(D["unit"]); plt.tight_layout(); plt.show()
print(y.describe().round(3).to_string())
n_missing = int(y.isna().sum()); print("결측:", n_missing, "| 추정 주기:", pd.infer_freq(y.index))
'''

PLOT_FIN = r'''
fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
y.plot(ax=axes[0], title=f"Price | {DATA_KIND}")
ret.plot(ax=axes[1], title="일별 로그수익률(%)")
plt.tight_layout(); plt.show()
print(ret.describe().round(4).to_string())
print("왜도:", round(float(stats.skew(ret)), 3), "| 초과첨도:", round(float(stats.kurtosis(ret)), 3),
      "(정규분포면 둘 다 0)")
'''

DECOMP = r'''
# 계절성 분해 (주기 M=@@M@@). 표본이 주기의 2배 미만이면 건너뛴다.
if 2 * M <= len(y) and M > 1:
    dec = seasonal_decompose(y.astype(float), model="additive", period=M)
    parts = pd.concat([dec.observed, dec.trend, dec.seasonal, dec.resid], axis=1,
                      keys=["observed", "trend", "seasonal", "resid"])
    parts.iloc[-min(len(parts), 6 * M):].plot(subplots=True, figsize=(11, 7), title="분해 결과(최근 구간)")
    plt.tight_layout(); plt.show()
    r = dec.resid.dropna(); sr = (dec.seasonal + dec.resid).dropna()
    Fs = max(0.0, 1 - float(r.var()) / float(sr.var()))
    print(f"계절성 세기 F_S = {Fs:.3f}  (0=없음, 1=매우 강함; 휴리스틱 지표)")
else:
    Fs = np.nan; print("표본이 짧아 분해를 건너뜀")
'''

STAT_OTHER = r'''
rows = [stationarity_row(y, "level")]
yd = y.diff().dropna(); rows.append(stationarity_row(yd, "1차 차분"))
if 3 * M < len(y) and M > 1 and M <= 60:
    rows.append(stationarity_row(y.diff(M).dropna(), f"계절차분(M={M})"))
res = pd.DataFrame(rows); show(res)
work = yd if rows[0]["읽기"] != "정상성과 부합" else y      # 이후 ACF 분석 대상
print("ACF 분석 대상:", "1차 차분" if work is yd else "level")
'''

STAT_FIN = r'''
res = pd.DataFrame([stationarity_row(y, "Price"), stationarity_row(ret, "Log return(%)")]); show(res)
work = ret; Fs = np.nan
'''

ACF = r'''
fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
nl = int(min(40, len(work) // 4))
plot_acf(work, lags=nl, ax=ax[0], title="ACF"); plot_pacf(work, lags=nl, ax=ax[1], title="PACF", method="ywm")
plt.tight_layout(); plt.show()
lb = acorr_ljungbox(work, lags=[10], return_df=True)
print("Ljung-Box(10) p =", round(float(lb["lb_pvalue"].iloc[0]), 4), "-> 작으면 자기상관 존재")
'''

ARCH_FIN = r'''
fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
plot_acf(ret ** 2, lags=40, ax=ax[0], title="제곱수익률 ACF")
ret.abs().rolling(21).mean().plot(ax=ax[1], title="21일 평균 |수익률| (변동성 군집)")
plt.tight_layout(); plt.show()
arch_p = het_arch(ret, nlags=10)[1]
print("ARCH-LM(10) p =", round(float(arch_p), 4), "-> 작으면 조건부 이분산(변동성 군집)과 부합")
'''

VAR_OTHER = r'''
# 분산 안정성: 앞·뒤 절반의 분산 비교(Levene)와 이동 표준편차
h = len(work) // 2
lev = stats.levene(work.iloc[:h], work.iloc[h:])
print(f"Levene p = {lev.pvalue:.4f} (작으면 전·후반 분산이 다름)")
work.rolling(max(7, M if M < 60 else 30)).std().plot(title="이동 표준편차", figsize=(11, 3.5)); plt.show()
'''

PM_EXTRA = r'''
# (선택) 대기질: PM2.5 월별 기후값
pm = D.get("pm")
if pm is not None and len(pm.dropna()) > 200:
    pm.dropna().groupby(pm.dropna().index.month).mean().plot(kind="bar", title="PM2.5 월별 평균(Open-Meteo 대기질 모델값, 실측 아님)")
    plt.show()
else:
    print("PM2.5 자료가 없어 기온만 분석합니다(오프라인이거나 수집 실패).")
'''

SUMMARY = r'''
print("=== 자동 요약(숫자 확인용, 해석은 직접 작성) ===")
print("데이터 종류:", DATA_KIND)
for r_ in res.to_dict("records"):
    print(f"- {r_['series']}: ADF p={r_['ADF_p']:.3f}, KPSS p={r_['KPSS_p']:.3f} -> {r_['읽기']}")
if not np.isnan(Fs): print(f"- 계절성 세기 F_S={Fs:.2f}")
'''

INTERP = r'''
## 3. 결과 해석 작성

1. `DATA_KIND`가 **REAL**인지 **SYNTHETIC**인지 먼저 적는다. 합성자료의 결과는 방법 시연이며 현상에 대한 증거가 아니다.
2. 수준과 차분(또는 수익률)에서 ADF·KPSS가 어떻게 다른지 설명한다. 두 검정이 어긋나면 구조변화·추세·표본기간을 논의한다.
3. 계절성 세기와 ACF/PACF가 이후 모형(Ch.2)의 후보 차수에 주는 시사점을 적는다.
4. 한계: 단일 표본, 검정력, 데이터 정의(재분석·집계·취소 제외 등).

## 4. 심화 과제
- 표본기간을 절반으로 나누어 결론이 유지되는지 확인한다.
- 차분 대신 로그변환 후 차분으로 바꿔 결과를 비교한다.
- **제출:** 그래프 3개 이상, 검정표, 해석 단락, 데이터 출처·한계.
'''

def build(domain, title, question):
    fin = domain == "Finance"
    cells = [
        md(f"# Chapter 1 · {title}\n\n**연구질문:** {question}\n\n**학습 흐름:** 개념 → 자료 → 시각화 → 분해 → 정상성 검정 → 자기상관 → 해석.\n\n"
           "> 이 노트북은 위에서 아래로 실행하면 끝까지 동작하도록 만들었습니다. 온라인 자료를 먼저 시도하고, 실패하면 **합성자료로 자동 대체**하며 `DATA_KIND`에 표시합니다."),
        md(THEORY),
        code(SETUP),
        code(LOADERS[domain].replace("@@WHICH@@", WHICH[domain]).replace("@@FORCE@@", "False")),
        md("## 2. 시각화와 진단"),
        code(PLOT_FIN if fin else PLOT_LEVEL),
    ]
    cells.append(code(DIAG))
    if not fin:
        cells.append(code(DECOMP.replace("@@M@@", "M")))
    cells += [code(STAT_FIN if fin else STAT_OTHER), code(ACF)]
    cells.append(code(ARCH_FIN if fin else VAR_OTHER))
    if domain == "EnergyEnvironment":
        cells.append(code(PM_EXTRA))
    cells += [code(SUMMARY), md(INTERP)]
    return cells

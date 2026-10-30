from .cells import md, code
from .common import SETUP
from .data_cells import LOADERS

WHICH = {"Finance": "", "RealEstate": "volume", "Manufacturing": "demand", "PublicPolicy": "complaints",
         "EnergyEnvironment": "demand", "BusinessMarketing": ""}
HORIZON = {"Finance": 20, "RealEstate": 24, "Manufacturing": 28, "PublicPolicy": 28, "EnergyEnvironment": 28, "BusinessMarketing": 28}
LOGT = {"PublicPolicy": True, "BusinessMarketing": False}

THEORY = r'''
## 1. 핵심 개념·수식

**ARIMA$(p,d,q)$:** $\phi(L)(1-L)^d y_t = c + \theta(L)\varepsilon_t$, $\ \varepsilon_t \sim WN(0,\sigma^2)$.

**SARIMA$(p,d,q)(P,D,Q)_m$:** 계절 차분 $(1-L^m)^D$와 계절 AR/MA 다항식 $\Phi(L^m),\Theta(L^m)$을 추가한다.

**차수 선택:** $\mathrm{AIC}=2k-2\ln\hat{L}$. AIC는 **적합 내 기준**이며 외표본 성능을 보장하지 않는다. 항상 시간순 홀드아웃에서 기준선과 비교한다.

**예측 오차 지표:** $\mathrm{MAE}$, $\mathrm{RMSE}$, $\mathrm{MASE}=\dfrac{\mathrm{MAE}}{\frac{1}{T-1}\sum_{t=2}^{T}|y_t-y_{t-1}|}$ (분모는 학습구간 1단계 나이브의 평균절대오차; 1보다 작으면 학습구간 나이브보다 낫다).

**잔차 진단:** 잔차가 백색잡음이면 Ljung–Box $Q$ 검정에서 기각되지 않아야 한다.
'''

THEORY_GARCH = r'''
**GARCH(1,1):** $r_t=\mu+\varepsilon_t,\ \varepsilon_t=\sigma_t z_t,\ \sigma_t^2=\omega+\alpha\varepsilon_{t-1}^2+\beta\sigma_{t-1}^2$, 정상성 조건 $\alpha+\beta<1$. 외부 패키지 없이 최대우도로 직접 추정한다.
'''

SPLIT = r'''
H = @@H@@                                  # 예측 구간 길이(관측 단위)
LOG = @@LOG@@                              # 건수·양수 자료의 분산 안정화를 위한 log1p 사용 여부
s_all = y.astype(float)
z_all = np.log1p(s_all) if LOG else s_all   # 모형이 보는 척도
train_z, test_z = z_all.iloc[:-H].to_numpy(), z_all.iloc[-H:].to_numpy()
train, test = s_all.iloc[:-H].to_numpy(), s_all.iloc[-H:].to_numpy()
back = (lambda v: np.expm1(v)) if LOG else (lambda v: v)    # 모형 척도 -> 원척도
print(f"학습 {len(train)} | 검증 {len(test)} | log1p 사용: {LOG}")
'''

BASE = r'''
results = {}
def record(name, fc):
    fc = np.asarray(fc, float)
    results[name] = {"MAE": mae(test, fc), "RMSE": rmse(test, fc), "MASE": mase(test, fc, train, m=1)}
record("naive", naive_fc(train, H))
record("drift", drift_fc(train, H))
if M > 1 and M <= len(train) // 3:
    record(f"seasonal naive(m={M})", snaive_fc(train, H, M))
show(pd.DataFrame(results).T)
'''

ARIMA = r'''
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller

d = 0 if adfuller(train_z, autolag="AIC")[1] < 0.05 else 1       # 단순 규칙(검정은 보조 수단)
cands = []
for p in range(3):
    for q in range(3):
        try:
            fit = ARIMA(train_z, order=(p, d, q)).fit()
            cands.append((fit.aic, p, q, fit))
        except Exception:
            continue
cands.sort(key=lambda t: t[0])
aic, p_, q_, best = cands[0]
print(f"선택 ARIMA({p_},{d},{q_})  AIC={aic:.1f}  (후보 {len(cands)}개 중 AIC 최소)")
fc = best.get_forecast(H)
mean_z, ci_z = np.asarray(fc.predicted_mean), np.asarray(fc.conf_int(alpha=0.05))
record(f"ARIMA({p_},{d},{q_})", back(mean_z))
lb = acorr_ljungbox(best.resid, lags=[10], return_df=True)["lb_pvalue"].iloc[0]
print("잔차 Ljung-Box(10) p =", round(float(lb), 4), "-> 작으면 잔차에 자기상관이 남음")
'''

SARIMA = r'''
from statsmodels.tsa.statespace.sarimax import SARIMAX
USE_SARIMA = M in (7, 12) and len(train_z) > 4 * M
if USE_SARIMA:
    try:
        sfit = SARIMAX(train_z, order=(1, d, 1), seasonal_order=(1, 1, 1, M),
                       enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
        sfc = sfit.get_forecast(H)
        record(f"SARIMA(1,{d},1)(1,1,1)_{M}", back(np.asarray(sfc.predicted_mean)))
        s_mean_z, s_ci_z = np.asarray(sfc.predicted_mean), np.asarray(sfc.conf_int(alpha=0.05))
        print("SARIMA 잔차 Ljung-Box p =", round(float(acorr_ljungbox(sfit.resid, lags=[10], return_df=True)["lb_pvalue"].iloc[0]), 4))
    except Exception as e:
        USE_SARIMA = False; print("SARIMA 적합 실패:", type(e).__name__, str(e)[:100])
else:
    print(f"M={M}: 이 노트북에서는 SARIMA를 건너뜁니다(주기가 7·12가 아니거나 표본이 짧음).")
'''

EXOG = r'''
# 외생변수(기온) 포함 SARIMAX. 검증구간의 기온을 미래 시나리오 입력으로 쓴다(= 미래 기온을 안다고 가정, 결과 해석 시 명시).
X_all = D["X"]["temp"].to_numpy(float).reshape(-1, 1)
X_tr, X_te = X_all[:-H], X_all[-H:]
try:
    xfit = SARIMAX(train_z, exog=X_tr, order=(1, 0, 1), seasonal_order=(1, 0, 1, 7),
                   enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    xfc = np.asarray(xfit.get_forecast(H, exog=X_te).predicted_mean)
    record("SARIMAX + 기온(기온을 안다고 가정)", back(xfc))
except Exception as e:
    print("SARIMAX 외생변수 적합 실패:", type(e).__name__, str(e)[:100])
'''

COMPARE = r'''
tab = pd.DataFrame(results).T.sort_values("MASE")
show(tab)
best_name = tab.index[0]
print("검증구간 MASE 최소:", best_name, "| 주의: 단일 검증구간이므로 우열은 불확실(→ Ch.7 walk-forward)")
fig, ax = plt.subplots(figsize=(11, 4))
idx_te = s_all.index[-H:]
ax.plot(s_all.index[-4 * H:], s_all.iloc[-4 * H:], label="actual")
ax.plot(idx_te, back(mean_z), label=f"ARIMA({p_},{d},{q_})")
ax.fill_between(idx_te, back(ci_z[:, 0]), back(ci_z[:, 1]), alpha=0.15)
if "USE_SARIMA" in globals() and USE_SARIMA:
    ax.plot(idx_te, back(s_mean_z), label="SARIMA")
ax.plot(idx_te, snaive_fc(train, H, M) if (M > 1 and M <= len(train) // 3) else naive_fc(train, H), "--", label="baseline")
ax.legend(); ax.set_title(f"{D['label']} 예측 | {DATA_KIND}"); plt.tight_layout(); plt.show()
'''

INTERP = r'''
## 3. 결과 해석 작성
1. 어떤 기준선이 가장 강했는지, 복잡한 모형이 그 기준선을 외표본에서 이겼는지(MASE<기준선) 적는다.
2. 잔차 Ljung–Box 결과가 모형 충분성에 대해 말하는 바를 적는다.
3. AIC 최소 모형과 외표본 최소 오차 모형이 다르면 그 이유(과적합, 구조변화)를 논의한다.
4. 한계: 단일 검증구간, 로그변환 역변환 편의, 구조변화. 합성자료 결과는 방법 시연이다.

**제출:** 기준선 포함 지표표, 예측 그래프, 잔차 진단, 해석 단락, 데이터 출처·한계.
'''

# ---- 금융: 수익률 ARIMA + GARCH ----
FIN_SPLIT = r'''
H = 250                                    # 마지막 약 1년을 검증으로 사용
r_all = ret.astype(float)
r_tr, r_te = r_all.iloc[:-H].to_numpy(), r_all.iloc[-H:].to_numpy()
print(f"학습 {len(r_tr)} | 검증 {len(r_te)} (로그수익률 %)")
'''
FIN_ARIMA = r'''
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox
fit = ARIMA(r_tr, order=(1, 0, 1)).fit()
print("ARIMA(1,0,1) 추정 완료 | 잔차 Ljung-Box(10) p =",
      round(float(acorr_ljungbox(fit.resid, lags=[10], return_df=True)["lb_pvalue"].iloc[0]), 4))
# 검증구간 다기간 예측은 평균으로 수렴하므로, 일일 1단계 예측을 갱신 없이 비교하기보다 기준선(역사적 평균)과 비교한다.
arima_fc = np.asarray(fit.get_forecast(H).predicted_mean)
hist_mean = np.full(H, r_tr.mean()); zero = np.zeros(H)
def dm_test(e1, e2, h=1):
    # Diebold-Mariano (제곱오차 손실, Newey-West 분산, 단순 버전)
    d = np.asarray(e1) ** 2 - np.asarray(e2) ** 2; n = len(d); dbar = d.mean()
    L = max(h - 1, 0); g0 = np.var(d, ddof=0); var = g0
    for l in range(1, L + 1):
        var += 2 * (1 - l / (L + 1)) * np.mean((d[l:] - dbar) * (d[:-l] - dbar))
    stat = dbar / np.sqrt(var / n); return stat, 2 * (1 - stats.norm.cdf(abs(stat)))
sse = lambda f: float(np.sum((r_te - f) ** 2))
r2_oos = 1 - sse(arima_fc) / sse(hist_mean)             # 역사적 평균 대비 표본 외 R²
print(f"RMSE: ARIMA={rmse(r_te, arima_fc):.4f}  역사평균={rmse(r_te, hist_mean):.4f}  0예측={rmse(r_te, zero):.4f}")
print(f"표본 외 R²(역사평균 대비) = {r2_oos:.4f}  (0 이하이면 평균보다 낫지 않음)")
st, pv = dm_test(r_te - arima_fc, r_te - hist_mean)
print(f"Diebold-Mariano(ARIMA vs 역사평균): stat={st:.3f}, p={pv:.3f}")
'''
FIN_GARCH = r'''
# GARCH(1,1) 최대우도 추정 (%, 단위 변환으로 수치 안정성 확보)
def garch11_nll(theta, r):
    mu, omega, alpha, beta = theta
    e = r - mu; n = len(r); s2 = np.empty(n); s2[0] = np.var(r)
    for t in range(1, n):
        s2[t] = omega + alpha * e[t - 1] ** 2 + beta * s2[t - 1]
    return 0.5 * np.sum(np.log(2 * np.pi * s2) + e ** 2 / s2)

def fit_garch11(r):
    x0 = [r.mean(), 0.05 * np.var(r), 0.08, 0.88]
    cons = [{"type": "ineq", "fun": lambda th: 0.999 - th[2] - th[3]}]
    bnds = [(-1, 1), (1e-8, None), (1e-6, 0.5), (1e-6, 0.999)]
    res = optimize.minimize(garch11_nll, x0, args=(r,), method="SLSQP", bounds=bnds, constraints=cons,
                            options={"maxiter": 200, "ftol": 1e-9})
    return res

def garch_filter(theta, r):
    mu, omega, alpha, beta = theta; e = r - mu; s2 = np.empty(len(r)); s2[0] = np.var(r)
    for t in range(1, len(r)):
        s2[t] = omega + alpha * e[t - 1] ** 2 + beta * s2[t - 1]
    return s2, e

g = fit_garch11(r_tr)
mu_, om_, al_, be_ = g.x
print(f"GARCH(1,1): mu={mu_:.4f} omega={om_:.5f} alpha={al_:.3f} beta={be_:.3f} | alpha+beta={al_+be_:.3f} | 수렴={g.success}")
# 검증구간 1단계 조건부 분산 예측(매일 갱신)과 기준선(최근 21일 표본분산) 비교, 실현변동성 대용치로 e_t^2 사용
r_full = r_all.to_numpy(); s2_full, e_full = garch_filter(g.x, r_full)
n_tr = len(r_tr)
garch_var = om_ + al_ * e_full[n_tr - 1:-1] ** 2 + be_ * s2_full[n_tr - 1:-1]       # t의 분산을 t-1 정보로 예측
roll_var = np.array([np.var(r_full[t - 21:t]) for t in range(n_tr, len(r_full))])
proxy = (r_te - mu_) ** 2
def qlike(proxy, f): return float(np.mean(np.log(f) + proxy / f))
print(f"QLIKE(작을수록 좋음): GARCH={qlike(proxy, garch_var):.4f}  21일 롤링분산={qlike(proxy, roll_var):.4f}")
print(f"MSE(분산 대용치): GARCH={np.mean((proxy-garch_var)**2):.4f}  롤링={np.mean((proxy-roll_var)**2):.4f}")
fig, ax = plt.subplots(figsize=(11, 3.8))
ax.plot(r_all.index[-H:], np.sqrt(proxy), alpha=0.3, label="|e_t| (실현 대용치)")
ax.plot(r_all.index[-H:], np.sqrt(garch_var), label="GARCH sigma")
ax.plot(r_all.index[-H:], np.sqrt(roll_var), label="21일 롤링 sigma"); ax.legend(); plt.tight_layout(); plt.show()
'''
FIN_INTERP = r'''
## 3. 결과 해석 작성
1. 수익률 평균 예측: 표본 외 R²가 0 이하이고 DM 검정이 기각되지 않으면 "평균 예측은 어렵다"가 합리적 결론이다. 효율적 시장 가설과 연결하되, 단일 구간 결과임을 명시한다.
2. 변동성 예측: QLIKE와 MSE 모두에서 GARCH가 롤링분산보다 낮은지 확인하고, 실현변동성 대용치($e_t^2$)의 잡음을 한계로 적는다.
3. `DATA_KIND`가 합성이면 GARCH 모수는 생성 모수(약 α=0.08, β=0.90)와 비교하는 **추정기 검증**이다. 실제 시장에 대한 증거가 아니다.
4. 거래비용·위험조정 성과 없이 경제적 유의성을 주장하지 않는다.
'''

def build(domain, title, question):
    if domain == "Finance":
        return [
            md(f"# Chapter 2 · {title}\n\n**연구질문:** {question}\n\n> 위에서 아래로 실행하면 끝까지 동작합니다. 온라인 실패 시 합성 대체(`DATA_KIND` 표시)."),
            md(THEORY + THEORY_GARCH), code(SETUP), code(LOADERS[domain]),
            md("## 2. 분할과 수익률 평균 예측 (ARIMA)"), code(FIN_SPLIT), code(FIN_ARIMA),
            md("## 3. 변동성 예측 (GARCH)"), code(FIN_GARCH), md(FIN_INTERP)]
    cells = [md(f"# Chapter 2 · {title}\n\n**연구질문:** {question}\n\n> 위에서 아래로 실행하면 끝까지 동작합니다. 온라인 실패 시 합성 대체(`DATA_KIND` 표시)."),
             md(THEORY), code(SETUP),
             code(LOADERS[domain].replace("@@WHICH@@", WHICH[domain]).replace("@@FORCE@@", "False")),
             md("## 2. 분할과 기준선"),
             code(SPLIT.replace("@@H@@", str(HORIZON[domain])).replace("@@LOG@@", str(LOGT.get(domain, False)))),
             code(BASE), md("## 3. ARIMA / SARIMA"), code(ARIMA), code(SARIMA)]
    if domain == "EnergyEnvironment":
        cells.append(code(EXOG))
    cells += [md("## 4. 비교와 진단"), code(COMPARE), md(INTERP)]
    return cells

from .cells import md, code
from .common import SETUP, PANEL_TOOLS

THEORY = r'''
## 1. 핵심 개념·수식

**패널 모형:** $y_{it}=x_{it}'\beta+\alpha_i+\lambda_t+\varepsilon_{it}$. $\alpha_i$는 개체 고유 효과, $\lambda_t$는 시간 효과.

**Pooled OLS:** $\alpha_i$를 오차에 넣는다. $\mathrm{Cov}(x_{it},\alpha_i)\neq0$이면 $\hat\beta$는 **불일치**하다.

**고정효과(FE, within):** 개체 평균을 뺀다. $\ddot y_{it}=y_{it}-\bar y_i=\ddot x_{it}'\beta+\ddot\varepsilon_{it}$. 시간불변 변수의 계수는 식별되지 않는다.

**확률효과(RE):** $\alpha_i\perp x_{it}$를 가정하고 준차분 $y_{it}-\theta\bar y_i$ ($\theta=1-\sqrt{\sigma_\varepsilon^2/(\sigma_\varepsilon^2+T\sigma_\alpha^2)}$)로 GLS 추정한다. 가정이 맞으면 FE보다 효율적이다.

**Hausman 검정(과 Mundlak 대안):** $H=(\hat\beta_{FE}-\hat\beta_{RE})'[V_{FE}-V_{RE}]^{-1}(\hat\beta_{FE}-\hat\beta_{RE})\sim\chi^2_k$. 기각하면 RE의 외생성 가정이 의심된다. 군집 로버스트 환경에서는 $y_{it}$를 $x_{it}$와 개체평균 $\bar x_i$에 회귀해 $\bar x_i$ 계수가 0인지 보는 Mundlak 검정을 쓴다(이 노트북에서 사용).

**TWFE:** 개체·시간 효과를 모두 포함. **군집 표준오차**는 개체 내 상관과 이분산에 대응한다(군집 수가 적으면 불안정).

**이질성:** $y_{it}=\alpha_i+\beta_g x_{it}+\varepsilon_{it}$ ($g$=그룹)처럼 상호작용으로 그룹별 기울기를 추정한다.
'''

DATA_SYN = r'''
def make_unit_panel(N=@@N@@, T=@@T@@, seed=SEED, beta=@@BETA@@, gamma=@@GAMMA@@, rho_x_alpha=0.8, start="@@START@@", freq="@@FREQ@@"):
    # NOT real data: x가 개체효과 alpha와 상관되도록 만들어 Pooled OLS가 편의를 갖게 한 패널. 참값 beta, gamma를 안다.
    rng = np.random.default_rng(seed)
    alpha = rng.normal(0, 3, N); grp = (np.arange(N) % 2)                        # 두 그룹(이질성 비교용)
    dates = pd.date_range(start, periods=T, freq=freq)
    lam = np.cumsum(rng.normal(0, 0.3, T))
    x = rho_x_alpha * alpha[:, None] + rng.normal(0, 1, (N, T))                  # alpha와 상관된 설명변수
    z = rng.normal(0, 1, (N, T))
    beta_i = np.where(grp == 1, beta + 0.5, beta)                                # 그룹 1은 기울기가 0.5 더 큼
    y = alpha[:, None] + lam[None, :] + beta_i[:, None] * x + gamma * z + rng.normal(0, 1, (N, T))
    df = pd.DataFrame({"unit": np.repeat(np.arange(N), T), "t": np.tile(np.arange(T), N), "date": np.tile(dates, N),
                       "y": y.ravel(), "x": x.ravel(), "z": z.ravel(), "group": np.repeat(grp, T)})
    return df

TRUE_BETA, TRUE_GAMMA = @@BETA@@, @@GAMMA@@
panel_df = make_unit_panel()
DATA_KIND = f"SYNTHETIC (NOT real data): 개체효과와 x가 상관된 패널, 참값 beta={TRUE_BETA}(그룹1은 +0.5), gamma={TRUE_GAMMA}"
print("DATA_KIND:", DATA_KIND)
print("개체 수:", panel_df["unit"].nunique(), "| 기간 수:", panel_df["t"].nunique(), "| 관측:", len(panel_df))
'''

DATA_FIN = r'''
def synthetic_sector_panel(N=9, T=120, seed=SEED):
    # NOT real data: 시장수익률과 섹터별 베타가 다른 월별 수익률 패널
    rng = np.random.default_rng(seed); mkt = rng.normal(0.8, 4.0, T); betas = np.linspace(0.6, 1.4, N); alphas = rng.normal(0, 0.3, N)
    r = alphas[:, None] + betas[:, None] * mkt[None, :] + rng.normal(0, 1.5, (N, T))
    return pd.DataFrame(r.T, index=pd.date_range("2014-01-01", periods=T, freq="MS"), columns=[f"S{i}" for i in range(N)]), \
           pd.Series(mkt, index=pd.date_range("2014-01-01", periods=T, freq="MS"), name="mkt")

SECTORS = ["XLF", "XLK", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB"]
rets, mkt, DATA_KIND = None, None, "SYNTHETIC (NOT real data): 섹터 수익률 패널(참 베타 0.6~1.4)"
if USE_LIVE_DATA and ensure("yfinance"):
    try:
        import yfinance as yf
        raw = yf.download(SECTORS + ["SPY"], start="2014-01-01", progress=False, auto_adjust=True)["Close"]
        m = raw.resample("MS").last().pct_change().dropna() * 100
        if m.shape[0] > 60 and m.shape[1] == len(SECTORS) + 1:
            mkt = m["SPY"].rename("mkt"); rets = m[SECTORS]
            DATA_KIND = "REAL: SPDR 섹터 ETF 월수익률(%) (Yahoo Finance via yfinance)"
    except Exception as e:
        print("온라인 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:120])
if rets is None:
    rets, mkt = synthetic_sector_panel()
long_ = rets.reset_index(names="date").melt(id_vars="date", var_name="sector", value_name="y")
long_["unit"] = pd.factorize(long_["sector"])[0]; long_["t"] = pd.factorize(long_["date"])[0]
long_["x"] = long_["date"].map(mkt)                                   # 시장수익률(%)
long_["z"] = long_.groupby("unit")["y"].shift(1)                      # 개체 내 1기 시차 수익률
long_["group"] = (long_["unit"] >= len(SECTORS) // 2).astype(int)     # 뒤쪽 섹터 묶음(이질성 비교용)
panel_df = long_.dropna().reset_index(drop=True)
TRUE_BETA = TRUE_GAMMA = None
print("주의: z는 종속변수의 1기 시차(동적 패널)다. FE 추정은 짧은 T에서 Nickell 편의를 가지며, z의 개체평균은 y의 평균과 기계적으로 연결되어 Mundlak 검정이 쉽게 유의해진다. 해석에 주의한다.")
print("DATA_KIND:", DATA_KIND)
print("개체 수:", panel_df["unit"].nunique(), "| 기간 수:", panel_df["t"].nunique(), "| 관측:", len(panel_df))
'''

MODELS = r'''
def within(df, cols, by="unit"):
    return df[cols] - df.groupby(by)[cols].transform("mean")

ycol, xcols = "y", ["x", "z"]
n_obs = len(panel_df); N_u = panel_df["unit"].nunique()

# (1) Pooled OLS
Xp = np.column_stack([np.ones(n_obs)] + [panel_df[c] for c in xcols])
pooled = ols(panel_df[ycol], Xp, ["const"] + xcols, cov="cluster", groups=panel_df["unit"])

# (2) 고정효과 (within 변환). 절편은 식별되지 않으므로 제외. 자유도는 N개 개체평균만큼 보정
W = within(panel_df, [ycol] + xcols)
fe = ols(W[ycol], W[xcols].to_numpy(), xcols, cov="cluster", groups=panel_df["unit"])
dof_fix = (n_obs - len(xcols)) / (n_obs - len(xcols) - N_u)                      # 군집 SE의 소표본 보정(근사)
fe["se"] = fe["se"] * np.sqrt(dof_fix)

# (3) 확률효과 (준차분; 분산성분은 within/between 잔차로 추정)
Tn = panel_df.groupby("unit").size().mean()
sig_e2 = float(np.sum(fe["resid"] ** 2) / (n_obs - N_u - len(xcols)))
B = panel_df.groupby("unit")[[ycol] + xcols].mean()
Xb = np.column_stack([np.ones(len(B)), B[xcols].to_numpy()])
bb = ols(B[ycol], Xb, ["const"] + xcols, cov="nonrobust")
sig_b2 = float(np.sum(bb["resid"] ** 2) / (len(B) - Xb.shape[1]))
sig_a2 = max(sig_b2 - sig_e2 / Tn, 1e-8)
theta = 1 - np.sqrt(sig_e2 / (sig_e2 + Tn * sig_a2))
means = panel_df.groupby("unit")[[ycol] + xcols].transform("mean")
Q = panel_df[[ycol] + xcols] - theta * means
Xr = np.column_stack([np.full(n_obs, 1 - theta)] + [Q[c] for c in xcols])
re = ols(Q[ycol], Xr, ["const"] + xcols, cov="cluster", groups=panel_df["unit"])

# (4) 시간효과 포함 TWFE (개체·시간 이중 demeaning, 균형패널 가정)
def twoway(df, cols):
    g_u = df.groupby("unit")[cols].transform("mean"); g_t = df.groupby("t")[cols].transform("mean"); g = df[cols].mean()
    return df[cols] - g_u - g_t + g
x_time_only = bool(panel_df.groupby("t")["x"].nunique().max() == 1)          # x가 모든 개체에 같은 값이면 시간효과에 흡수됨
tw_cols = [c for c in xcols if not (c == "x" and x_time_only)]
if x_time_only:
    print("주의: x(시장수익률)는 시점마다 모든 개체에 동일하므로 시간효과에 완전히 흡수된다 -> TWFE에서는 x를 뺀다.")
W2 = twoway(panel_df, [ycol] + tw_cols)
twfe = ols(W2[ycol], W2[tw_cols].to_numpy(), tw_cols, cov="cluster", groups=panel_df["unit"])

coef_ = lambda r, names: pd.Series(np.asarray(r["beta"])[-len(names):], index=names)
se_ = lambda r, names: pd.Series(np.asarray(r["se"])[-len(names):], index=names)
tab = pd.DataFrame({"Pooled OLS": coef_(pooled, xcols), "FE": coef_(fe, xcols), "RE": coef_(re, xcols),
                    "TWFE": coef_(twfe, tw_cols)}).reindex(xcols)
se_tab = pd.DataFrame({"Pooled OLS": se_(pooled, xcols), "FE": se_(fe, xcols), "RE": se_(re, xcols),
                       "TWFE": se_(twfe, tw_cols)}).reindex(xcols)
print("계수 추정치 (행: 변수)"); show(tab)
print("\n군집 표준오차"); show(se_tab)
print(f"\n분산성분: sigma_e^2={sig_e2:.3f}, sigma_alpha^2={sig_a2:.3f}, theta={theta:.3f}")
if TRUE_BETA is not None:
    print(f"참값: beta(x)≈{TRUE_BETA}~{TRUE_BETA+0.5}(그룹 평균 약 {TRUE_BETA+0.25}), gamma(z)={TRUE_GAMMA}  -> FE/TWFE가 참값에 가깝고 Pooled·RE는 편의가 있어야 한다.")
'''

HAUSMAN = r'''
# Hausman 검정의 대안: Mundlak 보조회귀. y를 x, z와 개체평균(x̄_i, z̄_i)에 회귀하고 평균항의 계수가 0인지 군집 로버스트 Wald로 검정한다.
# 평균항이 유의하면 개체효과와 설명변수가 상관되어 RE의 외생성 가정이 의심된다(FE 선호). 군집 SE에서도 PSD 문제가 없다.
Mbar = panel_df.groupby("unit")[xcols].transform("mean").add_suffix("_bar")
Mbar = Mbar[[c for c in Mbar.columns if Mbar[c].nunique() > 1 and Mbar[c].groupby(panel_df["unit"]).first().std() > 1e-9]]   # 개체 간 변동이 없는 평균항(예: 모든 개체 공통 x)은 제외
Xm = np.column_stack([np.ones(n_obs)] + [panel_df[c] for c in xcols] + [Mbar[c] for c in Mbar.columns])
mund = ols(panel_df[ycol], Xm, ["const"] + xcols + list(Mbar.columns), cov="cluster", groups=panel_df["unit"])
idx = [mund["names"].index(c) for c in Mbar.columns]
bm = mund["beta"][idx]; Vm = mund["V"][np.ix_(idx, idx)]
Wm = float(bm @ np.linalg.pinv(Vm) @ bm); pm = 1 - stats.chi2.cdf(Wm, len(idx))
show(mund["table"].loc[list(Mbar.columns)])
print(f"Mundlak Wald = {Wm:.2f}, p = {pm:.4f}  (작으면 RE 외생성 의심 -> FE 선호; 군집 수 {N_u}개의 소표본 한계 주의)")
'''

HETERO = r'''
# 그룹별 이질적 기울기: within 변환 후 x × group 상호작용
W3 = within(panel_df, [ycol, "x", "z"]); g_dm = panel_df["group"] - panel_df.groupby("unit")["group"].transform("mean")
Xh = np.column_stack([W3["x"], W3["x"] * panel_df["group"], W3["z"]])
hf = ols(W3[ycol], Xh, ["x (그룹0)", "x × 그룹1 (추가 기울기)", "z"], cov="cluster", groups=panel_df["unit"])
show(hf["table"])
if TRUE_BETA is not None:
    print(f"참값: x 기울기={TRUE_BETA}, 그룹1 추가 기울기=0.5")
'''

PLOT_ = r'''
fig, ax = plt.subplots(figsize=(9, 3.6))
ypos = np.arange(len(xcols)); w = 0.2
for i, name in enumerate(["Pooled OLS", "FE", "RE", "TWFE"]):
    ax.errorbar(tab[name].to_numpy(float), ypos + (i - 1.5) * w, xerr=1.96 * se_tab[name].to_numpy(float), fmt="o", label=name)
ax.set_yticks(ypos); ax.set_yticklabels(xcols); ax.axvline(0, color="k", lw=0.5); ax.legend(); ax.set_title("추정치와 95% 구간(군집 SE)"); plt.show()
'''

INTERP = r'''
## 3. 결과 해석 작성
1. Pooled OLS와 FE의 차이가 큰 변수는 무엇인가? 그 차이는 개체 고유 효과와 설명변수의 상관(누락변수 편의)과 어떻게 연결되는가?
2. Mundlak(Hausman 대안) 검정 결과로 RE와 FE 중 무엇을 택하는가? 군집 수가 적을 때 Wald 검정의 한계도 적는다.
3. 시간효과(TWFE)를 넣으면 계수가 어떻게 바뀌는가? 공통 충격을 통제한 의미를 적는다.
4. 이질성: 그룹별 기울기 차이가 통계적으로 유의한가? 개체 수(군집 수)가 적을 때 군집 SE의 신뢰 한계를 논의한다.
5. `DATA_KIND`가 합성이면 **참값 회복 여부**로 추정기를 점검하고, 실제 자료이면 인과적 해석을 단정하지 않는다.

**제출:** 모형별 계수표, 그림, Mundlak/Hausman 결과, 이질성 표, 해석 단락, 한계.
'''

CFG = {
 "Finance":           dict(kind="fin"),
 "RealEstate":        dict(N="40", T="60", BETA="-1.5", GAMMA="0.8", START="2010-01-01", FREQ="MS", note="단위: 지역(주). 설명변수 x는 금리 변화, z는 소득 증가율의 합성 대용이다."),
 "Manufacturing":     dict(N="30", T="48", BETA="0.9", GAMMA="0.4", START="2020-01-01", FREQ="MS", note="단위: 공장. x는 자동화 투자, z는 가동률의 합성 대용, y는 생산성이다."),
 "PublicPolicy":      dict(N="50", T="20", BETA="2.0", GAMMA="1.0", START="2005-01-01", FREQ="MS", note="단위: 지자체. x는 정책 지출, z는 인구 구조의 합성 대용이다."),
 "EnergyEnvironment": dict(N="36", T="40", BETA="-0.7", GAMMA="0.5", START="2010-01-01", FREQ="MS", note="단위: 지역. x는 에너지 가격, z는 소득의 합성 대용, y는 배출량이다."),
 "BusinessMarketing": dict(N="45", T="52", BETA="-1.2", GAMMA="1.1", START="2023-01-01", FREQ="W-MON", note="단위: 점포. x는 가격, z는 프로모션 강도의 합성 대용, y는 매출이다."),
}

def build(domain, title, question):
    c = CFG[domain]
    if c.get("kind") == "fin":
        data = DATA_FIN; note = "섹터 ETF 월수익률 패널(온라인 성공 시 실제 자료). x는 시장수익률(%), z는 개체 내 1기 시차 수익률이다."
    else:
        data = DATA_SYN.replace("@@N@@", c["N"]).replace("@@T@@", c["T"]).replace("@@BETA@@", c["BETA"]).replace("@@GAMMA@@", c["GAMMA"]) \
                       .replace("@@START@@", c["START"]).replace("@@FREQ@@", c["FREQ"]); note = c["note"]
    return [md(f"# Chapter 6 · {title}\n\n**연구질문:** {question}\n\n{note}\n\n> 위에서 아래로 실행하면 끝까지 동작합니다."),
            md(THEORY), code(SETUP), code(PANEL_TOOLS), md("## 2. 데이터"), code(data),
            md("## 3. Pooled · FE · RE · TWFE"), code(MODELS), code(HAUSMAN), code(PLOT_),
            md("## 4. 그룹별 이질성"), code(HETERO), md(INTERP)]

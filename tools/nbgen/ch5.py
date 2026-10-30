from .cells import md, code
from .common import SETUP, PANEL_TOOLS
from .data_cells import PUBLICPOLICY

THEORY = r'''
## 1. 핵심 개념·수식

**잠재결과와 처치효과:** 처치 단위 $i$의 사후 효과 $\tau_{it}=Y_{it}(1)-Y_{it}(0)$. 관측되지 않는 $Y_{it}(0)$(반사실)을 어떻게 대체하느냐가 방법을 가른다.

**ITS(중단 시계열):** $Y_t=\beta_0+\beta_1 t+\beta_2 D_t+\beta_3 (t-T_0)D_t+\varepsilon_t$, $D_t=\mathbf 1[t\ge T_0]$. $\beta_2$=즉시 수준변화, $\beta_3$=기울기 변화. 식별은 "개입이 없었다면 사전추세가 이어졌다"와 **동시 사건 부재**에 의존한다. 오차의 자기상관 때문에 HAC(Newey–West) 표준오차를 쓴다.

**DID(이중차분):** $Y_{it}=\alpha_i+\lambda_t+\tau\, D_{it}+\varepsilon_{it}$. 식별은 **평행추세**(처치가 없었다면 처치집단과 비교집단의 평균 변화가 같다)에 의존한다. 사전 이벤트 스터디 계수가 0과 다르면 가정이 의심된다.

**합성통제(SCM):** 비처치 단위의 가중평균으로 처치 단위의 사전 경로를 재현한다. $\hat w=\arg\min_{w\ge0,\ \sum w=1}\sum_{t<T_0}\big(Y_{1t}-\sum_j w_j Y_{jt}\big)^2$, 효과 $\hat\tau_t=Y_{1t}-\sum_j \hat w_j Y_{jt}$ ($t\ge T_0$). 추론은 **in-space 위약**(각 도너를 가짜 처치로 놓고 사후/사전 RMSPE 비를 비교)으로 한다.

> 이 노트북의 합성 패널은 **효과 $\tau$를 우리가 알고 있다.** 추정기가 이를 회복하는지를 확인하는 것이 목적이며, 실제 사건의 효과 추정이 아니다.
'''

DATA_SYN = r'''
TAU = @@TAU@@
panel, treated, T0 = make_panel(N=24, T=48, n_treated=@@NT@@, T0=30, tau=TAU, seed=SEED, parallel=True)   # 평행추세가 성립하도록 설계
DATA_KIND = f"SYNTHETIC (NOT real data): 공통추세 패널(평행추세 성립), 주입 효과 tau={TAU}"
@@FREQ_LINE@@
print("DATA_KIND:", DATA_KIND)
print("패널 크기(시점×단위):", panel.shape, "| 처치 단위:", treated, "| 처치 시작 인덱스 T0 =", T0)
panel.iloc[:, :6].plot(figsize=(10, 3.6), title="일부 단위의 결과변수"); plt.axvline(panel.index[T0], color="k", ls="--"); plt.show()
'''

DATA_PROP99 = r'''
def parse_prop99(raw):
    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
    df = pd.read_csv(io.StringIO(text), sep=";")
    cols = {c.strip().lower(): c for c in df.columns}
    for need in ("state", "year", "packspercapita", "treated"):
        if need not in cols: raise ValueError("예상 열 없음: " + need)
    return df.rename(columns={cols["state"]: "State", cols["year"]: "Year",
                              cols["packspercapita"]: "PacksPerCapita", cols["treated"]: "treated"})

panel, treated, T0, DATA_KIND, TAU = None, None, None, None, None
if USE_LIVE_DATA:
    try:
        df99 = parse_prop99(fetch_bytes("https://raw.githubusercontent.com/synth-inference/synthdid/master/data/california_prop99.csv"))
        wide = df99.pivot(index="Year", columns="State", values="PacksPerCapita").sort_index()
        tr_state = df99.loc[df99["treated"] == 1, "State"].unique().tolist()
        first_year = int(df99.loc[df99["treated"] == 1, "Year"].min())
        if wide.isna().any().any() or len(tr_state) != 1:
            raise ValueError("패널이 불균형이거나 처치 단위가 하나가 아님")
        panel = wide[tr_state + [c for c in wide.columns if c not in tr_state]]
        treated = tr_state; T0 = int(np.where(panel.index == first_year)[0][0])
        DATA_KIND = "REAL: California Prop 99 (synthdid 저장소 california_prop99.csv)"
    except Exception as e:
        print("Prop 99 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:120])
if panel is None:
    TAU = -8.0
    panel, treated, T0 = make_panel(N=30, T=31, start="1970-01-01", freq="D", n_treated=1, T0=19, tau=TAU, seed=SEED)
    panel.index = pd.Index(range(1970, 2001), name="Year")
    DATA_KIND = f"SYNTHETIC (NOT real data): 요인모형 패널(1970-2000, 단위별 추세 상이 -> 평행추세 위반), 주입 효과 tau={TAU}"
print("DATA_KIND:", DATA_KIND)
print("패널 크기:", panel.shape, "| 처치 단위:", treated, "| 처치 시작 위치 T0 =", T0, "(", panel.index[T0], ")")
panel.iloc[:, :8].plot(figsize=(10, 3.6), legend=False, title="일부 단위의 결과변수"); plt.axvline(panel.index[T0], color="k", ls="--"); plt.show()
'''

ITS = r'''
# ---- (1) ITS: 처치 단위 한 개의 시계열 ----
u = treated[0]; ys = panel[u].to_numpy(float); n = len(ys); t = np.arange(n)
D_ = (t >= T0).astype(float); TA = (t - T0) * D_
X = np.column_stack([np.ones(n), t, D_, TA])
fit_its = ols(ys, X, ["const", "trend", "level_change(beta2)", "slope_change(beta3)"], cov="HAC", maxlags=3)
show(fit_its["table"])
pre = np.arange(n) < T0
fit_pre = ols(ys[pre], np.column_stack([np.ones(pre.sum()), t[pre]]), ["const", "trend"], cov="nonrobust")
cf = fit_pre["beta"][0] + fit_pre["beta"][1] * t                          # 사전추세 외삽(반사실)
plt.figure(figsize=(10, 3.8)); plt.plot(panel.index, ys, label=f"observed ({u})"); plt.plot(panel.index, cf, "--", label="사전추세 외삽(반사실)")
plt.axvline(panel.index[T0], color="k", ls=":"); plt.legend(); plt.title("ITS"); plt.show()
dw = np.sum(np.diff(fit_its["resid"]) ** 2) / np.sum(fit_its["resid"] ** 2)
print(f"Durbin-Watson={dw:.2f} (2 근처면 1차 자기상관 약함; HAC로 표준오차 보정)")
its_avg_effect = float(np.mean(ys[T0:] - cf[T0:]))
print(f"사후 평균 (관측-외삽) = {its_avg_effect:.3f}" + (f" | 주입 효과 tau={TAU}" if TAU is not None else ""))
'''

DID = r'''
# ---- (2) DID: 처치 단위 vs 비교 단위, 이원고정효과 + 이벤트 스터디 ----
long = panel.reset_index().melt(id_vars=panel.index.name or "index", var_name="unit", value_name="y")
tcol = panel.index.name or "index"
long["t"] = long[tcol].map({v: i for i, v in enumerate(panel.index)}); long = long.drop(columns=tcol)
long["treated_unit"] = long["unit"].isin(treated).astype(float); long["post"] = (long["t"] >= T0).astype(float)
long["D"] = long["treated_unit"] * long["post"]

def twfe_design(df, regs):
    U = pd.get_dummies(df["unit"], drop_first=True, dtype=float); Tm = pd.get_dummies(df["t"], drop_first=True, dtype=float, prefix="t")
    cols = [np.ones(len(df))] + [df[r].to_numpy(float) for r in regs]
    names = ["const"] + list(regs)
    return np.column_stack(cols + [U.to_numpy(), Tm.to_numpy()]), names + list(U.columns) + list(Tm.columns)

Xd, nm = twfe_design(long, ["D"])
rows_ = []
for cv in ("HC1", "cluster"):
    f_ = ols(long["y"], Xd, nm, cov=cv, groups=long["unit"])
    rows_.append({"SE 종류": cv, "tau_hat": float(f_["beta"][1]), "se": float(f_["se"][1]), "p": float(f_["p"][1])})
fit_did = ols(long["y"], Xd, nm, cov="cluster", groups=long["unit"])
print("TWFE DID | 처치 단위 수 =", len(treated), "| 비교 단위 수 =", panel.shape[1] - len(treated))
show(pd.DataFrame(rows_).set_index("SE 종류"))
if len(treated) < 5:
    print("주의: 처치 군집이 적으면 군집 SE는 과소추정되기 쉽다. 아래 순열(위약) p값을 더 신뢰한다. 실제 연구는 wild cluster bootstrap 등을 사용한다.")

# 순열 추론: 비교 단위에서 같은 수의 가짜 처치 단위를 뽑아 DID 추정치의 분포를 만든다
Pv = panel.to_numpy(float); ctrl_idx = [i for i, c in enumerate(panel.columns) if c not in treated]
def did_2x2(idx_t, idx_c):
    f = lambda idx, sl: Pv[sl][:, idx].mean()
    return (f(idx_t, slice(T0, None)) - f(idx_t, slice(0, T0))) - (f(idx_c, slice(T0, None)) - f(idx_c, slice(0, T0)))
rng_ = np.random.default_rng(SEED); draws = []
for _ in range(500):
    pick = rng_.choice(ctrl_idx, size=len(treated), replace=False); rest = [i for i in ctrl_idx if i not in pick]
    draws.append(did_2x2(list(pick), rest))
tau_2x2 = did_2x2([i for i, c in enumerate(panel.columns) if c in treated], ctrl_idx)
p_perm_did = (1 + np.sum(np.abs(draws) >= abs(tau_2x2))) / (1 + len(draws))
print(f"2x2 DID 추정치 = {tau_2x2:.3f} | 위약 분포 sd = {np.std(draws):.3f} | 순열 p = {p_perm_did:.3f}")

# 이벤트 스터디: 처치 시점 대비 상대시점 더미(-1 기준) -> 사전 계수가 0 근처인지 평행추세 점검
long["rel"] = long["t"] - T0
rels_all = [r for r in sorted(long["rel"].unique()) if r != -1]          # 모든 상대시점 더미(-1 기준): 끝점을 묶지 않아 편의가 생기지 않게 함
for r in rels_all:
    long[f"ev_{r}"] = ((long["rel"] == r) & (long["treated_unit"] == 1)).astype(float)
Xe, nme = twfe_design(long, [f"ev_{r}" for r in rels_all])
fit_ev = ols(long["y"], Xe, nme, cov="nonrobust")        # 상대시점 더미가 소수 관측만 덮어 HC1/군집 SE가 붕괴하므로 동분산 SE 사용(근사)
ev_all = fit_ev["table"].loc[[f"ev_{r}" for r in rels_all]].copy(); ev_all.index = rels_all
ev = ev_all.loc[[r for r in rels_all if -8 <= r <= 8]]                    # 그림은 -8..8만
fig, ax = plt.subplots(figsize=(9, 3.6)); ax.errorbar(ev.index, ev["coef"], yerr=1.96 * ev["se"], fmt="o")
ax.axhline(0, color="k"); ax.axvline(-0.5, color="gray", ls=":"); ax.set_title("이벤트 스터디(기준: 상대시점 -1)"); plt.show()
pre_ev = ev_all.loc[[r for r in rels_all if r < 0]]
wald = float((pre_ev["coef"] ** 2 / pre_ev["se"] ** 2).sum()); pw = 1 - stats.chi2.cdf(wald, len(pre_ev))
print(f"사전계수 근사 Wald(동분산 SE, 공분산 무시) = {wald:.2f}, p = {pw:.3f}  (작으면 평행추세 의심; 근사 검정임)")
'''

SCM = r'''
# ---- (3) 합성통제(SCM) + in-space 위약 ----
def scm_weights(y1_pre, Y0_pre):
    J = Y0_pre.shape[1]
    f = lambda w: np.sum((y1_pre - Y0_pre @ w) ** 2)
    res = optimize.minimize(f, np.full(J, 1 / J), method="SLSQP", bounds=[(0, 1)] * J,
                            constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}], options={"maxiter": 300, "ftol": 1e-10})
    return res.x

def scm_gap(unit, donors, P):
    y1 = P[unit].to_numpy(float); Y0 = P[donors].to_numpy(float)
    w = scm_weights(y1[:T0], Y0[:T0]); gap = y1 - Y0 @ w
    rmspe_pre = np.sqrt(np.mean(gap[:T0] ** 2)); rmspe_post = np.sqrt(np.mean(gap[T0:] ** 2))
    return w, gap, rmspe_pre, rmspe_post

unit1 = treated[0]; donors = [c for c in panel.columns if c not in treated]
w, gap, rp, rq = scm_gap(unit1, donors, panel)
top = pd.Series(w, index=donors).sort_values(ascending=False).head(5)
print("상위 도너 가중치:"); show(top.to_frame("weight"))
print(f"사전 RMSPE={rp:.3f} | 사후 평균 gap={gap[T0:].mean():.3f}" + (f" | 주입 효과 tau={TAU}" if TAU is not None else ""))
plac = {}
for d_ in donors:                                   # in-space 위약: 각 도너를 가짜 처치 단위로
    others = [c for c in donors if c != d_]
    _, g_, a_, b_ = scm_gap(d_, others, panel)
    plac[d_] = (a_, b_, g_)
ratio_true = rq / max(rp, 1e-9)
ratios = np.array([b / max(a, 1e-9) for a, b, _ in plac.values()])
p_perm = (1 + np.sum(ratios >= ratio_true)) / (1 + len(ratios))
print(f"사후/사전 RMSPE 비: 처치={ratio_true:.2f} | 위약 분포 중앙값={np.median(ratios):.2f} | 순열 p = {p_perm:.3f} (도너 {len(ratios)}개 기준 최소 p={1/(1+len(ratios)):.3f})")
fig, ax = plt.subplots(figsize=(10, 3.8))
for d_, (a_, b_, g_) in plac.items():
    if a_ < 2 * max(rp, 1e-9) + 1e-9: ax.plot(panel.index, g_, color="gray", alpha=0.4)
ax.plot(panel.index, gap, color="C3", lw=2, label=f"{unit1} (처치)"); ax.axvline(panel.index[T0], color="k", ls=":"); ax.axhline(0, color="k", lw=0.5)
ax.set_title("SCM gap과 in-space 위약(사전 적합이 좋은 도너만 표시)"); ax.legend(); plt.show()
'''

COMPARE = r'''
rows = [{"방법": "ITS (HAC) 수준변화 β2", "추정": float(fit_its["beta"][2]), "se": float(fit_its["se"][2])},
        {"방법": "TWFE DID τ (군집 SE)", "추정": float(fit_did["table"].loc["D", "coef"]), "se": float(fit_did["table"].loc["D", "se"])}]
if "gap" in globals():
    rows.append({"방법": "SCM 사후 평균 gap", "추정": float(gap[T0:].mean()), "se": np.nan})
tab = pd.DataFrame(rows).set_index("방법")
if TAU is not None: tab["주입된 tau"] = TAU
show(tab)
print("ITS의 수준변화(β2)는 처치 직후 한 시점의 변화이고, DID·SCM은 사후 평균효과라 정의가 다르다. 비교 시 정의를 맞춰 읽는다.")
'''

INTERP = r'''
## 3. 결과 해석 작성
1. `DATA_KIND`를 먼저 적는다. 합성 패널이면 주입 효과 $\tau$와 추정치를 비교해 **추정기의 회복 여부**를 서술한다. 실제 자료(Prop 99)이면 추정치를 인과효과로 단정하지 않고 가정(평행추세·간섭 없음·도너 풀)과 함께 해석한다.
2. 이벤트 스터디의 사전계수와 사전 RMSPE가 **식별 가정의 증거**로 충분한지, 아니면 단지 "반증 실패"인지 구분한다.
3. 처치 단위가 하나(또는 소수)일 때 표준오차·p값의 신뢰 한계를 논의한다(순열 p의 최소값 $1/(1+J)$).
4. 한계: 동시 정책, 예상 효과(anticipation), 전염(spillover), 효과의 이질성(동시기 처치가 여러 개일 때 TWFE의 편의).

**제출:** 세 방법의 추정표, 이벤트 스터디/SCM gap 그림, 위약 결과, 가정별 점검 표, 해석 단락.
'''

# 도메인 구성
CFG = {
 "Finance":            dict(data="syn", tau="-6.0", nt="1", freq="MS", methods="its"),
 "RealEstate":         dict(data="syn", tau="-5.0", nt="4", freq="MS", methods="did"),
 "Manufacturing":      dict(data="syn", tau="-7.0", nt="1", freq="MS", methods="its"),
 "PublicPolicy":       dict(data="prop99", methods="all"),
 "EnergyEnvironment":  dict(data="syn", tau="-9.0", nt="3", freq="MS", methods="did_its"),
 "BusinessMarketing":  dict(data="syn", tau="6.0", nt="3", freq="MS", methods="did_its"),
}
UNIT_NOTE = {
 "Finance": "결과변수는 월별 지표(예: 변동성 지수), 처치 단위는 사건을 겪은 한 개의 시계열로 가정한 **합성** 설정이다.",
 "RealEstate": "단위는 지역, 처치는 임의의 가상 정책(실제 정책 아님)이다.",
 "Manufacturing": "단위는 생산라인, 처치는 가상의 공정 개선이다.",
 "PublicPolicy": "실제 자료 연결 시 California Prop 99(1988년 담배세 인상) 사례를 사용한다. 실패하면 합성 패널.",
 "EnergyEnvironment": "단위는 지역, 처치는 가상의 환경규제이며 결과는 대기질 지표의 대용 합성값이다.",
 "BusinessMarketing": "단위는 점포/지역, 처치는 가상의 광고 캠페인이다.",
}

def build(domain, title, question):
    c = CFG[domain]
    cells = [md(f"# Chapter 5 · {title}\n\n**연구질문:** {question}\n\n{UNIT_NOTE[domain]}\n\n> 위에서 아래로 실행하면 끝까지 동작합니다."),
             md(THEORY), code(SETUP), code(PANEL_TOOLS), md("## 2. 데이터")]
    if c["data"] == "prop99":
        cells.append(code(DATA_PROP99))
    else:
        cells.append(code(DATA_SYN.replace("@@TAU@@", c["tau"]).replace("@@NT@@", c["nt"]).replace("@@FREQ_LINE@@", "")))
        cells[-1] = code(cells[-1][1] + "\n")      # no-op, keep
    cells += [md("## 3. ITS"), code(ITS), md("## 4. DID와 이벤트 스터디"), code(DID)]
    if domain in ("PublicPolicy",) or c["methods"] in ("all",):
        cells += [md("## 5. 합성통제와 위약검정"), code(SCM)]
    cells += [md("## 6. 방법 비교"), code(COMPARE), md(INTERP)]
    return cells

from .cells import md, code
from .common import SETUP, PANEL_TOOLS
from .data_cells import LOADERS

WHICH = {"Finance": "", "RealEstate": "price", "Manufacturing": "sensor", "PublicPolicy": "complaints",
         "EnergyEnvironment": "temp", "BusinessMarketing": ""}

THEORY_WF = r'''
## 1. 핵심 개념·수식

**누수(leakage):** 예측 시점 $t$에 알 수 없는 정보가 특성·전처리·분할에 들어가 성능이 과대평가되는 문제. 대표 경로 세 가지.
1. **전처리 누수:** 표준화·결측대체·모수 추정을 전체 자료로 한다(학습구간 통계만 써야 함).
2. **미래 정보 누수:** 중심 이동평균 등 $y_{t+k}$를 포함하는 특성.
3. **분할 누수:** 시계열에 무작위 K-겹 교차검증을 쓴다(인접 관측이 학습·검증에 섞임).

**Walk-forward(롤링 오리진) 평가:** 시점 $T_1<T_2<\dots$마다 $[1,T_k]$로 학습하고 $(T_k,T_k+h]$를 평가한다. 폴드별 오차의 분포(평균·분산·최악)를 본다.

**Diebold–Mariano 검정:** 손실차 $d_t=L(e^{A}_t)-L(e^{B}_t)$의 평균이 0인지 검정한다. $\mathrm{DM}=\bar d/\sqrt{\widehat{\mathrm{LRV}}(d)/n}$.

**부트스트랩 신뢰구간:** 폴드 손실차를 블록 부트스트랩하여 우열의 불확실성을 본다.
'''

WF_CORE = r'''
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold

def make_X(s, lags=(1, 2, 3, 5, 10), rolls=(5, 20)):
    X = pd.DataFrame({f"lag_{k}": s.shift(k) for k in lags})
    for w in rolls:
        X[f"rm_{w}"] = s.shift(1).rolling(w).mean(); X[f"rs_{w}"] = s.shift(1).rolling(w).std()
    return X

def dm_stat(d, h=1):
    d = np.asarray(d, float); n = len(d); dbar = d.mean(); var = np.var(d)
    for l in range(1, max(h, 1)):
        var += 2 * (1 - l / h) * np.mean((d[l:] - dbar) * (d[:-l] - dbar))
    stat = dbar / np.sqrt(var / n); return stat, 2 * (1 - stats.norm.cdf(abs(stat)))

def block_bootstrap_ci(d, block=5, B=1000, seed=SEED):
    rng = np.random.default_rng(seed); d = np.asarray(d, float); n = len(d); out = []
    for _ in range(B):
        starts = rng.integers(0, max(n - block + 1, 1), size=int(np.ceil(n / block)))
        out.append(np.concatenate([d[s0:s0 + block] for s0 in starts])[:n].mean())
    return np.percentile(out, [2.5, 97.5])
'''

WF_FIN = r'''
r = ret.astype(float); X = make_X(r); data = pd.concat([X, r.rename("target")], axis=1).dropna()
XX, yy = data.drop(columns="target"), data["target"]
def models():
    return {"Ridge": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
            "HistGB": HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, random_state=SEED)}

# ---- A. 올바른 평가: Walk-forward (확장 창, 폴드 8개) ----
n = len(data); n_folds = 8; fold = max(100, n // 12); start = n - n_folds * fold
rows, loss = [], {"hist_mean": [], "Ridge": [], "HistGB": []}
for k in range(n_folds):
    a, b = start + k * fold, start + (k + 1) * fold
    Xtr, ytr, Xte, yte = XX.iloc[:a], yy.iloc[:a], XX.iloc[a:b], yy.iloc[a:b]
    base = np.full(len(yte), ytr.mean()); loss["hist_mean"].append(np.mean((yte - base) ** 2))
    for name, m in models().items():
        m.fit(Xtr, ytr); loss[name].append(np.mean((yte.to_numpy() - m.predict(Xte)) ** 2))
L = pd.DataFrame(loss, index=[f"fold{k+1}" for k in range(n_folds)])
print("폴드별 MSE:"); show(L)
print("평균 MSE:"); show(L.mean().to_frame("MSE"))
for name in ("Ridge", "HistGB"):
    d = L["hist_mean"] - L[name]            # 양수면 모델이 역사평균보다 낫다
    st, pv = dm_stat(d.to_numpy()); lo, hi = block_bootstrap_ci(d.to_numpy(), block=2)
    print(f"{name} vs 역사평균: 평균 손실개선={d.mean():.4f}, DM p≈{pv:.3f} (폴드 {len(d)}개, 근사), 부트스트랩 95% CI=[{lo:.4f},{hi:.4f}]")
wf_mse = float(L["Ridge"].mean())
'''

LEAK_FIN = r'''
# ---- B. 누수를 일부러 만들어 성능이 얼마나 부풀려지는지 확인 ----
split = int(len(data) * 0.8)
def holdout(Xa, ya, scale_on_all=False, model=None):
    Xa = Xa.copy()
    mu_sd = (Xa.mean(), Xa.std()) if scale_on_all else (Xa.iloc[:split].mean(), Xa.iloc[:split].std())   # 누수 1: 전체 통계로 표준화
    Z = (Xa - mu_sd[0]) / mu_sd[1]
    m = model or Ridge(alpha=10.0); m.fit(Z.iloc[:split], ya.iloc[:split]); p = m.predict(Z.iloc[split:])
    return float(np.mean((ya.iloc[split:].to_numpy() - p) ** 2))
res_leak = {"정상(학습구간 통계로 표준화)": holdout(XX, yy)}
res_leak["누수1: 전체 자료로 표준화"] = holdout(XX, yy, scale_on_all=True)
# 누수 2: 중심 이동평균 특성(미래 포함)
Xc = XX.copy(); Xc["centered_ma"] = r.rolling(5, center=True).mean().loc[XX.index]; Xc = Xc.dropna(); yc = yy.loc[Xc.index]
split_c = int(len(Xc) * 0.8)
m2 = Ridge(alpha=1.0).fit(Xc.iloc[:split_c], yc.iloc[:split_c])
res_leak["누수2: 중심 이동평균(미래 포함)"] = float(np.mean((yc.iloc[split_c:].to_numpy() - m2.predict(Xc.iloc[split_c:])) ** 2))
# 누수 3: 무작위 K-겹 (시간 섞임)
kf = KFold(n_splits=5, shuffle=True, random_state=SEED); errs = []
for tr_i, te_i in kf.split(XX):
    m3 = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, random_state=SEED).fit(XX.iloc[tr_i], yy.iloc[tr_i])
    errs.append(np.mean((yy.iloc[te_i].to_numpy() - m3.predict(XX.iloc[te_i])) ** 2))
res_leak["누수3: 무작위 K-겹 CV (HistGB)"] = float(np.mean(errs))
res_leak["참고: 역사평균 기준선"] = float(np.mean((yy.iloc[split:].to_numpy() - yy.iloc[:split].mean()) ** 2))
tabL = pd.Series(res_leak).to_frame("MSE"); show(tabL)
print("해석 가이드: 누수 설정의 MSE가 정상 설정보다 유의하게 작다면 그 차이가 '누수가 만든 허위 성능'이다. 수익률은 예측이 어려워 차이가 작을 수 있다 -> 누수의 영향이 큰 자료는 이후 도메인(센서·프로모션)에서 확인.")
'''

# ---- 일반 시계열(부동산 기간·지역 / 에너지 체제변화) ----
SUBSAMPLE = r'''
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def make_X(s, lags=(1, 2, 3, 7, 14), rolls=(7, 28)):
    X = pd.DataFrame({f"lag_{k}": s.shift(k) for k in lags})
    for w in rolls:
        X[f"rm_{w}"] = s.shift(1).rolling(w).mean()
    return X

def rolling_origin(s, n_folds=8, fold=None, kind="ridge", window=None, lags=(1, 2, 3, 7, 14)):
    s = s.astype(float); X = make_X(s, lags=lags); data = pd.concat([X, s.rename("target")], axis=1).dropna()
    XX, yy = data.drop(columns="target"), data["target"]; n = len(data); fold = fold or max(30, n // (n_folds + 3))
    start = n - n_folds * fold; out = []
    for k in range(n_folds):
        a, b = start + k * fold, start + (k + 1) * fold
        lo = 0 if window is None else max(0, a - window)
        mdl = make_pipeline(StandardScaler(), Ridge(alpha=1.0)) if kind == "ridge" else HistGradientBoostingRegressor(max_iter=120, learning_rate=0.06, random_state=SEED)
        mdl.fit(XX.iloc[lo:a], yy.iloc[lo:a]); p = mdl.predict(XX.iloc[a:b]); naive = XX["lag_1"].iloc[a:b].to_numpy()
        out.append({"fold": k + 1, "end": XX.index[b - 1], "RMSE": rmse(yy.iloc[a:b], p), "RMSE_naive": rmse(yy.iloc[a:b], naive)})
    return pd.DataFrame(out)
'''

RE_ROB = r'''
# ---- 지역·기간 강건성: 여러 지역(합성 패널) × 시기 ----
rng = np.random.default_rng(SEED)
def synth_region(seed, trend, amp, vol, n=240):
    rg = np.random.default_rng(seed); t = np.arange(n)
    return pd.Series(100 + trend * t + amp * np.sin(2 * np.pi * (t % 12) / 12) + np.cumsum(rg.normal(0, vol, n)),
                     index=pd.date_range("2005-01-01", periods=n, freq="MS"))
regions = {"지역A(완만)": synth_region(1, 0.25, 1.0, 0.3), "지역B(변동 큼)": synth_region(2, 0.40, 2.5, 0.9),
           "지역C(계절 강함)": synth_region(3, 0.20, 5.0, 0.3), "전국(제공 자료)": y.astype(float)}
rows = []
for name, s in regions.items():
    for kind in ("ridge", "hgb"):
        R_ = rolling_origin(s, n_folds=6, fold=24, kind=kind, lags=(1, 2, 3, 12))
        rows.append({"region": name, "model": kind, "mean_RMSE": R_["RMSE"].mean(), "mean_RMSE_naive": R_["RMSE_naive"].mean(),
                     "상대(RMSE/naive)": R_["RMSE"].mean() / R_["RMSE_naive"].mean(), "worst_fold_상대": (R_["RMSE"] / R_["RMSE_naive"]).max()})
tab = pd.DataFrame(rows).set_index(["region", "model"]); show(tab)
print("\n해석: 상대 RMSE<1이면 나이브보다 낫다. 지역에 따라 순위/이득이 바뀌는지, worst_fold에서 무너지는지 본다.")
'''
RE_ROB2 = r'''
# ---- 하이퍼 설정 민감도: 학습 창 길이(전체 vs 최근 W) ----
s0 = regions["전국(제공 자료)"]; rows = []
for win in (None, 60, 120):
    R_ = rolling_origin(s0, n_folds=6, fold=24, kind="ridge", window=win, lags=(1, 2, 3, 12))
    rows.append({"학습 창": "전체(expanding)" if win is None else f"최근 {win}개월", "mean_RMSE": R_["RMSE"].mean()})
show(pd.DataFrame(rows).set_index("학습 창"))
rows = []
for lg in [(1,), (1, 2, 3), (1, 2, 3, 12), (1, 2, 3, 6, 12, 24)]:
    R_ = rolling_origin(s0, n_folds=6, fold=24, kind="ridge", lags=lg); rows.append({"시차 집합": str(lg), "mean_RMSE": R_["RMSE"].mean()})
show(pd.DataFrame(rows).set_index("시차 집합"))
print("해석: 결론(모형 우열)이 창 길이·시차 선택에 뒤집히면 '강건하지 않다'고 보고한다.")
'''

EN_REGIME = r'''
# ---- 체제변화: 평균 이동을 주입한 기온 시계열과 원 시계열 비교 ----
s_all = y.astype(float)
brk = int(len(s_all) * 0.6); s_shift = s_all.copy(); s_shift.iloc[brk:] += 2.0          # 6번째 10분위 이후 평균 +2도(주입)
def sup_f(series, trim=0.15, step=30):
    # 평균 이동에 대한 sup-F(Chow) 스캔. 임계값은 비표준(Andrews)이므로 최댓값과 위치만 보고 "확인용"으로 쓴다.
    v = series.to_numpy(float); n = len(v); best = (0, None)
    for k in range(int(trim * n), int((1 - trim) * n), step):
        a, b = v[:k], v[k:]
        rss1 = np.sum((a - a.mean()) ** 2) + np.sum((b - b.mean()) ** 2); rss0 = np.sum((v - v.mean()) ** 2)
        F = (rss0 - rss1) / (rss1 / (n - 2))
        if F > best[0]: best = (F, k)
    return best
for name, ser in (("원 시계열", s_all), ("평균 이동 주입", s_shift)):
    # 계절성을 제거한 뒤 이동 검정(계절 평균 제거)
    clim = ser.groupby(ser.index.dayofyear).transform("mean"); anom = ser - clim
    F, k = sup_f(anom); print(f"{name}: sup-F={F:.1f}, 추정 이동 위치={ser.index[k].date() if k else None}  (주입 위치 {s_all.index[brk].date()})")
'''
EN_REGIME2 = r'''
# ---- 체제변화 전후 예측 성능 (롤링 오리진, 폴드별) ----
for name, ser in (("원 시계열", s_all), ("평균 이동 주입", s_shift)):
    R_ = rolling_origin(ser, n_folds=8, fold=120, kind="hgb", lags=(1, 2, 3, 7, 14))
    R_["상대"] = R_["RMSE"] / R_["RMSE_naive"]
    print(f"[{name}]"); show(R_[["fold", "end", "RMSE", "RMSE_naive", "상대"]])
print("해석: 체제변화 직후 폴드에서 트리 모형은 학습 범위 밖 값을 예측하지 못해 성능이 급락할 수 있다(외삽 한계). 롤링 학습 창이나 변화점 탐지를 연결해 본다.")
'''

# ---- 제조: 경보 정확도/누수 ----
MFG = r'''
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve
df_m = D["df"].copy(); HOR = 12
fut = pd.concat([df_m["fault"].shift(-k) for k in range(1, HOR + 1)], axis=1).max(axis=1)
target = fut.fillna(0).astype(int)
def feats(s, name, center=False):
    f = pd.DataFrame(index=s.index)
    for w in (6, 12, 24):
        f[f"{name}_mean{w}"] = s.rolling(w, center=center).mean()           # center=True면 미래 값이 섞인다(누수)
        f[f"{name}_std{w}"] = s.rolling(w, center=center).std()
    return f
def build(center):
    X = pd.concat([feats(df_m["vibration"], "vib", center), feats(df_m["temp"], "temp", center)], axis=1)
    d = pd.concat([X, target.rename("t")], axis=1).dropna(); return d.drop(columns="t"), d["t"]
def split_eval(center, shuffle=False):
    X, t = build(center); n_tr = int(len(X) * 0.7)
    if shuffle:                                                             # 누수: 시간을 섞는 무작위 분할
        idx = np.random.default_rng(SEED).permutation(len(X)); tr_i, te_i = idx[:n_tr], idx[n_tr:]
    else:
        tr_i, te_i = np.arange(n_tr), np.arange(n_tr, len(X))
    m = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, random_state=SEED).fit(X.iloc[tr_i], t.iloc[tr_i])
    p = m.predict_proba(X.iloc[te_i])[:, 1]; return average_precision_score(t.iloc[te_i], p), t.iloc[te_i].mean(), p, t.iloc[te_i], X.index[te_i]
rows = []
for label, c_, sh_ in [("정상: 과거 창 + 시간순 분할", False, False), ("누수A: 중심 창(미래 포함)", True, False),
                       ("누수B: 무작위 분할", False, True), ("누수A+B", True, True)]:
    ap, base_rate, *_ = split_eval(c_, sh_); rows.append({"설정": label, "PR_AUC": ap, "양성비율(기준)": base_rate})
show(pd.DataFrame(rows).set_index("설정"))
print("PR-AUC가 정상 설정보다 크게 높은 설정은 누수로 부풀려진 값이다(참 성능이 아님).")
'''
MFG2 = r'''
# ---- 정상 설정에서 경보 품질: 임계값은 학습구간에서만 정하고 선행시간을 계산 ----
X, t = build(False); n_tr = int(len(X) * 0.7)
m = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, random_state=SEED).fit(X.iloc[:n_tr], t.iloc[:n_tr])
p_tr = m.predict_proba(X.iloc[:n_tr])[:, 1]; p_te = m.predict_proba(X.iloc[n_tr:])[:, 1]
prec, rec, thr = precision_recall_curve(t.iloc[:n_tr], p_tr); ok_ = np.where(prec[:-1] >= 0.5)[0]
th = float(thr[ok_[0]]) if len(ok_) else 0.5                         # 학습구간에서 정밀도>=0.5가 되는 최소 임계값
alarm = pd.Series(p_te >= th, index=X.index[n_tr:])
events = df_m.index[(df_m["fault"] == 1) & (df_m.index >= X.index[n_tr])]
lead, caught = [], 0
for ev in events:                                                      # 이벤트 전 12시간 안에 첫 경보까지의 선행시간
    win = alarm.loc[ev - pd.Timedelta(hours=HOR): ev - pd.Timedelta(hours=1)]
    if win.any():
        caught += 1; lead.append((ev - win[win].index[0]).total_seconds() / 3600)
false_alarm_hours = int((alarm & ~(t.loc[alarm.index] == 1)).sum())
print(f"검증구간 고장 {len(events)}건 중 사전 경보 {caught}건 | 평균 선행시간 {np.mean(lead) if lead else float('nan'):.1f}시간 | 오경보 시간 수 {false_alarm_hours} / {len(alarm)}")
print("주의: 이벤트가 매우 적어(수 건) 재현율·선행시간의 불확실성이 크다. 신뢰구간 또는 반복 검증이 필요하다.")
'''

# ---- 공공정책: 위약 ----
POLICY = r'''
# Prop 99(실제) 또는 합성 패널로 SCM 효과와 시점·공간 위약분포를 비교한다.
def parse_prop99(raw):
    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
    df = pd.read_csv(io.StringIO(text), sep=";"); cols = {c.strip().lower(): c for c in df.columns}
    for need in ("state", "year", "packspercapita", "treated"):
        if need not in cols: raise ValueError("예상 열 없음: " + need)
    return df.rename(columns={cols["state"]: "State", cols["year"]: "Year", cols["packspercapita"]: "PacksPerCapita", cols["treated"]: "treated"})

panel, treated, T0, DATA_KIND = None, None, None, None
if USE_LIVE_DATA:
    try:
        df99 = parse_prop99(fetch_bytes("https://raw.githubusercontent.com/synth-inference/synthdid/master/data/california_prop99.csv"))
        wide = df99.pivot(index="Year", columns="State", values="PacksPerCapita").sort_index()
        tr_state = df99.loc[df99["treated"] == 1, "State"].unique().tolist(); first_year = int(df99.loc[df99["treated"] == 1, "Year"].min())
        if wide.isna().any().any() or len(tr_state) != 1: raise ValueError("패널 불균형 또는 처치 단위 != 1")
        panel = wide[tr_state + [c for c in wide.columns if c not in tr_state]]; treated = tr_state
        T0 = int(np.where(panel.index == first_year)[0][0]); DATA_KIND = "REAL: California Prop 99 (synthdid 저장소)"
    except Exception as e:
        print("Prop 99 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:120])
if panel is None:
    panel, treated, T0 = make_panel(N=30, T=31, start="1970-01-01", freq="D", n_treated=1, T0=19, tau=-8.0, seed=SEED)
    panel.index = pd.Index(range(1970, 2001), name="Year"); DATA_KIND = "SYNTHETIC (NOT real data): 요인모형 패널, 주입 효과 tau=-8.0"
print("DATA_KIND:", DATA_KIND, "| 패널:", panel.shape, "| 처치:", treated, "| T0 위치:", T0)

def scm_weights(y1_pre, Y0_pre):
    J = Y0_pre.shape[1]; f = lambda w: np.sum((y1_pre - Y0_pre @ w) ** 2)
    return optimize.minimize(f, np.full(J, 1 / J), method="SLSQP", bounds=[(0, 1)] * J,
                             constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}], options={"maxiter": 300, "ftol": 1e-10}).x
def scm_effect(P, unit, donors, t0):
    y1 = P[unit].to_numpy(float); Y0 = P[donors].to_numpy(float); w = scm_weights(y1[:t0], Y0[:t0]); gap = y1 - Y0 @ w
    return gap[t0:].mean(), np.sqrt(np.mean(gap[:t0] ** 2)), np.sqrt(np.mean(gap[t0:] ** 2))
unit1 = treated[0]; donors = [c for c in panel.columns if c not in treated]
eff, rp, rq = scm_effect(panel, unit1, donors, T0)
print(f"SCM 사후 평균 효과 = {eff:.3f} | 사전 RMSPE = {rp:.3f}")
'''
POLICY2 = r'''
# ---- 공간 위약: 각 도너를 가짜 처치로 ----
plac = []
for d_ in donors:
    e_, a_, b_ = scm_effect(panel, d_, [c for c in donors if c != d_], T0); plac.append((d_, e_, a_, b_))
P = pd.DataFrame(plac, columns=["unit", "effect", "rmspe_pre", "rmspe_post"]); P["ratio"] = P["rmspe_post"] / P["rmspe_pre"].clip(lower=1e-9)
ratio_t = rq / max(rp, 1e-9)
p_space = (1 + int((P["ratio"] >= ratio_t).sum())) / (1 + len(P))
print(f"[공간 위약] 처치 비율={ratio_t:.2f}, 위약 중앙값={P['ratio'].median():.2f}, 순열 p={p_space:.3f} (최소 가능 p={1/(1+len(P)):.3f})")
good = P[P["rmspe_pre"] <= 2 * max(rp, 1e-9)]
print(f"사전 적합이 나쁜 도너(사전 RMSPE>2배)를 제외하면 위약 {len(good)}개, p={(1 + int((good['ratio'] >= ratio_t).sum())) / (1 + len(good)):.3f}")
# ---- 시간 위약: 처치 이전 기간 안에서 가짜 개입 시점 ----
rows = []
for fake in range(max(8, T0 // 3), T0 - 2):
    e_, a_, b_ = scm_effect(panel.iloc[:T0], unit1, donors, fake); rows.append({"가짜 T0": panel.index[fake], "효과": e_})
Tp = pd.DataFrame(rows).set_index("가짜 T0"); show(Tp)
print(f"실제 효과 {eff:.2f} vs 시간 위약 효과 범위 [{Tp['효과'].min():.2f}, {Tp['효과'].max():.2f}]  -> 실제 효과가 위약 범위 밖이어야 설득력이 있다")
'''
PLACEBO_FIG = r'''
fig, ax = plt.subplots(figsize=(8, 3.6)); ax.hist(P["effect"], bins=15, alpha=0.6, label="공간 위약 효과"); ax.axvline(eff, color="C3", lw=2, label="처치 단위"); ax.legend()
ax.set_title("효과 추정치의 위약 분포"); plt.show()
'''

# ---- 경영: 프로모션 누수 ----
BIZ = r'''
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
df_s = D["df"].copy() if "df" in D else None
if df_s is None:
    # 실제 자료에는 프로모션 표지가 없다 -> 누수 시연은 합성 자료로 수행한다
    ns_ = {}
    df_s = synthetic_sales(); DATA_KIND = "SYNTHETIC (NOT real data): 프로모션 표지가 있는 합성 매출 (누수 시연용)"
sales, promo = df_s["sales"].astype(float), df_s["promo"].astype(float)
dow = pd.get_dummies(sales.index.dayofweek, prefix="dow", dtype=float); dow.index = sales.index
def X_base():
    return pd.concat([pd.DataFrame({f"lag_{k}": sales.shift(k) for k in (1, 7, 14)}), dow, promo.rename("promo_today")], axis=1)
def evaluate(X, label, shuffle=False):
    d = pd.concat([X, sales.rename("t")], axis=1).dropna(); n_tr = int(len(d) * 0.75)
    idx = np.random.default_rng(SEED).permutation(len(d)) if shuffle else np.arange(len(d))
    tr, te = idx[:n_tr], idx[n_tr:]
    m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.06, random_state=SEED).fit(d.drop(columns="t").iloc[tr], d["t"].iloc[tr])
    return {"설정": label, "RMSE": rmse(d["t"].iloc[te], m.predict(d.drop(columns="t").iloc[te]))}
rows = [evaluate(X_base(), "정상: 오늘 프로모션(사전 계획) + 과거 판매")]
Xl = X_base(); Xl["promo_effect_proxy"] = sales.shift(-1) - sales               # 누수: 내일 판매와의 차이(미래 정보)
rows.append(evaluate(Xl, "누수1: 미래 판매가 들어간 파생변수"))
Xl2 = X_base(); Xl2["promo_next7_mean_sales"] = sales.shift(-1).rolling(7).mean()   # 누수: 프로모션 이후 판매 평균(사후 결과)
rows.append(evaluate(Xl2, "누수2: 프로모션 이후 판매 평균(사후 변수)"))
rows.append(evaluate(X_base(), "누수3: 무작위 분할", shuffle=True))
show(pd.DataFrame(rows).set_index("설정"))
print("RMSE가 정상 설정보다 크게 낮은 설정은 누수다. 프로모션 변수는 '예측 시점에 알려진 계획'일 때만 합법적 특성이다.")
'''
BIZ2 = r'''
# 프로모션 정보가 실제로 도움이 되는지(정직한 평가): 시간순 walk-forward, 프로모션 포함/제외 비교
def wf(X, n_folds=6, fold=60):
    d = pd.concat([X, sales.rename("t")], axis=1).dropna(); n = len(d); start = n - n_folds * fold; out = []
    for k in range(n_folds):
        a, b = start + k * fold, start + (k + 1) * fold
        m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.06, random_state=SEED).fit(d.drop(columns="t").iloc[:a], d["t"].iloc[:a])
        out.append(rmse(d["t"].iloc[a:b], m.predict(d.drop(columns="t").iloc[a:b])))
    return np.array(out)
w_with, w_wo = wf(X_base()), wf(X_base().drop(columns="promo_today"))
print("Walk-forward RMSE | 프로모션 포함:", w_with.round(1), "평균", round(w_with.mean(), 1))
print("Walk-forward RMSE | 프로모션 제외:", w_wo.round(1), "평균", round(w_wo.mean(), 1))
'''

INTERP = r'''
## 3. 결과 해석 작성
1. 정상 설정과 누수 설정의 성능 차이를 표로 제시하고, **어떤 누수 경로가 가장 큰 왜곡을 만들었는지** 설명한다.
2. 폴드(또는 지역·기간) 간 변동을 보고 "평균은 좋지만 최악의 경우가 나쁘다"를 구분한다.
3. 결론(모형 우열, 효과 방향)이 설정 변경에도 유지되는가? 유지되지 않으면 "강건하다"가 아니라 "민감하다"로 쓴다.
4. 한계: 폴드 수, 이벤트 수, 합성자료의 한계, 위약검정이 모든 식별 가정을 증명하지는 않는다는 점.

**제출:** 정상/누수 비교표, 폴드별 결과, 강건성 표, 한계 단락. 누수 점검 목록(`validation/Leakage_Checklist.md`)과 대조하라.
'''

def build(domain, title, question):
    head = [md(f"# Chapter 7 · {title}\n\n**연구질문:** {question}\n\n> 위에서 아래로 실행하면 끝까지 동작합니다."), md(THEORY_WF), code(SETUP)]
    ld = lambda w: code(LOADERS[domain].replace("@@WHICH@@", w).replace("@@FORCE@@", "True" if domain == "BusinessMarketing" else "False"))
    if domain == "Finance":
        return head + [ld(""), md("## 2. Walk-forward 평가"), code(WF_CORE), code(WF_FIN), md("## 3. 누수 실험"), code(LEAK_FIN), md(INTERP)]
    if domain == "RealEstate":
        return head + [ld("price"), md("## 2. 지역·기간 강건성"), code(SUBSAMPLE), code(RE_ROB), md("## 3. 설정 민감도"), code(RE_ROB2), md(INTERP)]
    if domain == "Manufacturing":
        return head + [ld("sensor"), md("## 2. 누수 실험"), code(MFG), md("## 3. 경보 품질"), code(MFG2), md(INTERP)]
    if domain == "PublicPolicy":
        return head + [code(PANEL_TOOLS), md("## 2. 데이터와 SCM 효과"), code(POLICY), md("## 3. 시점·공간 위약"), code(POLICY2), code(PLACEBO_FIG), md(INTERP)]
    if domain == "EnergyEnvironment":
        return head + [ld("temp"), md("## 2. 체제변화 탐지와 예측 성능"), code(SUBSAMPLE), code(EN_REGIME), code(EN_REGIME2), md(INTERP)]
    return head + [ld(""), md("## 2. 프로모션 누수"), code(BIZ), md("## 3. 프로모션 정보의 실제 가치"), code(BIZ2), md(INTERP)]

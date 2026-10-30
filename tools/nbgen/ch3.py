from .cells import md, code
from .common import SETUP
from .data_cells import LOADERS

WHICH = {"Finance": "", "RealEstate": "price", "Manufacturing": "sensor", "PublicPolicy": "traffic",
         "EnergyEnvironment": "demand", "BusinessMarketing": ""}

THEORY = r'''
## 1. 핵심 개념·수식

**지도학습 형태의 예측:** $\hat y_{t}=f(y_{t-1},\dots,y_{t-L},\ \text{rolling}_{t-1},\ \text{calendar}_t,\ x_t)$. 모든 특성은 **예측 시점 $t$에 알 수 있는 정보**만 사용한다(롤링 통계는 반드시 한 칸 이동).

**시간순 검증:** 무작위 분할 대신 훈련 구간이 항상 검증 구간보다 앞서는 expanding-window 분할을 쓴다.

**기준선 대비 성능:** $\mathrm{MASE}<1$이면 1단계 나이브보다 낫다. 수익률처럼 예측력이 약한 자료는 **표본 외 $R^2_{OS}=1-\dfrac{\sum(y_t-\hat y_t)^2}{\sum(y_t-\bar y_{t-1})^2}$** ($\bar y_{t-1}$: 직전까지의 평균)로 평가한다.

**변수 중요도:** 순열 중요도는 특성을 섞었을 때 검증 오차가 늘어난 정도이며 인과적 중요도가 아니다. 상관된 특성이 있으면 해석이 불안정하다.
'''

CORE = r'''
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import (RandomForestRegressor, HistGradientBoostingRegressor,
                              RandomForestClassifier, HistGradientBoostingClassifier)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve

def calendar_features(idx, freq):
    out = pd.DataFrame(index=idx)
    if freq in ("D", "B", "h"):
        out["dow"] = idx.dayofweek
    if freq == "h":
        out["hour"] = idx.hour
    out["month_sin"] = np.sin(2 * np.pi * idx.month / 12); out["month_cos"] = np.cos(2 * np.pi * idx.month / 12)
    return out

def lag_features(s, lags, rolls=()):
    X = pd.DataFrame({f"lag_{k}": s.shift(k) for k in lags})
    for w in rolls:
        X[f"rmean_{w}"] = s.shift(1).rolling(w).mean()          # shift(1): 현재 값을 쓰지 않는다(누수 방지)
        X[f"rstd_{w}"] = s.shift(1).rolling(w).std()
    return X

def get_models():
    models = {
        "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "RandomForest": RandomForestRegressor(n_estimators=150, min_samples_leaf=5, max_features=0.6, n_jobs=-1, random_state=SEED),
        "HistGB": HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, random_state=SEED),
    }
    if ensure("xgboost"):                                         # 선택: 설치돼 있으면 XGBoost도 비교
        from xgboost import XGBRegressor
        models["XGBoost"] = XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8,
                                         random_state=SEED, n_jobs=-1, verbosity=0)
    return models

def fit_eval(X, target, n_test, models=None):
    # 앞쪽으로 학습, 마지막 n_test 관측으로 평가 (1단계 예측, 시차 입력은 실제값)
    data = pd.concat([X, target.rename("target")], axis=1).dropna()
    tr, te = data.iloc[:-n_test], data.iloc[-n_test:]
    Xtr, ytr, Xte, yte = tr.drop(columns="target"), tr["target"], te.drop(columns="target"), te["target"]
    models = models or get_models(); preds = {}
    for name, mdl in models.items():
        mdl.fit(Xtr, ytr); preds[name] = pd.Series(mdl.predict(Xte), index=te.index)
    return dict(Xtr=Xtr, ytr=ytr, Xte=Xte, yte=yte, preds=preds, models=models, data=data)

def cv_rmse(X, target, models, n_splits=4, test_size=None):
    data = pd.concat([X, target.rename("target")], axis=1).dropna()
    test_size = test_size or max(30, len(data) // 10)
    tss = TimeSeriesSplit(n_splits=n_splits, test_size=test_size); out = {k: [] for k in models}
    from sklearn.base import clone
    for tr_i, te_i in tss.split(data):
        a, b = data.iloc[tr_i], data.iloc[te_i]
        for name, mdl in models.items():
            m_ = clone(mdl).fit(a.drop(columns="target"), a["target"])
            out[name].append(rmse(b["target"], m_.predict(b.drop(columns="target"))))
    return pd.DataFrame(out).agg(["mean", "std"]).T.rename(columns={"mean": "CV_RMSE_mean", "std": "CV_RMSE_sd"})
'''

REG_REPORT = r'''
# 결과표: 기준선과 모델, 마지막 구간 평가 + 시간순 CV
def report(res, baselines, train_for_scale):
    rows = {}
    for name, f in {**baselines, **res["preds"]}.items():
        rows[name] = {"MAE": mae(res["yte"], f), "RMSE": rmse(res["yte"], f),
                      "MASE": mase(res["yte"], f, train_for_scale, m=1)}
    tab = pd.DataFrame(rows).T.sort_values("RMSE"); show(tab); return tab
'''

# --------- 도메인별 ---------
FIN = r'''
rr = ret.astype(float)
X = pd.concat([lag_features(rr, [1, 2, 3, 4, 5], rolls=(5, 21)),
               lag_features(rr.abs(), [1, 2, 3]).add_prefix("abs_"),
               calendar_features(rr.index, "B")[["dow"]]], axis=1)
n_test = 500
res = fit_eval(X, rr, n_test)
yte = res["yte"]
hist_mean = rr.expanding().mean().shift(1).loc[yte.index]            # 직전까지의 평균 (기준선)
base = {"hist_mean": hist_mean, "zero": pd.Series(0.0, index=yte.index)}
tab = report(res, base, res["ytr"].to_numpy())
print("\n표본 외 R²(역사평균 대비), 방향 적중률(부호 일치; 기준은 \"항상 상승\"의 적중률)")
sse_b = float(np.sum((yte - hist_mean) ** 2)); rows = []
for name, f in res["preds"].items():
    r2 = 1 - float(np.sum((yte - f) ** 2)) / sse_b
    hit = float(np.mean(np.sign(f) == np.sign(yte)))
    p0 = float(np.mean(yte > 0))                          # "항상 상승" 예측의 적중률(양의 평균 수익률이면 0.5보다 큼)
    pv = stats.binomtest(int(np.sum(np.sign(f) == np.sign(yte))), len(yte), p0).pvalue
    rows.append({"model": name, "R2_OS": r2, "hit_rate": hit, "always_up_hit": p0, "binom_p(vs always_up)": pv})
show(pd.DataFrame(rows).set_index("model"))
print("\n시간순 CV (RMSE):"); show(cv_rmse(X, rr, get_models(), n_splits=4, test_size=250))
'''

FIN_NOTE = r'''
**읽는 법:** 수익률은 신호 대 잡음비가 매우 낮아, 정직하게 평가하면 $R^2_{OS}$가 0 근처이거나 음수인 것이 흔한 결과다. $R^2_{OS}>0$이어도 (i) 단일 구간, (ii) 거래비용·위험조정 없이는 경제적 유의성을 주장할 수 없고, (iii) DM 검정·반복 구간에서의 안정성을 확인해야 한다(Ch.7).
'''

RE = r'''
g = np.log(y).diff() * 100                                           # 월 성장률(%)
cal = calendar_features(g.index, "MS")[["month_sin", "month_cos"]]
X = pd.concat([lag_features(g, list(range(1, 13)), rolls=(3, 12)), cal], axis=1)
n_test = 48
res = fit_eval(X, g, n_test)
yte = res["yte"]
base = {"naive(lag1)": g.shift(1).loc[yte.index], "seasonal naive(lag12)": g.shift(12).loc[yte.index]}
tab = report(res, base, res["ytr"].to_numpy())
print("\n시간순 CV (RMSE):"); show(cv_rmse(X, g, get_models(), n_splits=4, test_size=36))
'''

RE_NOTE = r'''
**읽는 법:** 가격 **수준**을 예측하면 지수가 느리게 움직여 나이브도 매우 정확해 보인다. 그래서 여기서는 **증가율**을 예측 대상으로 삼았다. 지수는 평활·개정 절차를 거친 자료일 수 있어 자기상관이 인위적으로 클 수 있다(확인 필요).
'''

TRAFFIC = r'''
df_t = D["df"]; s = df_t["traffic"]
X = pd.concat([lag_features(s, [1, 2, 3, 24, 48, 168], rolls=(24,)), calendar_features(s.index, "h"),
               df_t[["temp", "rain"]]], axis=1)      # 기온·강수는 예보로 사전에 알 수 있다고 가정
n_test = 24 * 60
res = fit_eval(X, s, n_test)
yte = res["yte"]
base = {"naive(lag1)": s.shift(1).loc[yte.index], "seasonal naive(lag168)": s.shift(168).loc[yte.index]}
tab = report(res, base, res["ytr"].to_numpy())
print("\n시간순 CV (RMSE):"); show(cv_rmse(X, s, get_models(), n_splits=3, test_size=24 * 30))
best = tab.drop(index=list(base), errors="ignore").index[0]
pi = permutation_importance(res["models"][best], res["Xte"], yte, n_repeats=3, random_state=SEED,
                            scoring="neg_root_mean_squared_error")
imp = pd.Series(pi.importances_mean, index=res["Xte"].columns).sort_values(ascending=False)
print(f"\n순열 중요도(상위, 모델={best}):"); show(imp.head(8).to_frame("RMSE 증가량"))
'''

TRAFFIC_NOTE = r'''
**읽는 법:** 자료는 합성이며 생성식(출퇴근 피크·주말·강수)을 우리가 알고 있다. 따라서 모델이 `lag_168`, `hour`, `dow`를 중요하게 보는지는 **생성 구조를 되찾는지**의 점검이다. 실제 교통량으로 바꾸면 결과가 달라질 수 있다.
'''

SALES = r'''
df_s = D.get("df")
s = y.astype(float)
parts = [lag_features(s, [1, 7, 14, 28], rolls=(7, 28)), calendar_features(s.index, "D")]
if df_s is not None and "promo" in df_s:
    parts.append(df_s[["promo"]])                   # 프로모션은 사전 계획되어 알려져 있다고 가정(합성자료)
else:
    print("프로모션 변수가 없는 실제 자료입니다 -> 요일·계절·시차만 사용합니다.")
X = pd.concat(parts, axis=1)
n_test = 120
res = fit_eval(X, s, n_test)
yte = res["yte"]
base = {"naive(lag1)": s.shift(1).loc[yte.index], "seasonal naive(lag7)": s.shift(7).loc[yte.index]}
tab = report(res, base, res["ytr"].to_numpy())
print("\n시간순 CV (RMSE):"); show(cv_rmse(X, s, get_models(), n_splits=4, test_size=60))
best = tab.drop(index=list(base), errors="ignore").index[0]
pi = permutation_importance(res["models"][best], res["Xte"], yte, n_repeats=5, random_state=SEED,
                            scoring="neg_root_mean_squared_error")
show(pd.Series(pi.importances_mean, index=res["Xte"].columns).sort_values(ascending=False).head(8).to_frame("RMSE 증가량"))
'''

ENERGY_FEATS = r'''
s = y.astype(float); temp = D["X"]["temp"]
X = pd.concat([lag_features(s, [1, 2, 7, 14], rolls=(7,)), calendar_features(s.index, "D"), temp.to_frame("temp")], axis=1)
n_test = 365
res = fit_eval(X, s, n_test)
yte = res["yte"]
base = {"naive(lag1)": s.shift(1).loc[yte.index], "seasonal naive(lag7)": s.shift(7).loc[yte.index]}
tab = report(res, base, res["ytr"].to_numpy())
'''

LSTM = r'''
# LSTM: 최근 W일의 [수요, 기온]을 입력으로 다음 날 수요를 예측. torch가 없으면 MLP로 대체(표시).
W = 14
HAS_TORCH = ensure("torch")
arr = np.column_stack([s.to_numpy(float), temp.to_numpy(float)])
n_tr = len(arr) - n_test
mu_, sd_ = arr[:n_tr].mean(axis=0), arr[:n_tr].std(axis=0)          # 스케일은 학습구간 통계만 사용(누수 방지)
Z = (arr - mu_) / sd_
Xw = np.stack([Z[i - W:i] for i in range(W, len(Z))]); yw = Z[W:, 0]
cut = n_tr - W                                                       # 학습 윈도우의 마지막 인덱스
if HAS_TORCH:
    import torch, torch.nn as nn
    torch.manual_seed(SEED)
    class LSTMReg(nn.Module):
        def __init__(self, n_in, hid=32):
            super().__init__(); self.lstm = nn.LSTM(n_in, hid, batch_first=True); self.fc = nn.Linear(hid, 1)
        def forward(self, x):
            o, _ = self.lstm(x); return self.fc(o[:, -1, :]).squeeze(-1)
    net = LSTMReg(Xw.shape[2]); opt = torch.optim.Adam(net.parameters(), lr=1e-2); lossf = nn.MSELoss()
    Xt = torch.tensor(Xw[:cut], dtype=torch.float32); yt = torch.tensor(yw[:cut], dtype=torch.float32)
    for epoch in range(25):
        net.train(); perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 64):
            b = perm[i:i + 64]; opt.zero_grad(); loss = lossf(net(Xt[b]), yt[b]); loss.backward(); opt.step()
    net.eval()
    with torch.no_grad():
        p_te = net(torch.tensor(Xw[cut:], dtype=torch.float32)).numpy()
    kind_nn = "LSTM(torch)"
else:
    from sklearn.neural_network import MLPRegressor
    mlp = MLPRegressor(hidden_layer_sizes=(32,), max_iter=300, random_state=SEED).fit(Xw[:cut].reshape(cut, -1), yw[:cut])
    p_te = mlp.predict(Xw[cut:].reshape(len(Xw) - cut, -1)); kind_nn = "MLP(torch 없음: LSTM 대체)"
p_te = p_te * sd_[0] + mu_[0]                                        # 원척도 복원
y_true = s.to_numpy()[n_tr:]
print(f"{kind_nn}: RMSE={rmse(y_true, p_te):.3f}  MAE={mae(y_true, p_te):.3f}")
tab.loc[kind_nn] = {"MAE": mae(y_true, p_te), "RMSE": rmse(y_true, p_te), "MASE": mase(y_true, p_te, res["ytr"].to_numpy(), m=1)}
show(tab.sort_values("RMSE"))
'''

ENERGY_NOTE = r'''
**읽는 법:** 수요는 기온의 비선형(U자) 함수로 합성했다. 선형모형이 놓치는 비선형을 트리·신경망이 잡는지가 비교 포인트이며, 자료가 작고 구조가 단순해 신경망의 이점이 작게 나올 수 있다. 신경망은 초기값·epoch에 민감하므로 여러 시드로 반복한 뒤 결론을 내려야 한다.
'''

# ---- 제조: 분류 ----
MFG = r'''
df_m = D["df"].copy(); HOR = 12                                       # 향후 12시간 내 고장 여부
fut = pd.concat([df_m["fault"].shift(-k) for k in range(1, HOR + 1)], axis=1).max(axis=1)
target = fut.fillna(0).astype(int).rename("fault_next12")
def roll_feats(s, name):
    f = pd.DataFrame(index=s.index)
    for w in (6, 12, 24):
        f[f"{name}_mean{w}"] = s.rolling(w).mean()             # 현재 시점까지의 과거 창만 사용
        f[f"{name}_std{w}"] = s.rolling(w).std()
    f[f"{name}_slope12"] = (s - s.shift(12)) / 12
    return f
X = pd.concat([roll_feats(df_m["vibration"], "vib"), roll_feats(df_m["temp"], "temp")], axis=1)
data = pd.concat([X, target], axis=1).dropna()
n_tr = int(len(data) * 0.7)
tr, te = data.iloc[:n_tr], data.iloc[n_tr:]
Xtr, ytr, Xte, yte = tr.drop(columns="fault_next12"), tr["fault_next12"], te.drop(columns="fault_next12"), te["fault_next12"]
print(f"학습 {len(tr)}시간(양성 비율 {ytr.mean():.3f}) | 검증 {len(te)}시간(양성 비율 {yte.mean():.3f})")
print("검증구간 고장 이벤트 수(참고):", int(D['df'].loc[te.index, 'fault'].sum()), "-> 이벤트가 적으면 지표가 불안정")
clfs = {
    "Logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced")),
    "RandomForest": RandomForestClassifier(n_estimators=200, min_samples_leaf=5, class_weight="balanced", n_jobs=-1, random_state=SEED),
    "HistGB": HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=SEED),
}
rows, probs = [], {}
for name, c in clfs.items():
    c.fit(Xtr, ytr); p = c.predict_proba(Xte)[:, 1]; probs[name] = p
    rows.append({"model": name, "ROC_AUC": roc_auc_score(yte, p), "PR_AUC": average_precision_score(yte, p)})
rows.append({"model": "무작위(PR-AUC=양성비율)", "ROC_AUC": 0.5, "PR_AUC": float(yte.mean())})
show(pd.DataFrame(rows).set_index("model"))
'''
MFG2 = r'''
# 임계값은 학습구간에서만 정하고(재현율 80% 목표) 검증구간에 그대로 적용한다
best_name = max(probs, key=lambda k: average_precision_score(yte, probs[k]))
p_tr = clfs[best_name].predict_proba(Xtr)[:, 1]
prec, rec, thr = precision_recall_curve(ytr, p_tr)
ok = np.where(rec[:-1] >= 0.8)[0]; th = thr[ok[-1]] if len(ok) else 0.5
pred = (probs[best_name] >= th).astype(int)
tp = int(((pred == 1) & (yte.to_numpy() == 1)).sum()); fp = int(((pred == 1) & (yte.to_numpy() == 0)).sum())
fn = int(((pred == 0) & (yte.to_numpy() == 1)).sum())
print(f"모델={best_name} | 임계값(학습구간 기준)={th:.3f} | TP={tp} FP={fp} FN={fn} | "
      f"정밀도={tp/max(tp+fp,1):.3f} 재현율={tp/max(tp+fn,1):.3f}")
imp = pd.Series(permutation_importance(clfs[best_name], Xte, yte, n_repeats=3, random_state=SEED,
                scoring="average_precision").importances_mean, index=Xte.columns).sort_values(ascending=False)
show(imp.head(6).to_frame("PR-AUC 감소량"))
'''
MFG_NOTE = r'''
**읽는 법:** 합성 센서에는 고장 직전 12시간의 전조가 **심어져 있으므로** 높은 성능은 방법이 작동한다는 점검일 뿐이며 현장 성능이 아니다. 실제 설비 자료로는 (i) 고장 라벨의 시점 정의, (ii) 이벤트 수, (iii) 경보 후 조치 비용이 평가를 좌우한다. 평가 누수는 Ch.7에서 다룬다.
'''

NOTES = {"Finance": FIN_NOTE, "RealEstate": RE_NOTE, "PublicPolicy": TRAFFIC_NOTE, "EnergyEnvironment": ENERGY_NOTE,
         "Manufacturing": MFG_NOTE, "BusinessMarketing": "**읽는 법:** 프로모션 변수는 사전에 알려져 있다고 가정했다. 실제로 프로모션 일정이 사후에 정해지거나 판매에 반응해 바뀌면 이 가정이 깨진다(Ch.7 누수)."}

INTERP = r'''
## 3. 결과 해석 작성
1. 기준선(나이브·계절 나이브·역사평균)보다 나은 모델이 있는가? 개선폭은 CV 변동성($sd$) 대비 큰가?
2. 변수 중요도가 도메인 지식과 일관되는가? (인과적 해석 금지)
3. 가장 위험한 누수 경로 3개를 적고, 이 노트북에서 어떻게 막았는지(롤링 shift, 학습구간 통계 스케일, 시간순 분할)를 서술한다.
4. `DATA_KIND`가 합성이면 결과는 **방법 점검**이다. 실제 자료로 바꿨을 때 달라질 점을 적는다.

**제출:** 결과표(기준선 포함), CV 표, 중요도 그래프/표, 해석 단락, 한계.
'''

def build(domain, title, question):
    head = [md(f"# Chapter 3 · {title}\n\n**연구질문:** {question}\n\n> 위에서 아래로 실행하면 끝까지 동작합니다. 온라인 실패 시 합성 대체(`DATA_KIND` 표시)."),
            md(THEORY), code(SETUP),
            code(LOADERS[domain].replace("@@WHICH@@", WHICH[domain]).replace("@@FORCE@@", "False")),
            md("## 2. 특성 구성·모형·평가"), code(CORE), code(REG_REPORT)]
    body = {"Finance": [code(FIN)], "RealEstate": [code(RE)], "PublicPolicy": [code(TRAFFIC)],
            "BusinessMarketing": [code(SALES)], "EnergyEnvironment": [code(ENERGY_FEATS), md("## 3. LSTM"), code(LSTM)],
            "Manufacturing": [code(MFG), code(MFG2)]}[domain]
    return head + body + [md(NOTES[domain]), md(INTERP)]

# 모든 노트북 셀에 들어가는 공통 코드 문자열 (노트북은 Colab에서 단독 실행되어야 하므로 복사해 넣는다).

SETUP = r'''
import os, io, json, subprocess, sys, warnings, urllib.request, urllib.parse
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from scipy import stats, optimize

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
SEED = 42
# 네트워크 없이 합성자료로만 실행하려면 환경변수 TSLAB_OFFLINE=1 로 실행하거나 아래를 False로 바꾼다.
USE_LIVE_DATA = os.environ.get("TSLAB_OFFLINE") != "1"
plt.rcParams.update({"figure.figsize": (10, 4), "axes.grid": True,
                     "axes.spines.top": False, "axes.spines.right": False})

def ensure(pkg, mod=None):
    # 없으면 설치를 시도한다. 실패해도 노트북은 계속 실행되고 해당 선택 기능만 건너뛴다.
    try:
        __import__(mod or pkg); return True
    except Exception:
        if not USE_LIVE_DATA:
            return False
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True, timeout=300)
            __import__(mod or pkg); return True
        except Exception as e:
            print(f"[건너뜀] {pkg} 설치/가져오기 실패: {type(e).__name__}")
            return False

def fetch_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "ts-lab-course/1.0 (education)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

# ---- 평가 지표와 기준선 ----
def mae(a, f):  return float(np.mean(np.abs(np.asarray(a, float) - np.asarray(f, float))))
def rmse(a, f): return float(np.sqrt(np.mean((np.asarray(a, float) - np.asarray(f, float)) ** 2)))
def mase(a, f, train, m=1):
    train = np.asarray(train, float)
    scale = np.mean(np.abs(train[m:] - train[:-m]))
    return mae(a, f) / scale
def naive_fc(train, h):  return np.repeat(np.asarray(train, float)[-1], h)
def snaive_fc(train, h, m):
    train = np.asarray(train, float)
    return np.tile(train[-m:], int(np.ceil(h / m)))[:h]
def drift_fc(train, h):
    train = np.asarray(train, float)
    slope = (train[-1] - train[0]) / (len(train) - 1)
    return train[-1] + slope * np.arange(1, h + 1)
def show(df, digits=4):
    print(df.round(digits).to_string())
'''

PANEL_TOOLS = r'''
# ---- 패널·인과추론용 최소제곱과 로버스트 표준오차 (수식이 코드에 그대로 보이도록 직접 구현) ----
def ols(y, X, names=None, cov="HC1", groups=None, maxlags=None):
    y = np.asarray(y, float).reshape(-1); X = np.asarray(X, float)
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    if cov == "nonrobust":
        V = XtX_inv * (e @ e) / (n - k)
    elif cov == "HC1":
        V = XtX_inv @ (X.T * e ** 2 @ X) @ XtX_inv * n / (n - k)
    elif cov == "HAC":                                   # Newey-West, Bartlett 커널
        L = maxlags if maxlags is not None else int(np.floor(4 * (n / 100) ** (2 / 9)))
        Xe = X * e[:, None]
        S = Xe.T @ Xe
        for l in range(1, L + 1):
            G = Xe[l:].T @ Xe[:-l]
            S += (1 - l / (L + 1)) * (G + G.T)
        V = XtX_inv @ S @ XtX_inv * n / (n - k)
    elif cov == "cluster":                               # 군집 로버스트 (소표본 보정 포함)
        g = pd.factorize(np.asarray(groups))[0]; G = g.max() + 1
        S = np.zeros((k, k))
        for j in range(G):
            s = (X[g == j] * e[g == j][:, None]).sum(axis=0)
            S += np.outer(s, s)
        V = XtX_inv @ S @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    else:
        raise ValueError(cov)
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    t = b / np.where(se > 0, se, np.nan)
    dof = (len(np.unique(groups)) - 1) if cov == "cluster" else (n - k)
    p = 2 * (1 - stats.t.cdf(np.abs(t), dof))
    names = names or [f"x{i}" for i in range(k)]
    return {"beta": b, "se": se, "t": t, "p": p, "resid": e, "V": V, "names": list(names), "n": n,
            "table": pd.DataFrame({"coef": b, "se": se, "t": t, "p": p}, index=names)}

def make_panel(N=24, T=48, start="2018-01-01", freq="MS", n_treated=3, T0=30, tau=-8.0, seed=SEED,
               effect_shape="step", parallel=False):
    # NOT real data: 요인모형 패널. 처치효과 tau를 알고 있으므로 추정기가 이를 회복하는지 확인할 수 있다.
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=T, freq=freq)
    f1 = np.cumsum(rng.normal(0, 0.5, T)); f2 = np.sin(np.arange(T) * 2 * np.pi / 12)
    lam1 = rng.normal(1, 0.3, N); lam2 = rng.normal(0, 1, N); alpha = rng.normal(50, 8, N)
    if parallel:                                   # 모든 단위가 같은 공통추세만 가짐 -> 평행추세가 성립하는 설계
        lam1 = np.ones(N); lam2 = np.zeros(N)
    Y = alpha[:, None] + lam1[:, None] * f1[None] + 2 * lam2[:, None] * f2[None] + rng.normal(0, 1.0, (N, T))
    treated = list(range(n_treated))
    for i in treated:
        post = np.arange(T) >= T0
        ramp = np.clip((np.arange(T) - T0 + 1) / 6, 0, 1) if effect_shape == "ramp" else 1.0
        Y[i] += tau * post * ramp
    df = pd.DataFrame(Y.T, index=dates, columns=[f"U{i:02d}" for i in range(N)])
    return df, [f"U{i:02d}" for i in treated], T0
'''

# 정수 이상의 설명용 pandas 별칭 주의: 'M','H','Q','Y' 대신 'MS','D','B','W' 사용 (pandas 2.2/3.x 호환)

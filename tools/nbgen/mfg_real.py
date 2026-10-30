"""제조 도메인 실데이터(작은 공개 자료) 로더 코드 조각. data_sources/03 과 Ch3 제조 노트북이 공유한다.
노트북 셀에 그대로 들어가는 문자열이며, 모든 로더는 온라인 -> 검증 -> 합성 대체 순서다.
UCI 로드는 ucimlrepo(pip) 우선, 실패 시 static zip 경로(미검증 패턴, 확인 필요)를 시도한다."""

AI4I_CODE = r'''
import zipfile
AI4I_COLS = ["type", "air_temperature", "process_temperature", "rotational_speed", "torque", "tool_wear", "machine_failure"]
AI4I_MODES = ["twf", "hdf", "pwf", "osf", "rnf"]            # 고장 유형 열: 'machine_failure'를 거의 결정 -> 특성으로 쓰면 누수

def _norm_cols(df):
    out = df.copy()
    out.columns = [pd.Series(str(c)).str.replace(r"\[.*?\]", "", regex=True).str.strip().str.lower().str.replace(r"\s+", "_", regex=True).iloc[0]
                   for c in out.columns]
    return out

def parse_ai4i(df):
    d = _norm_cols(df)
    missing = [c for c in AI4I_COLS if c not in d.columns]
    if missing:
        raise ValueError("AI4I 예상 열 없음: " + ", ".join(missing))
    d = d[AI4I_COLS + [c for c in AI4I_MODES if c in d.columns]].copy()
    d["machine_failure"] = pd.to_numeric(d["machine_failure"]).astype(int)
    if len(d) < 5000 or not d["machine_failure"].isin([0, 1]).all():
        raise ValueError("AI4I 길이/라벨 이상")
    return d.reset_index(drop=True)

def synthetic_ai4i(n=10000, seed=2026101):
    """NOT real data: AI4I와 같은 열 구성의 합성 표. 고장은 규칙으로 생성(실제 현상 아님)."""
    rng = np.random.default_rng(seed)
    typ = rng.choice(["L", "M", "H"], n, p=[0.6, 0.3, 0.1])
    air = rng.normal(300, 2, n); proc = air + 10 + rng.normal(0, 1, n)
    rpm = rng.normal(1540, 170, n).clip(1100, 2900); torque = rng.normal(40, 6, n).clip(3, 80)
    wear = rng.integers(0, 250, n).astype(float)
    hdf = ((proc - air) < 8.6) & (rpm < 1380)
    power = torque * rpm * 2 * np.pi / 60
    pwf = (power < 3500) | (power > 9000)
    osf = wear * torque > np.where(typ == "L", 11000, np.where(typ == "M", 12000, 13000))
    twf = (wear > 200) & (rng.random(n) < 0.02)
    rnf = rng.random(n) < 0.001
    fail = (hdf | pwf | osf | twf | rnf).astype(int)
    return pd.DataFrame(dict(type=typ, air_temperature=air, process_temperature=proc, rotational_speed=rpm, torque=torque,
                             tool_wear=wear, machine_failure=fail, twf=twf.astype(int), hdf=hdf.astype(int),
                             pwf=pwf.astype(int), osf=osf.astype(int), rnf=rnf.astype(int)))

def fetch_uci_frame(uci_id, static_name, member=None):
    """UCI 자료 -> DataFrame. ucimlrepo 우선, 실패 시 static zip(경로 패턴 미검증)."""
    try:
        import importlib.util, subprocess, sys
        if importlib.util.find_spec("ucimlrepo") is None:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ucimlrepo"])
        from ucimlrepo import fetch_ucirepo
        r = fetch_ucirepo(id=uci_id)
        orig = getattr(r.data, "original", None)
        if orig is not None and len(orig):
            return orig
        return pd.concat([r.data.features, r.data.targets], axis=1)
    except Exception as e:
        print(f"ucimlrepo 실패({type(e).__name__}) -> static zip 시도")
        raw = fetch_bytes(f"https://archive.ics.uci.edu/static/public/{uci_id}/{static_name}.zip", timeout=60)
        z = zipfile.ZipFile(io.BytesIO(raw))
        name = member or [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        return pd.read_csv(z.open(name))

def load_ai4i(live=True):
    if live:
        try:
            return parse_ai4i(fetch_uci_frame(601, "ai4i+2020+predictive+maintenance+dataset")), "REAL: UCI AI4I 2020 (합성 생성 자료, CC BY 4.0)"
        except Exception as e:
            print("AI4I 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:100])
    return synthetic_ai4i(), "SYNTHETIC (NOT real data)"
'''

CMAPSS_CODE = r'''
import zipfile
CMAPSS_COLS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]

def parse_cmapss_train(text):
    """C-MAPSS train_FDxxx.txt: 공백 구분 26열, 한 행 = 한 엔진의 한 사이클. RUL = 마지막 사이클 - 현재 사이클."""
    df = pd.read_csv(io.StringIO(text) if isinstance(text, str) else io.BytesIO(text), sep=r"\s+", header=None)
    df = df.dropna(axis=1, how="all")
    if df.shape[1] != 26:
        raise ValueError(f"C-MAPSS 열 수 {df.shape[1]} != 26")
    df.columns = CMAPSS_COLS
    df["rul"] = df.groupby("unit")["cycle"].transform("max") - df["cycle"]
    if df["unit"].nunique() < 50:
        raise ValueError("엔진 수 부족")
    return df

def synthetic_cmapss(n_units=100, seed=2026102):
    """NOT real data: 사이클이 진행될수록 일부 센서가 열화하는 합성 엔진 자료."""
    rng = np.random.default_rng(seed); rows = []
    for u in range(1, n_units + 1):
        L = int(rng.integers(130, 360)); c = np.arange(1, L + 1); w = (c / L) ** 2
        r = {"unit": u, "cycle": c, "op1": rng.normal(0, 0.002, L), "op2": rng.normal(0, 0.0003, L), "op3": 100.0}
        for i in range(1, 22):
            base = 100 + 10 * i; sign = 1 if i % 2 else -1
            r[f"s{i}"] = base + (sign * 8 * w if i in (2, 3, 4, 7, 11, 12, 15, 17, 20, 21) else 0) + rng.normal(0, 0.5, L)
        rows.append(pd.DataFrame(r))
    df = pd.concat(rows, ignore_index=True)
    df["rul"] = df.groupby("unit")["cycle"].transform("max") - df["cycle"]
    return df

def load_cmapss_fd001(live=True):
    if live:
        try:
            z = zipfile.ZipFile(io.BytesIO(fetch_bytes("https://data.nasa.gov/docs/legacy/CMAPSSData.zip", timeout=120)))
            return parse_cmapss_train(z.read("train_FD001.txt")), "REAL: NASA C-MAPSS FD001 (시뮬레이션, 라이선스 표기 없음 - 확인 필요)"
        except Exception as e:
            print("C-MAPSS 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:100])
    return synthetic_cmapss(), "SYNTHETIC (NOT real data)"
'''

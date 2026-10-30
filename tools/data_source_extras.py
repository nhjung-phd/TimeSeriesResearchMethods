"""data_sources 노트북에 추가되는 셀 정의 (학생 예제 Example 01~07의 데이터 수집 부분을 정리·검증 코드와 함께 이식).
각 항목: (종류, 내용, 태그). 코드 셀은 raw 문자열이며 노트북에 그대로 들어간다.
DATA_KIND 변수는 기존 셀이 쓰므로 여기서는 KIND_* 이름을 쓴다(오프라인 테스트가 마지막 DATA_KIND를 검사)."""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
AIRLINE = open(os.path.join(_HERE, "_airline.csv"), encoding="utf-8").read().strip()

EXTRA = {}

# ------------------------------------------------------------------ 01 Finance
EXTRA["01"] = [
("md", r'''
## 추가 A. 미국 거시 3종 (FRED: FEDFUNDS, UNRATE, CPIAUCSL)
- 원 출처: 학생 예제 03번(`pandas_datareader`). 여기서는 **무키 `fredgraph.csv`** 로 읽어 라이브러리 의존을 줄였다(실행 확인 필요).
- 물가상승률은 **월별로 정렬한 뒤** `pct_change(12)`로 계산한다(원 예제는 정렬 전에 계산).
- CPIAUCSL은 사후 개정되는 빈티지 자료이므로 예측 평가에서는 look-ahead 위험을 명시한다.
''', None),
("code", r'''
def build_macro_panel(series_dict):
    """series_dict: {이름: pd.Series}. 월 시작(MS) 기준으로 맞추고 CPI에서 전년동월 대비 상승률을 만든다."""
    df = pd.concat(series_dict, axis=1).sort_index()
    df = df.resample("MS").mean()
    if "CPI" in df:
        df["INFL_YOY"] = df["CPI"].pct_change(12) * 100
    return df

def check_macro(df):
    assert df["FEDFUNDS"].dropna().between(0, 25).all(), "금리 범위 이상"
    assert df["UNRATE"].dropna().between(1, 30).all(), "실업률 범위 이상"
''', ["parsers"]),
("code", r'''
MACRO_IDS = {"FEDFUNDS": "FEDFUNDS", "UNRATE": "UNRATE", "CPI": "CPIAUCSL"}
try:
    ser = {k: parse_fred_csv(fetch_bytes(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={v}")) for k, v in MACRO_IDS.items()}
    macro = build_macro_panel(ser).loc["2000-01-01":"2024-12-31"]
    check_macro(macro)
    KIND_MACRO = "REAL: FRED " + ", ".join(MACRO_IDS.values())
except Exception as e:
    print("FRED 거시 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:100])
    n = 300; rng = np.random.default_rng(2026071); idx = pd.date_range("2000-01-01", periods=n, freq="MS")
    ff = np.clip(2 + np.cumsum(rng.normal(0, 0.15, n)), 0.05, 8)
    un = np.clip(5.5 + np.cumsum(rng.normal(0, 0.12, n)), 3, 12)
    cpi = 170 * np.cumprod(1 + rng.normal(0.0018, 0.002, n))
    macro = build_macro_panel({"FEDFUNDS": pd.Series(ff, idx), "UNRATE": pd.Series(un, idx), "CPI": pd.Series(cpi, idx)})
    KIND_MACRO = "SYNTHETIC (NOT real data)"
print("KIND_MACRO:", KIND_MACRO); print(macro.describe().round(2).T[["count", "mean", "min", "max"]])
macro[["FEDFUNDS", "UNRATE", "INFL_YOY"]].plot(subplots=True, figsize=(10, 6), title=KIND_MACRO); plt.show()
''', None),
("md", r"""
## 추가 B. 금 가격 (저장소 포함 CSV `data/finance/gold_historical_data.csv`)
- 학생 예제 06번이 쓰는 파일을 저장소에 포함했다(2016-02-05 ~ 2026-01-30, 2,510행, 열: Date, Adj Close, Close, High, Low, Open, Volume).
- **출처·라이선스 표기가 없는 파일이다.** Adj Close = Close, 거래량 0 행 36개, 가격대로 보아 Yahoo Finance 금 선물(`GC=F`) 계열로 **추정**되나 확인 필요하며, 재배포 가능 여부도 확인 필요하다.
- 읽는 순서: ① 저장소 파일(로컬 경로 또는 GitHub raw) → ② `yfinance` `GC=F` → ③ 합성. `KIND_GOLD`로 구분한다.
- 금은 금융 시계열이다(비주식이지만 비금융이 아니다). 연속월물 롤오버 단절 가능성과 거래량 0 행은 분석 전에 처리 규칙을 정한다.
""", None),
("code", r"""
def load_gold_csv(raw):
    df = pd.read_csv(io.BytesIO(raw) if isinstance(raw, (bytes, bytearray)) else io.StringIO(raw), parse_dates=["Date"])
    s = df.set_index("Date")["Close"].astype(float).sort_index().rename("gold")
    assert len(s) > 1500 and s.min() > 100 and not s.index.duplicated().any(), "금 CSV 길이/범위/중복 이상"
    return s

def to_log_return(price):
    return np.log(price).diff().dropna().rename("ret")

import os
GOLD_LOCAL = [p for p in ("data/finance/gold_historical_data.csv", "../data/finance/gold_historical_data.csv",
                          "gold_historical_data.csv") if os.path.exists(p)]
GOLD_RAW = "https://raw.githubusercontent.com/nhjung-phd/TimeSeriesResearchMethods/main/data/finance/gold_historical_data.csv"  # push 후 존재, 확인 필요
gold, KIND_GOLD = None, None
try:
    if GOLD_LOCAL:
        gold = load_gold_csv(open(GOLD_LOCAL[0], "rb").read()); KIND_GOLD = "REAL(file): " + GOLD_LOCAL[0] + " (출처 추정 GC=F)"
    else:
        gold = load_gold_csv(fetch_bytes(GOLD_RAW)); KIND_GOLD = "REAL(file): GitHub raw (출처 추정 GC=F)"
except Exception as e:
    print("금 CSV 읽기 실패 -> yfinance 시도:", type(e).__name__, str(e)[:80])
if gold is None:
    try:
        import subprocess, sys, importlib.util
        if importlib.util.find_spec("yfinance") is None:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "yfinance"])
        import yfinance as yf
        g = yf.download("GC=F", start="2016-02-01", end="2026-02-01", progress=False, auto_adjust=False)
        gold = g["Close"].squeeze().dropna().rename("gold")
        assert len(gold) > 1500 and gold.min() > 100
        KIND_GOLD = "REAL: Yahoo Finance GC=F (연속월물, 비공식 API)"
    except Exception as e:
        print("금 yfinance 실패 -> 합성 대체:", type(e).__name__, str(e)[:80])
        rng = np.random.default_rng(2026072)
        gold = pd.Series(1200 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 2500))),
                         index=pd.bdate_range("2016-02-05", periods=2500), name="gold")
        KIND_GOLD = "SYNTHETIC (NOT real data)"
print("KIND_GOLD:", KIND_GOLD); quality_report(gold)
r = to_log_return(gold); print("연율 변동성:", round(float(r.std() * np.sqrt(252)), 3))
""", None),
]

# ------------------------------------------------------------------ 05 Energy / Environment
EXTRA["05"] = [
("md", r'''
## 추가 C. NOAA CO₂ 대체 URL · 일 최저기온 · 조석 (학생 예제 01, 02, 04, 05번)
- **CO₂**: `csv`와 `txt` 두 형식, 여러 URL을 순서대로 시도한다. 평균열 결측은 −99.99이며, 학생 예제 04번의 `{-9.99, -0.99, -1}` 치환은 평균열 결측에 해당하지 않는다(확인 필요). 값 범위 검증(300–600 ppm)을 넣었다.
- **일 최저기온**: Melbourne 1981–1990 일 최저기온(jbrownlee/Datasets). 개인 저장소라 영구성이 보장되지 않는다. 서울 자료가 아니다.
- **조석(Boston 8443970)**: NOAA Tides & Currents 시간별 수위. 주 조석 주기는 약 12.42시간이다. 학생 예제 05번은 계절주기를 12로 둔다.
''', None),
("code", r'''
def parse_noaa_co2_any(raw):
    """NOAA co2_mm_mlo 의 csv/txt 형식을 모두 처리. 평균열 결측(-99.99)은 NaN."""
    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if "," in lines[0]:                                  # csv: 첫 비주석 행이 헤더
        df = pd.read_csv(io.StringIO("\n".join(lines)))
        df.columns = [c.strip().lower() for c in df.columns]
    else:                                                # txt: 공백 구분, 헤더 없음
        cols = ["year", "month", "decimal_date", "average", "deseasonalized", "ndays", "stdev", "uncertainty"]
        df = pd.read_csv(io.StringIO("\n".join(lines)), sep=r"\s+", header=None, names=cols)
    if not {"year", "month", "average"}.issubset(df.columns):
        raise ValueError("예상 열 없음: " + ", ".join(df.columns))
    avg = pd.to_numeric(df["average"], errors="coerce")
    avg = avg.where(avg > -90)
    idx = pd.to_datetime(dict(year=df["year"].astype(int), month=df["month"].astype(int), day=1))
    return pd.Series(avg.values, index=idx, name="co2_ppm")

def check_co2(s):
    v = s.dropna()
    assert len(v) > 600 and v.min() > 300 and v.max() < 600, "CO2 값 범위/길이 이상"

def parse_daily_min_temp(raw):
    df = pd.read_csv(io.BytesIO(raw) if isinstance(raw, (bytes, bytearray)) else io.StringIO(raw))
    df.columns = [c.strip().lower() for c in df.columns]
    return pd.Series(pd.to_numeric(df["temp"], errors="coerce").values, index=pd.to_datetime(df["date"]), name="temp_min")

def parse_tides_json(obj):
    if "data" not in obj:
        raise ValueError("API 응답에 data 없음: " + str(obj)[:120])
    df = pd.DataFrame(obj["data"])
    t = pd.to_datetime(df["t"], errors="coerce")
    return pd.Series(pd.to_numeric(df["v"], errors="coerce").values, index=t, name="water_level_m")[t.notna().values]

def fetch_tides_year(station, year):
    from urllib.parse import urlencode
    q = urlencode(dict(product="hourly_height", application="TimeSeriesCourse", begin_date=f"{year}0101", end_date=f"{year}1231",
                       station=station, datum="MLLW", time_zone="gmt", units="metric", format="json"))
    return parse_tides_json(json.loads(fetch_bytes("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?" + q, timeout=90)))
''', ["parsers"]),
("code", r'''
CO2_URLS = ["https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv",
            "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.txt"]
co2b = None
for u in CO2_URLS:
    try:
        co2b = parse_noaa_co2_any(fetch_bytes(u)); check_co2(co2b); KIND_CO2B = "REAL: " + u; break
    except Exception as e:
        print("CO2 시도 실패:", u.split('/')[-1], type(e).__name__, str(e)[:80]); co2b = None
if co2b is None:
    co2b = synthetic_series(816, "MS", 2026081, trend=0.2, season=12, noise=0.3, start="1958-03-01"); KIND_CO2B = "SYNTHETIC (NOT real data)"
print("KIND_CO2B:", KIND_CO2B, "| n =", len(co2b), "| 결측:", int(co2b.isna().sum()))

try:
    tmin = parse_daily_min_temp(fetch_bytes("https://raw.githubusercontent.com/jbrownlee/Datasets/master/daily-min-temperatures.csv"))
    assert len(tmin) > 3000 and tmin.dropna().between(-10, 40).all(); KIND_TMIN = "REAL: Melbourne daily min temp 1981-1990"
except Exception as e:
    print("일 최저기온 실패 -> 합성 대체:", type(e).__name__, str(e)[:80])
    t = np.arange(3650); rng = np.random.default_rng(2026082)
    tmin = pd.Series(11 + 5 * np.sin(2 * np.pi * t / 365.25) + rng.normal(0, 2.5, 3650), index=pd.date_range("1981-01-01", periods=3650, freq="D"))
    KIND_TMIN = "SYNTHETIC (NOT real data)"
print("KIND_TMIN:", KIND_TMIN, "| n =", len(tmin))

try:
    tides = pd.concat([fetch_tides_year("8443970", y) for y in (2023, 2024, 2025)]).sort_index()
    tides = tides[~tides.index.duplicated()]
    expected = len(pd.date_range("2023-01-01 00:00", "2025-12-31 23:00", freq="h"))
    print("조석 행:", len(tides), "/ 기대", expected)
    assert len(tides) > 0.95 * expected
    KIND_TIDE = "REAL: NOAA Tides & Currents 8443970 hourly_height (MLLW, GMT)"
except Exception as e:
    print("조석 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:80])
    h = np.arange(24 * 365); rng = np.random.default_rng(2026083)
    tides = pd.Series(1.5 + 1.4 * np.sin(2 * np.pi * h / 12.42) + 0.3 * np.sin(2 * np.pi * h / 354.4) + rng.normal(0, 0.1, len(h)),
                      index=pd.date_range("2024-01-01", periods=len(h), freq="h"), name="water_level_m")
    KIND_TIDE = "SYNTHETIC (NOT real data)"
print("KIND_TIDE:", KIND_TIDE, "| n =", len(tides))
fig, ax = plt.subplots(3, 1, figsize=(10, 7)); co2b.plot(ax=ax[0], title=KIND_CO2B)
tmin.plot(ax=ax[1], title=KIND_TMIN); tides.iloc[:24 * 14].plot(ax=ax[2], title="조석 첫 14일: " + KIND_TIDE); plt.tight_layout(); plt.show()
''', None),
]

# ------------------------------------------------------------------ 06 Business / Marketing
EXTRA["06"] = [
("md", r'''
## 추가 D. 국제선 항공 승객 (Box–Jenkins, 1949–1960 월별 144개)
- 학생 예제 07번이 쓰는 고전 교육용 시계열. **네트워크 없이** 저장소에 내장한 값을 쓰므로 항상 재현된다(원 예제의 내장 CSV와 동일 값, 첫 값 112, 마지막 값 432).
- 승법적 계절성(변동이 수준과 함께 커짐)이 있어 **로그 변환** 후 SARIMA/ETS를 쓰는 것이 표준이다. 표본이 작으므로(144) 외표본 결론은 신중히 해석한다.
''', None),
("code", '''
AIRLINE_CSV = """@@AIRLINE@@"""
''' + r'''def load_airline():
    df = pd.read_csv(io.StringIO(AIRLINE_CSV))
    df.columns = ["month", "passengers"]
    s = pd.Series(df["passengers"].astype(float).values, index=pd.to_datetime(df["month"]), name="passengers").asfreq("MS")
    assert len(s) == 144 and s.isna().sum() == 0 and s.iloc[0] == 112 and s.iloc[-1] == 432
    return s
air = load_airline(); KIND_AIR = "REAL (embedded): Box-Jenkins airline passengers 1949-1960"
print("KIND_AIR:", KIND_AIR); quality_report(air)
fig, ax = plt.subplots(1, 2, figsize=(11, 3.5)); air.plot(ax=ax[0], title="수준 (변동이 커짐)"); np.log(air).plot(ax=ax[1], title="로그"); plt.tight_layout(); plt.show()
''', None),
]
EXTRA["06"] = [(k, t.replace("@@AIRLINE@@", AIRLINE), g) for k, t, g in EXTRA["06"]]


# ------------------------------------------------------------------ 03 Manufacturing (작은 공개 자료)
from nbgen.mfg_real import AI4I_CODE, CMAPSS_CODE

_MFG_PARSERS_EXTRA = r'''
def parse_secom(data_text, labels_text):
    """secom.data(공백 구분, 'NaN' 결측) + secom_labels.data(라벨 [날짜 시간]). 타임스탬프 열이 있으면 index로 쓴다."""
    X = pd.read_csv(io.StringIO(data_text), sep=r"\s+", header=None, na_values=["NaN"])
    lab = pd.read_csv(io.StringIO(labels_text), sep=r"\s+", header=None)
    if len(lab) != len(X):
        raise ValueError("SECOM 행 수 불일치")
    y = pd.to_numeric(lab[0]).map({-1: 0, 1: 1})        # 1 = 불량(fail)
    if y.isna().any():
        raise ValueError("SECOM 라벨 값 이상(-1/1 외)")
    if lab.shape[1] >= 3:
        X.index = pd.to_datetime(lab[1] + " " + lab[2], dayfirst=True, errors="coerce")
    X.columns = [f"f{i}" for i in range(X.shape[1])]
    return X, y.rename("fail").set_axis(X.index)

def synthetic_secom(n=1567, p=60, seed=2026103):
    """NOT real data: 결측·불균형이 있는 합성 공정 센서 표."""
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(0, 1, (n, p)), columns=[f"f{i}" for i in range(p)],
                     index=pd.date_range("2008-07-19", periods=n, freq="40min"))
    y = pd.Series((rng.random(n) < 0.066 + 0.03 * (X["f0"] > 1.5)).astype(int), index=X.index, name="fail")
    X.loc[y == 1, "f1"] += 0.8
    X = X.mask(rng.random((n, p)) < 0.05)
    return X, y

STEEL_CLASSES = ["Pastry", "Z_Scratch", "K_Scatch", "Stains", "Dirtiness", "Bumps", "Other_Faults"]

def parse_steel(df):
    d = df.copy()
    cols = [c for c in d.columns if str(c).strip() in STEEL_CLASSES]
    if len(cols) != 7:
        cols = list(d.columns[-7:])                      # 열 이름이 다르면 마지막 7열을 결함 지시열로 가정 (확인 필요)
    y = d[cols].astype(int).values.argmax(axis=1)
    X = d.drop(columns=cols).select_dtypes("number")
    if len(d) < 1500 or X.shape[1] < 20:
        raise ValueError("Steel Plates 길이/특성 수 이상")
    return X.reset_index(drop=True), pd.Series(y, name="fault_class")

def synthetic_steel(n=1941, p=27, seed=2026104):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 7, n); X = pd.DataFrame(rng.normal(0, 1, (n, p)), columns=[f"x{i}" for i in range(p)])
    for k in range(7):
        X.loc[y == k, f"x{k}"] += 1.5
    return X, pd.Series(y, name="fault_class")

def parse_cwru_mat(raw):
    """CWRU .mat -> 구동단(DE) 가속도 신호. 변수명 규칙: 'X###_DE_time'."""
    from scipy.io import loadmat
    m = loadmat(io.BytesIO(raw))
    key = [k for k in m if k.endswith("_DE_time")]
    if not key:
        raise ValueError("DE_time 변수 없음: " + ", ".join(k for k in m if not k.startswith("__")))
    return np.asarray(m[key[0]]).ravel().astype(float)

def synthetic_bearing(fs=12000, seconds=4, fault_hz=0.0, seed=2026105):
    """NOT real data: 공진 + 잡음, fault_hz>0이면 그 주기로 충격(외륜결함 유사). 주파수 값은 가정이다."""
    rng = np.random.default_rng(seed); n = fs * seconds; t = np.arange(n) / fs
    x = 0.05 * np.sin(2 * np.pi * 30 * t) + rng.normal(0, 0.05, n)
    if fault_hz > 0:
        for t0 in np.arange(0, seconds, 1 / fault_hz):
            i = int(t0 * fs); k = np.arange(min(200, n - i))
            x[i:i + len(k)] += 0.8 * np.exp(-k / 40) * np.sin(2 * np.pi * 3000 * k / fs)
    return x

def bearing_features(x):
    from scipy.stats import kurtosis
    return dict(rms=float(np.sqrt(np.mean(x ** 2))), kurtosis=float(kurtosis(x)), peak=float(np.max(np.abs(x))))
'''

EXTRA["03"] = [
("md", r'''
## 추가 · 작은 공개 제조 자료 (용량 순)

| 자료 | 용량·규모 | 라이선스 | 검증 | 성격 |
|---|---|---|---|---|
| UCI AI4I 2020 (id 601) | 약 0.5MB, 10,000행 | CC BY 4.0 | A (페이지 확인) | **합성 생성 표**. 행이 독립적이며 시계열 아님 |
| UCI Steel Plates Faults (id 198) | 약 0.1MB, 1,941×27 | CC BY 4.0 | A | 결함 유형 분류 표 |
| UCI SECOM (id 179) | 약 1.9MB, 1,567×591 | CC BY 4.0 | A | 공정 센서 + 합불. 결측 많음. 타임스탬프는 라벨 파일에 있는 것으로 알려져 있음(확인 필요) |
| NASA C-MAPSS FD001 | 텍스트 ZIP(용량 미확인) | 표기 없음 | B (카탈로그 페이지 확인) | **시뮬레이션** 엔진 열화(사이클 단위, 달력 시간 아님) |
| CWRU 베어링 `.mat` | 파일당 수 MB 추정 | 이용약관 표기 없음 | B | 진동 신호. `.mat` 직접 URL은 사이트에서 복사해 `CWRU_URLS`에 넣을 것(미검증) |

**주의:** AI4I의 고장 유형 열(TWF, HDF, PWF, OSF, RNF)은 `machine_failure`를 거의 결정하므로 특성으로 쓰면 **누수**다. 이 저장소 코드는 이 열들을 분리한다.
이 표들은 **달력 시계열이 아니므로** ARIMA·계절성 분석에 쓰지 않는다. C-MAPSS는 사이클 기반이고, CWRU는 고주파 신호 분류용이다.
''', None),
("code", _MFG_PARSERS_EXTRA + AI4I_CODE + CMAPSS_CODE, ["parsers"]),
("code", r'''
def majority_acc(y):
    return float(y.value_counts(normalize=True).max())

# 1) AI4I
ai4i, KIND_AI4I = load_ai4i(live=True)
print("KIND_AI4I:", KIND_AI4I, "|", ai4i.shape, "| 고장 비율:", round(float(ai4i['machine_failure'].mean()), 4),
      "| 항상 '정상' 예측 정확도:", round(1 - float(ai4i['machine_failure'].mean()), 4), "(정확도는 불균형에서 무의미)")

# 2) Steel Plates
try:
    Xs, ys = parse_steel(fetch_uci_frame(198, "steel+plates+faults")); KIND_STEEL = "REAL: UCI Steel Plates Faults"
except Exception as e:
    print("Steel 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:100]); Xs, ys = synthetic_steel(); KIND_STEEL = "SYNTHETIC (NOT real data)"
print("KIND_STEEL:", KIND_STEEL, "|", Xs.shape, "| 최빈 클래스 비율:", round(majority_acc(ys), 3))

# 3) SECOM (static zip: 타임스탬프 포함 가능, 경로 패턴 미검증 -> 실패 시 ucimlrepo)
try:
    z = zipfile.ZipFile(io.BytesIO(fetch_bytes("https://archive.ics.uci.edu/static/public/179/secom.zip", timeout=60)))
    Xq, yq = parse_secom(z.read("secom.data").decode(), z.read("secom_labels.data").decode()); KIND_SECOM = "REAL: UCI SECOM (static zip)"
except Exception as e:
    print("SECOM static zip 실패:", type(e).__name__, str(e)[:80])
    try:
        raw = fetch_uci_frame(179, "secom")
        ycol = [c for c in raw.columns if "pass" in str(c).lower() or "fail" in str(c).lower()]
        yq = raw[ycol[0]].map({-1: 0, 1: 1}).rename("fail"); Xq = raw.drop(columns=ycol); KIND_SECOM = "REAL: UCI SECOM (ucimlrepo, 타임스탬프 없음)"
    except Exception as e2:
        print("SECOM ucimlrepo 실패 -> 합성 대체:", type(e2).__name__, str(e2)[:80]); Xq, yq = synthetic_secom(); KIND_SECOM = "SYNTHETIC (NOT real data)"
print("KIND_SECOM:", KIND_SECOM, "|", Xq.shape, "| 불량 비율:", round(float(yq.mean()), 4), "| 결측 비율:", round(float(Xq.isna().mean().mean()), 3))

# 4) C-MAPSS FD001
cm, KIND_CMAPSS = load_cmapss_fd001(live=True)
print("KIND_CMAPSS:", KIND_CMAPSS, "|", cm.shape, "| 엔진 수:", cm['unit'].nunique(), "| 수명(사이클) 중앙값:", int(cm.groupby('unit')['cycle'].max().median()))

# 5) CWRU: 사이트에서 복사한 .mat URL을 넣으면 사용 (미입력/실패 시 합성)
CWRU_URLS = {"normal": "", "outer_race": ""}          # 예: {"normal": "<97.mat 링크>", "outer_race": "<외륜 결함 .mat 링크>"} (확인 필요)
try:
    sig = {k: parse_cwru_mat(fetch_bytes(u, timeout=60)) for k, u in CWRU_URLS.items() if u}
    assert len(sig) == len(CWRU_URLS), "URL 미입력"
    KIND_CWRU = "REAL: CWRU .mat (DE 가속도)"
except Exception as e:
    print("CWRU -> 합성 대체:", type(e).__name__, str(e)[:80])
    sig = {"normal": synthetic_bearing(fault_hz=0.0), "outer_race": synthetic_bearing(fault_hz=105.0)}; KIND_CWRU = "SYNTHETIC (NOT real data)"
print("KIND_CWRU:", KIND_CWRU, {k: {a: round(b, 3) for a, b in bearing_features(v).items()} for k, v in sig.items()})
''', None),
("md", r'''
## 점검 체크리스트 (추가분)
- 표 자료(AI4I, Steel, SECOM)는 **행이 독립**인지, 시간 순서가 의미 있는지(SECOM) 먼저 확인한다. 시간 순서가 있으면 무작위 분할 대신 시간순 분할을 쓴다.
- 클래스 불균형에서는 정확도 대신 PR-AUC와 기준선(항상 정상)을 같이 보고한다.
- CWRU: 같은 녹화에서 자른 세그먼트를 train/test에 섞으면 누수다. 부하·결함 크기 단위로 분할한다(Ch.7).
- C-MAPSS RUL: 사이클 번호는 달력 시간이 아니다. 시뮬레이션 자료의 성능은 실제 설비 성능이 아니다.
''', None),
]

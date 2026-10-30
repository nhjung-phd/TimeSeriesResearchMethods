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

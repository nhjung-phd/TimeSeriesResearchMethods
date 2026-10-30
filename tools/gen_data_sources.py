import json, uuid, sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_source_extras import EXTRA
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data_sources') + os.sep
def md(s): return {"cell_type":"markdown","id":uuid.uuid4().hex[:8],"metadata":{},"source":s.strip('\n').splitlines(True)}
def code(s,tags=None):
    m={"tags":tags} if tags else {}
    return {"cell_type":"code","execution_count":None,"id":uuid.uuid4().hex[:8],"metadata":m,"outputs":[],"source":s.strip('\n').splitlines(True)}
def nb(cells):
    return {"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":5}

COMMON='''
import io, json, urllib.request, numpy as np, pandas as pd, matplotlib.pyplot as plt

def fetch_bytes(url, timeout=30):
    """무키 공개 URL 요청. 실패 시 예외 -> 호출부에서 합성 대체."""
    req = urllib.request.Request(url, headers={"User-Agent": "ts-lab-course/1.0 (education)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def synthetic_series(n, freq, seed, trend=0.05, season=12, noise=1.0, start="2015-01-01"):
    """NOT real data: 방법 시연용 합성 시계열."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    y = 100 + trend * t + 3 * np.sin(2 * np.pi * t / season) + rng.normal(0, noise, n)
    return pd.Series(y, index=pd.date_range(start, periods=n, freq=freq), name="value")

def quality_report(s):
    s = s.sort_index()
    print("관측 수:", len(s), "| 기간:", s.index.min(), "~", s.index.max())
    print("결측:", int(s.isna().sum()), "| 중복 시점:", int(s.index.duplicated().sum()))
    f = pd.infer_freq(s.index) if len(s) > 2 else None
    print("추정 주기:", f)
'''

def build(num, name, title, intro, parsers, loader, extra_md):
    cells=[md(intro), code(COMMON), code(parsers, ["parsers"]), code(loader), md(extra_md)]
    for kind, txt, tags in EXTRA.get(num, []):
        cells.append(md(txt) if kind == "md" else code(txt, tags))
    json.dump(nb(cells), open(ROOT+f"{num}_{name}_Data.ipynb","w"), ensure_ascii=False, indent=1)

# ---------------- 01 Finance ----------------
build("01","Finance","금융·투자",'''
# Data Source 01 · 금융·투자

**목적:** 수집할 시계열의 단위·주기·결측·발표시점을 점검한다.

| 출처 | 접근 | 검증 상태 |
|---|---|---|
| FRED `fredgraph.csv` (예: `DGS10` 10년 국채금리) | 무키 | B (엔드포인트·헤더 수업 전 확인) |
| Yahoo Finance (`yfinance`) | 무키(비공식) | B |
| 한국은행 ECOS | 무료키 | C |
| Ken French Data Library | 수동 | C |

자세한 목록: `resources/Data_Source_Catalog.md`. **API 키는 파일에 쓰지 말고 `getpass`/환경변수로만 입력**한다.
온라인 연결이 실패하면 합성자료로 대체하며 `DATA_KIND`로 구분한다. 합성자료의 결과는 실제 현상의 증거가 아니다.
''','''
def parse_fred_csv(raw):
    """FRED fredgraph.csv 파싱. 날짜 열 이름이 DATE 또는 observation_date일 수 있고, 결측은 '.' 로 표시될 수 있다."""
    df = pd.read_csv(io.BytesIO(raw) if isinstance(raw, (bytes, bytearray)) else io.StringIO(raw))
    date_col = next(c for c in df.columns if c.lower() in ("date", "observation_date"))
    val_col = [c for c in df.columns if c != date_col][0]
    s = pd.Series(pd.to_numeric(df[val_col], errors="coerce").values,
                  index=pd.to_datetime(df[date_col]), name=val_col)
    return s
''','''
SERIES_ID = "DGS10"   # FRED 시리즈 ID. 실제 존재·단위는 FRED 페이지에서 확인할 것.
try:
    raw = fetch_bytes(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}")
    y = parse_fred_csv(raw)
    DATA_KIND = "REAL: FRED " + SERIES_ID
except Exception as e:
    print("온라인 수집 실패 -> 합성 대체:", type(e).__name__, e)
    y = synthetic_series(1500, "B", 2026011, trend=0.002, season=250, noise=0.15, start="2018-01-01")
    DATA_KIND = "SYNTHETIC (NOT real data)"
print("DATA_KIND:", DATA_KIND)
quality_report(y)
y.plot(title=DATA_KIND); plt.show()
''','''
## 점검 체크리스트
- 단위(%, 지수, 수준)와 **주기**(영업일/월)가 연구질문과 맞는가
- 결측(휴장일)·대체 규칙을 사전에 정의했는가
- 수정주가/발표시점(빈티지): 사후 개정 값을 쓰면 look-ahead 위험
- 라이선스·재배포 조건: 원자료는 저장소에 올리지 않는다
''')

# ---------------- 02 RealEstate ----------------
build("02","RealEstate","부동산",'''
# Data Source 02 · 부동산

| 출처 | 접근 | 검증 상태 |
|---|---|---|
| FHFA House Price Index CSV (`hpi_master`, `hpi_at_state` 등) | 무키 | A(파일명) / B(전체 URL 확인 필요) |
| 한국부동산원 R-ONE | 신청/무료키 | C |
| 국토교통부 실거래가 (공공데이터포털) | 무료키 | C |

FHFA 파일의 **정확한 URL은 FHFA HPI 다운로드 페이지에서 복사**해 `HPI_URL`에 넣는다(아래 값은 확인 필요한 추정 경로).
열 구성은 파일 버전마다 다를 수 있어 로더는 열 이름을 소문자로 정규화하고, 필수 열이 없으면 합성자료로 대체한다.
''','''
def parse_fhfa_master(raw):
    df = pd.read_csv(io.BytesIO(raw) if isinstance(raw, (bytes, bytearray)) else io.StringIO(raw))
    df.columns = [c.strip().lower() for c in df.columns]
    need = {"yr", "period"}
    if not need.issubset(df.columns):
        raise ValueError("예상 열(yr, period) 없음: " + ", ".join(df.columns[:10]))
    return df
''','''
HPI_URL = "https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv"  # 확인 필요: 다운로드 페이지에서 실제 링크 복사
try:
    df = parse_fhfa_master(fetch_bytes(HPI_URL, timeout=60))
    print("열:", list(df.columns))
    DATA_KIND = "REAL: FHFA (열 선택은 아래에서 직접 확인)"
    # 열 이름 확인 후 직접 지정: 예) 지역/지수 구분 열로 필터링해 월별 시리즈 구성
except Exception as e:
    print("온라인 수집 실패 -> 합성 대체:", type(e).__name__, e)
    y = synthetic_series(240, "MS", 2026021, trend=0.4, season=12, noise=0.8, start="2005-01-01")
    DATA_KIND = "SYNTHETIC (NOT real data)"
    quality_report(y); y.plot(title=DATA_KIND); plt.show()
print("DATA_KIND:", DATA_KIND)
''','''
## 점검 체크리스트
- 지수의 기준시점·지수화 방식, 계절조정 여부 (SA/NSA)
- 지역 코드 체계(주/대도시권)와 패널 균형 여부
- 품질·면적 구성 변화(실거래 단위 자료일 때)
- 국내 자료(R-ONE, 실거래가)는 키·이용허락 확인 후 별도 셀로 추가
''')

# ---------------- 03 Manufacturing ----------------
build("03","Manufacturing","제조·품질",'''
# Data Source 03 · 제조·품질

> **솔직한 한계:** 달력 시간이 있는 무료 제조 시계열은 드물다. 아래 "추가" 셀에서 작은 공개 자료(AI4I, Steel Plates, SECOM, C-MAPSS, CWRU)를 다룬다. 이들은 대부분 **달력 시계열이 아니라** 표·사이클·신호 자료다.

이 노트북의 기본 경로(아래 셀)는 **합성 공정 자료 + 관리도 시연**이다. 실데이터 로더는 "추가" 셀에 있다.
''','''
def synthetic_process(n=400, seed=2026031, shift_at=250, shift=1.2):
    """NOT real data: 평균 이동이 있는 공정 측정값 (관리도 시연용)."""
    rng = np.random.default_rng(seed)
    x = rng.normal(10, 0.5, n)
    x[shift_at:] += shift
    return pd.Series(x, index=pd.RangeIndex(n), name="measure"), shift_at
''','''
USE_SECOM = False   # True로 바꾸면 UCI SECOM을 시도 (pip install ucimlrepo 필요, 구조는 직접 확인)
DATA_KIND = None
if USE_SECOM:
    try:
        from ucimlrepo import fetch_ucirepo
        secom = fetch_ucirepo(id=179)
        X = secom.data.features
        print("SECOM 특성 shape:", X.shape, "| 타임스탬프 열 여부는 secom.data.original 확인")
        DATA_KIND = "REAL: UCI SECOM (구조 확인 필요)"
    except Exception as e:
        print("SECOM 수집 실패 -> 합성 대체:", type(e).__name__, e)
if DATA_KIND is None:
    y, brk = synthetic_process()
    DATA_KIND = "SYNTHETIC (NOT real data)"
    mu0, sd0 = y.iloc[:brk].mean(), y.iloc[:brk].std()
    fig, ax = plt.subplots()
    ax.plot(y.index.to_numpy(), y.to_numpy()); ax.set_title(DATA_KIND)
    ax.axhline(mu0 + 3 * sd0, ls="--"); ax.axhline(mu0 - 3 * sd0, ls="--"); plt.show()
print("DATA_KIND:", DATA_KIND)
''','''
## 점검 체크리스트
- 관측 단위가 **시간(달력)**인지, 로트·사이클 번호인지: 사이클 자료에 달력 기반 ARIMA/계절성을 적용하지 않는다
- 라벨(합불)의 시점 정렬과 누수 여부 (Ch.8)
- 센서 결측·드리프트와 교정 시점
- 라이선스 확인 전 원자료 재배포 금지
''')

# ---------------- 04 PublicPolicy ----------------
build("04","PublicPolicy","공공정책",'''
# Data Source 04 · 공공정책

| 출처 | 접근 | 검증 상태 |
|---|---|---|
| California Prop 99 (`synthdid` 저장소 `california_prop99.csv`) | 무키 (GitHub raw) | A(열 구성) / B(라이선스) |
| World Bank API v2 | 무키 | A |
| NYC 311 Socrata (`erm2-nwe9`) | 무키(제한) | A |
| KOSIS / 공공데이터포털 | 무료키 | C |

Prop 99는 **구분자가 `;`** 이고 열이 State, Year, PacksPerCapita, treated이다. 합성대조(SCM)·DID 실습(Ch.7)의 대표 자료로 알려져 있다.
''','''
def parse_prop99(raw):
    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
    df = pd.read_csv(io.StringIO(text), sep=";")
    cols = {c.strip().lower(): c for c in df.columns}
    for need in ("state", "year", "packspercapita", "treated"):
        if need not in cols:
            raise ValueError("예상 열 없음: " + need + " / 실제: " + ", ".join(df.columns))
    df = df.rename(columns={cols["state"]: "State", cols["year"]: "Year",
                            cols["packspercapita"]: "PacksPerCapita", cols["treated"]: "treated"})
    return df
''','''
URL = "https://raw.githubusercontent.com/synth-inference/synthdid/master/data/california_prop99.csv"
try:
    df = parse_prop99(fetch_bytes(URL))
    DATA_KIND = "REAL: California Prop 99 (synthdid repo)"
except Exception as e:
    print("온라인 수집 실패 -> 합성 패널 대체:", type(e).__name__, e)
    rng = np.random.default_rng(2026041)
    rows = []
    for s in range(30):
        base = 120 + rng.normal(0, 15); tr = -0.8 + rng.normal(0, 0.2)
        for yr in range(1970, 2001):
            eff = -20 * (yr - 1988) / 12 if (s == 0 and yr >= 1989) else 0   # 합성 처치효과
            rows.append((f"S{s}", yr, base + tr * (yr - 1970) + eff + rng.normal(0, 2), int(s == 0 and yr >= 1989)))
    df = pd.DataFrame(rows, columns=["State", "Year", "PacksPerCapita", "treated"])
    DATA_KIND = "SYNTHETIC (NOT real data)"
print("DATA_KIND:", DATA_KIND, "| shape:", df.shape, "| 단위 수:", df["State"].nunique())
wide = df.pivot(index="Year", columns="State", values="PacksPerCapita")
print("패널 균형 여부(결측 수):", int(wide.isna().sum().sum()))
wide.iloc[:, :8].plot(legend=False, title=DATA_KIND); plt.show()
''','''
## 점검 체크리스트
- 처치 표시(`treated`)가 처치 시점 이후 모든 기간에서 1인가, 처치 전 기간의 사전추세는 평행한가
- 도너풀 오염(유사 정책을 시행한 주)을 제외했는가
- 정책 시점의 정의·발표 시점 vs 시행 시점
- 국내 자료(KOSIS, data.go.kr)는 키 발급 후 별도 셀로 추가. 통계표 ID는 공식 포털에서 확인
''')

# ---------------- 05 EnergyEnvironment ----------------
build("05","EnergyEnvironment","에너지·환경",'''
# Data Source 05 · 에너지·환경

| 출처 | 접근 | 검증 상태 |
|---|---|---|
| NOAA GML Mauna Loa CO₂ 월별 (`co2_mm_mlo.csv`) | 무키 | A |
| Open-Meteo Historical Weather (ERA5 재분석) | 무키 | A (일평균 변수명은 응답으로 확인) |
| Open-Meteo Air Quality | 무키 | A (한국 지점은 해상도 낮음, 예측 자료는 실측 아님) |
| Open Power System Data / UCI Household Power | 수동 | B / A |
| 기상청 KMA / AirKorea | 무료키·신청 | C |

NOAA 파일은 `#` 주석 행이 있고 결측이 **−99.99**로 표시된다. Open-Meteo는 **관측소 값이 아니라 재분석 격자 값**이다.
''','''
def parse_noaa_co2(raw):
    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
    df = pd.read_csv(io.StringIO(text), comment="#")
    df.columns = [c.strip().lower() for c in df.columns]
    if not {"year", "month", "average"}.issubset(df.columns):
        raise ValueError("예상 열 없음: " + ", ".join(df.columns))
    s = df["average"].where(df["average"] > -90)          # -99.99 -> NaN
    idx = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    return pd.Series(s.values, index=idx, name="co2_ppm")

def parse_openmeteo_daily(obj):
    d = obj["daily"]
    tmax = pd.Series(d["temperature_2m_max"], index=pd.to_datetime(d["time"]))
    tmin = pd.Series(d["temperature_2m_min"], index=pd.to_datetime(d["time"]))
    return ((tmax + tmin) / 2).rename("t_mid")             # 최고·최저 평균: 정의된 일평균이 아님
''','''
try:
    co2 = parse_noaa_co2(fetch_bytes("https://gml.noaa.gov/aftp/products/trends/co2/co2_mm_mlo.csv"))
    DATA_KIND = "REAL: NOAA GML Mauna Loa CO2"
except Exception as e:
    print("NOAA 수집 실패 -> 합성 대체:", type(e).__name__, e)
    co2 = synthetic_series(720, "MS", 2026051, trend=0.15, season=12, noise=0.3, start="1965-01-01")
    DATA_KIND = "SYNTHETIC (NOT real data)"
print("DATA_KIND (CO2):", DATA_KIND); quality_report(co2); co2.plot(title=DATA_KIND); plt.show()

# 선택: Open-Meteo 서울 일 기온 (무키, 비상업 무료, 호출 제한 있음)
try:
    u = ("https://archive-api.open-meteo.com/v1/archive?latitude=37.57&longitude=126.98"
         "&start_date=2020-01-01&end_date=2023-12-31&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FSeoul")
    t = parse_openmeteo_daily(json.loads(fetch_bytes(u, timeout=60)))
    print("REAL (ERA5 재분석, 관측소 아님):", len(t), "일"); t.plot(title="Seoul t_mid (Open-Meteo/ERA5)"); plt.show()
except Exception as e:
    print("Open-Meteo 실패 (선택 항목):", type(e).__name__, e)
''','''
## 점검 체크리스트
- 재분석/모델 값과 관측소 실측을 구분해 보고한다
- 결측 코드(−99.99 등)와 시간대(UTC/현지)
- 예측(forecast) 자료를 과거 실측처럼 쓰지 않는다
- 국내 자료(KMA, AirKorea, KPX)는 키·이용약관 확인 후 추가
''')

# ---------------- 06 BusinessMarketing ----------------
build("06","BusinessMarketing","경영·마케팅",'''
# Data Source 06 · 경영·마케팅

| 출처 | 접근 | 검증 상태 |
|---|---|---|
| Wikimedia Pageviews REST API | 무키 (User-Agent 필요) | A |
| UCI Online Retail II (id 502, CC BY 4.0) | 수동 | A |
| UCI Bike Sharing (id 275, CC BY 4.0) | 수동 | A |
| Google Trends (`pytrends`) | 비공식 | C (권장 안 함) |

기본 경로는 Wikimedia 일별 조회수(관심도 대리변수)이다. 소매 거래·대여량은 UCI에서 내려받아 별도 셀로 읽는다.
''','''
def parse_wikimedia_pageviews(obj):
    items = obj["items"]
    idx = pd.to_datetime([it["timestamp"][:8] for it in items], format="%Y%m%d")
    return pd.Series([it["views"] for it in items], index=idx, name="views")
''','''
ARTICLE = "Time_series"
try:
    u = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
         f"{ARTICLE}/daily/20230101/20231231")
    y = parse_wikimedia_pageviews(json.loads(fetch_bytes(u)))
    DATA_KIND = "REAL: Wikimedia pageviews " + ARTICLE
except Exception as e:
    print("수집 실패 -> 합성 대체:", type(e).__name__, e)
    y = synthetic_series(365, "D", 2026061, trend=0.02, season=7, noise=2.0, start="2023-01-01")
    DATA_KIND = "SYNTHETIC (NOT real data)"
print("DATA_KIND:", DATA_KIND); quality_report(y); y.plot(title=DATA_KIND); plt.show()
''','''
## 점검 체크리스트
- 조회수는 봇/자동 접근 필터(`user` 에이전트) 정의에 따라 달라진다
- 개입(캠페인·이벤트) 날짜가 외생적인지 사전에 정의했는가 (Ch.7)
- Online Retail II: 취소/반품 행(송장번호 `C` 접두 등)과 결측 고객ID 처리는 데이터 설명 페이지로 확인
- 개인정보·라이선스 조건 확인. 원자료는 재배포하지 않는다
''')
print("ok")

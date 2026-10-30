# 도메인별 데이터 로더 코드. 온라인 시도 -> 실패 시 명시적 합성 대체. 모든 합성은 "NOT real data"로 표시.

FINANCE = r'''
def garch_sim(n, seed, omega=0.02, alpha=0.08, beta=0.90):
    rng = np.random.default_rng(seed); r = np.zeros(n); s2 = omega / (1 - alpha - beta)
    for t in range(n):
        r[t] = np.sqrt(s2) * rng.standard_normal()
        s2 = omega + alpha * r[t] ** 2 + beta * s2
    return r + 0.04                                            # 일수익률(%) , 약간의 양의 평균

def load_finance():
    px, kind = None, "SYNTHETIC (NOT real data): GARCH(1,1) 수익률로 만든 가격"
    if USE_LIVE_DATA and ensure("yfinance"):
        try:
            import yfinance as yf
            raw = yf.download("SPY", start="2015-01-01", progress=False, auto_adjust=True)
            c = raw["Close"]
            if isinstance(c, pd.DataFrame):
                c = c.iloc[:, 0]
            c = c.dropna().astype(float)
            if len(c) > 500:
                px, kind = c, "REAL: SPY (Yahoo Finance, yfinance)"
        except Exception as e:
            print("온라인 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:120])
    if px is None:
        r = garch_sim(2500, SEED)
        px = pd.Series(100 * np.exp(np.cumsum(r / 100)), index=pd.bdate_range("2015-01-01", periods=2500))
    px.index = pd.to_datetime(px.index)
    if getattr(px.index, "tz", None) is not None:
        px.index = px.index.tz_localize(None)
    return dict(y=px.rename("price"), kind=kind, m=5, freq="B", label="SPY 종가", unit="USD")

D = load_finance()
y, DATA_KIND, M, FREQ = D["y"], D["kind"], D["m"], D["freq"]
ret = (np.log(y).diff().dropna() * 100).rename("log_return_pct")      # 로그수익률(%)
print("DATA_KIND:", DATA_KIND); print("관측 수:", len(y), "| 기간:", y.index.min().date(), "~", y.index.max().date())
'''

REALESTATE = r'''
def parse_fhfa_master(raw):
    # FHFA hpi_master.csv 파싱. 스키마(열 이름)는 버전에 따라 달라질 수 있어 방어적으로 처리하고, 실패하면 예외를 낸다.
    df = pd.read_csv(io.BytesIO(raw) if isinstance(raw, (bytes, bytearray)) else io.StringIO(raw))
    df.columns = [c.strip().lower() for c in df.columns]
    if not {"yr", "period"}.issubset(df.columns):
        raise ValueError("열(yr, period) 없음: " + ", ".join(df.columns[:12]))
    col = "index_nsa" if "index_nsa" in df.columns else None
    if col is None:
        raise ValueError("index_nsa 열 없음")
    if "frequency" in df.columns:
        df = df[df["frequency"].astype(str).str.lower().str.startswith("month")]
    keys = [k for k in ("hpi_type", "hpi_flavor", "level", "place_id", "place_name") if k in df.columns]
    g = df.groupby(keys).size().sort_values(ascending=False)
    if keys:
        df = df.merge(g.index[:1].to_frame(index=False), on=keys)   # 관측이 가장 많은 한 계열
    s = pd.Series(pd.to_numeric(df[col], errors="coerce").values,
                  index=pd.to_datetime(dict(year=df["yr"].astype(int), month=df["period"].astype(int), day=1)))
    s = s.dropna().sort_index()
    if len(s) < 100:
        raise ValueError("관측 수 부족")
    return s

def synthetic_house(n=300, seed=SEED):
    rng = np.random.default_rng(seed); t = np.arange(n)
    cycle = 6 * np.sin(2 * np.pi * t / 120)
    seas = 1.2 * np.sin(2 * np.pi * (t % 12) / 12 - 1.0)
    shock = np.cumsum(rng.normal(0, 0.35, n))
    return pd.Series(100 + 0.35 * t + cycle + seas + shock, index=pd.date_range("2000-01-01", periods=n, freq="MS"))

def synthetic_volume(n=240, seed=SEED + 1):
    rng = np.random.default_rng(seed); t = np.arange(n)
    seas = 18 * np.sin(2 * np.pi * (t % 12) / 12 - 1.5)
    return pd.Series(np.maximum(200 + 0.2 * t + seas + np.cumsum(rng.normal(0, 1.2, n)) + rng.normal(0, 6, n), 10),
                     index=pd.date_range("2005-01-01", periods=n, freq="MS"))

def load_realestate(which="price"):
    if which == "volume":
        return dict(y=synthetic_volume().rename("volume"), m=12, freq="MS", label="월별 주택거래량(합성)", unit="건",
                    kind="SYNTHETIC (NOT real data): 검증된 무료 거래량 출처 없음")
    s, kind = None, "SYNTHETIC (NOT real data): 추세+주기+계절+확률적 충격 주택가격지수"
    if USE_LIVE_DATA:
        try:
            s = parse_fhfa_master(fetch_bytes("https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv", timeout=90))
            kind = "REAL: FHFA HPI (index_nsa, 계열 선택 규칙은 parse_fhfa_master 참고)"
        except Exception as e:
            print("FHFA 수집/파싱 실패 -> 합성 대체:", type(e).__name__, str(e)[:120])
    if s is None:
        s = synthetic_house()
    return dict(y=s.rename("hpi"), m=12, freq="MS", label="주택가격지수", unit="지수", kind=kind)

D = load_realestate("@@WHICH@@")
y, DATA_KIND, M, FREQ = D["y"], D["kind"], D["m"], D["freq"]
print("DATA_KIND:", DATA_KIND); print("관측 수:", len(y), "| 기간:", y.index.min().date(), "~", y.index.max().date())
'''

MANUFACTURING = r'''
def synthetic_sensor(n_days=180, seed=SEED, n_faults=14):
    # NOT real data: 일주기 + 느린 드리프트 + 잡음, 고장 직전 12시간 동안 진동이 증가하는 전조 구간 포함
    rng = np.random.default_rng(seed); n = n_days * 24; t = np.arange(n)
    vib = 1.0 + 0.15 * np.sin(2 * np.pi * (t % 24) / 24) + 0.0005 * t + rng.normal(0, 0.05, n)
    temp = 60 + 3 * np.sin(2 * np.pi * (t % 24) / 24 - 0.5) + rng.normal(0, 0.6, n)
    fault = np.zeros(n, int)
    starts = np.sort(rng.choice(np.arange(72, n - 24), n_faults, replace=False))
    for s0 in starts:
        for k in range(12):
            vib[s0 - 12 + k] += 0.03 * (k + 1); temp[s0 - 12 + k] += 0.15 * (k + 1)
        vib[s0:s0 + 2] += 0.8; fault[s0] = 1
    idx = pd.date_range("2024-01-01", periods=n, freq="h")
    return pd.DataFrame({"vibration": vib, "temp": temp, "fault": fault}, index=idx)

def synthetic_demand(n=1095, seed=SEED + 2):
    rng = np.random.default_rng(seed); t = np.arange(n)
    mu = 500 + 0.15 * t + 40 * np.sin(2 * np.pi * t / 365.25) + 60 * (t % 7 < 5) + rng.normal(0, 12, n)
    return pd.Series(mu, index=pd.date_range("2021-01-01", periods=n, freq="D"), name="demand")

def load_manufacturing(which="sensor"):
    # 달력 시간이 있는 무료 제조 시계열은 드물다(카탈로그 3절). 기본은 합성 자료이며 NOT real data로 표시한다.
    if which == "demand":
        return dict(y=synthetic_demand(), m=7, freq="D", label="일별 제조 수요(합성)", unit="개",
                    kind="SYNTHETIC (NOT real data)")
    df = synthetic_sensor()
    return dict(y=df["vibration"], df=df, m=24, freq="h", label="진동 센서(합성)", unit="mm/s",
                kind="SYNTHETIC (NOT real data)")

D = load_manufacturing("@@WHICH@@")
y, DATA_KIND, M, FREQ = D["y"], D["kind"], D["m"], D["freq"]
print("DATA_KIND:", DATA_KIND); print("관측 수:", len(y), "| 기간:", y.index.min(), "~", y.index.max())
'''

PUBLICPOLICY = r'''
def parse_soda_daily(rows):
    # Socrata SoQL 응답(list of dict: day, n) -> 일별 건수 시계열
    s = pd.Series([float(r["n"]) for r in rows], index=pd.to_datetime([r["day"][:10] for r in rows]))
    s = s.sort_index().asfreq("D")
    if len(s) < 200 or s.isna().mean() > 0.2:
        raise ValueError("관측 부족/결측 과다")
    return s.interpolate()

def synthetic_complaints(n=1000, seed=SEED):
    rng = np.random.default_rng(seed); t = np.arange(n)
    lam = 3000 + 0.8 * t + 400 * (t % 7 < 5) + 300 * np.sin(2 * np.pi * t / 365.25)
    y = rng.negative_binomial(50, 50 / (50 + lam))
    return pd.Series(y.astype(float), index=pd.date_range("2022-01-01", periods=n, freq="D"))

def synthetic_traffic(n_days=365, seed=SEED + 3):
    # NOT real data: 시간별 교통량 (출퇴근 피크, 주말 감소, 기온·강수 영향)
    rng = np.random.default_rng(seed); n = n_days * 24; idx = pd.date_range("2023-01-01", periods=n, freq="h")
    hour, dow = idx.hour.to_numpy(), idx.dayofweek.to_numpy()
    peak = 1800 * np.exp(-0.5 * ((hour - 8) / 1.6) ** 2) + 2100 * np.exp(-0.5 * ((hour - 17.5) / 1.8) ** 2)
    base = 900 + 400 * np.sin(np.pi * np.clip(hour - 5, 0, 18) / 18)
    temp = 12 + 12 * np.sin(2 * np.pi * (np.arange(n) / 24 - 100) / 365) + rng.normal(0, 2, n)
    rain = (rng.random(n) < 0.08).astype(float)
    vol = (base + peak * (dow < 5) + 0.6 * peak * (dow >= 5) * 0.4) * (1 - 0.12 * rain) + 8 * (temp - 12) + rng.normal(0, 90, n)
    return pd.DataFrame({"traffic": np.maximum(vol, 0), "temp": temp, "rain": rain}, index=idx)

def load_policy(which="complaints"):
    if which == "traffic":
        df = synthetic_traffic()
        return dict(y=df["traffic"], df=df, m=24, freq="h", label="시간별 교통량(합성)", unit="대/시",
                    kind="SYNTHETIC (NOT real data): 검증된 무료 교통량 출처를 연결하지 못함")
    s, kind = None, "SYNTHETIC (NOT real data): 음이항 일별 민원 건수"
    if USE_LIVE_DATA:
        try:
            q = {"$select": "date_trunc_ymd(created_date) as day, count(*) as n",
                 "$where": "created_date between '2022-01-01T00:00:00' and '2024-12-31T23:59:59'",
                 "$group": "day", "$order": "day", "$limit": "2000"}
            url = "https://data.cityofnewyork.us/resource/erm2-nwe9.json?" + urllib.parse.urlencode(q)
            s = parse_soda_daily(json.loads(fetch_bytes(url, timeout=120)))
            kind = "REAL: NYC 311 일별 민원 건수 (NYC Open Data, Socrata)"
        except Exception as e:
            print("NYC 311 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:120])
    if s is None:
        s = synthetic_complaints()
    return dict(y=s.rename("requests"), m=7, freq="D", label="일별 민원 건수", unit="건", kind=kind)

D = load_policy("@@WHICH@@")
y, DATA_KIND, M, FREQ = D["y"], D["kind"], D["m"], D["freq"]
print("DATA_KIND:", DATA_KIND); print("관측 수:", len(y), "| 기간:", y.index.min(), "~", y.index.max())
'''

ENERGY = r'''
def parse_openmeteo_daily(obj):
    d = obj["daily"]; idx = pd.to_datetime(d["time"])
    tmax = pd.Series(d["temperature_2m_max"], index=idx, dtype=float)
    tmin = pd.Series(d["temperature_2m_min"], index=idx, dtype=float)
    return ((tmax + tmin) / 2).rename("temp_mid")          # 최고·최저 평균(정의된 일평균 아님)

def parse_openmeteo_pm25(obj):
    h = obj["hourly"]; s = pd.Series(h["pm2_5"], index=pd.to_datetime(h["time"]), dtype=float)
    return s.resample("D").mean().rename("pm2_5")

def parse_daily_min_temp(raw):
    df = pd.read_csv(io.BytesIO(raw)); df.columns = [c.strip().lower() for c in df.columns]
    s = pd.Series(pd.to_numeric(df["temp"], errors="coerce").values, index=pd.to_datetime(df["date"]), name="temp_mid")
    if len(s) < 3000 or not s.dropna().between(-10, 40).all():
        raise ValueError("일 최저기온 길이/범위 이상")
    return s

def synthetic_temp(n=3652, seed=SEED):
    rng = np.random.default_rng(seed); t = np.arange(n)
    return pd.Series(12 + 13 * np.sin(2 * np.pi * (t - 110) / 365.25) + rng.normal(0, 3, n) + 0.0004 * t,
                     index=pd.date_range("2015-01-01", periods=n, freq="D"), name="temp_mid")

def load_energy(which="temp"):
    temp, pm, kind = None, None, "SYNTHETIC (NOT real data)"
    if USE_LIVE_DATA:
        try:
            u = ("https://archive-api.open-meteo.com/v1/archive?latitude=37.57&longitude=126.98"
                 "&start_date=2015-01-01&end_date=2024-12-31&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FSeoul")
            temp = parse_openmeteo_daily(json.loads(fetch_bytes(u, timeout=120)))
            kind = "REAL: Open-Meteo/ERA5 재분석 서울 일 기온 (관측소 실측 아님)"
        except Exception as e:
            print("Open-Meteo 기온 수집 실패 -> 2순위 시도:", type(e).__name__, str(e)[:120])
            try:
                temp = parse_daily_min_temp(fetch_bytes("https://raw.githubusercontent.com/jbrownlee/Datasets/master/daily-min-temperatures.csv", timeout=60))
                kind = "REAL: Melbourne 일 최저기온 1981-1990 (jbrownlee/Datasets; 서울 아님, 일평균 아닌 최저기온)"
            except Exception as e2:
                print("일 최저기온 수집 실패 -> 합성 대체:", type(e2).__name__, str(e2)[:100]); temp = None
        try:
            u = ("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=37.57&longitude=126.98"
                 "&hourly=pm2_5&start_date=2022-09-01&end_date=2024-12-31&timezone=Asia%2FSeoul")
            pm = parse_openmeteo_pm25(json.loads(fetch_bytes(u, timeout=120)))
        except Exception as e:
            print("Open-Meteo 대기질 수집 실패(선택 항목):", type(e).__name__, str(e)[:100])
    if temp is None:
        temp = synthetic_temp()
    temp = temp.asfreq("D").interpolate()
    if which == "demand":
        rng = np.random.default_rng(SEED + 5); t = np.arange(len(temp))
        dow = temp.index.dayofweek.to_numpy()
        dem = 60 + 0.9 * np.abs(temp.to_numpy() - 18) ** 1.15 + 6 * (dow < 5) + 0.004 * t + rng.normal(0, 2.0, len(temp))
        return dict(y=pd.Series(dem, index=temp.index, name="demand"), X=temp.to_frame("temp"), m=7, freq="D",
                    label="일별 전력수요(합성, 기온 의존)", unit="GWh",
                    kind="SYNTHETIC-DERIVED (NOT real data): 수요는 합성, 기온 입력은 " + kind)
    return dict(y=temp, pm=pm, m=365, freq="D", label="일평균 기온", unit="°C", kind=kind)

D = load_energy("@@WHICH@@")
y, DATA_KIND, FREQ = D["y"], D["kind"], D["freq"]
M = D["m"]
print("DATA_KIND:", DATA_KIND); print("관측 수:", len(y), "| 기간:", y.index.min().date(), "~", y.index.max().date())
'''

BUSINESS = r'''
def aggregate_online_retail(df):
    # UCI Online Retail II: 취소 송장(번호가 C로 시작)과 음수 수량을 제외한 일별 매출
    df = df.copy(); df.columns = [str(c).strip() for c in df.columns]
    inv = df["Invoice"].astype(str)
    df = df[~inv.str.startswith("C") & (df["Quantity"] > 0) & (df["Price"] > 0)]
    rev = (df["Quantity"] * df["Price"]).groupby(pd.to_datetime(df["InvoiceDate"]).dt.normalize()).sum()
    s = rev.asfreq("D", fill_value=0.0)
    if len(s) < 200:
        raise ValueError("관측 부족")
    return s

def synthetic_sales(n=730, seed=SEED):
    rng = np.random.default_rng(seed); t = np.arange(n); dow = (t % 7)
    promo = np.zeros(n); 
    for s0 in range(40, n - 7, 60): promo[s0:s0 + 5] = 1.0
    mu = 1000 + 0.6 * t + 150 * np.sin(2 * np.pi * t / 365.25) - 200 * (dow >= 5) + 350 * promo
    return pd.DataFrame({"sales": np.maximum(mu + rng.normal(0, 60, n), 0), "promo": promo},
                        index=pd.date_range("2023-01-01", periods=n, freq="D"))

def load_business(force_synth=False):
    s, kind = None, "SYNTHETIC (NOT real data): 요일·연간 계절성과 프로모션이 있는 일별 매출"
    if USE_LIVE_DATA and not force_synth and ensure("openpyxl"):
        try:
            import zipfile
            z = zipfile.ZipFile(io.BytesIO(fetch_bytes("https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip", timeout=180)))
            name = [n for n in z.namelist() if n.lower().endswith(".xlsx")][0]
            sheets = pd.read_excel(io.BytesIO(z.read(name)), sheet_name=None)
            s = aggregate_online_retail(pd.concat(sheets.values(), ignore_index=True))
            kind = "REAL: UCI Online Retail II 일별 매출 (CC BY 4.0, 취소 송장 제외)"
        except Exception as e:
            print("Online Retail II 수집 실패 -> 합성 대체:", type(e).__name__, str(e)[:120])
    if s is not None:
        return dict(y=s.rename("sales"), m=7, freq="D", label="일별 매출", unit="GBP", kind=kind)
    df = synthetic_sales()
    return dict(y=df["sales"], df=df, m=7, freq="D", label="일별 매출(합성)", unit="원", kind=kind)

D = load_business(@@FORCE@@)
y, DATA_KIND, M, FREQ = D["y"], D["kind"], D["m"], D["freq"]
print("DATA_KIND:", DATA_KIND); print("관측 수:", len(y), "| 기간:", y.index.min().date(), "~", y.index.max().date())
'''

LOADERS = {"Finance": FINANCE, "RealEstate": REALESTATE, "Manufacturing": MANUFACTURING,
           "PublicPolicy": PUBLICPOLICY, "EnergyEnvironment": ENERGY, "BusinessMarketing": BUSINESS}

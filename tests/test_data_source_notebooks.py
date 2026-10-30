"""data_sources 노트북 오프라인 검증: 코드 셀 컴파일, 파서 모의 테스트, 키 문자열 부재.
네트워크 없이 실행되며, 온라인 로더 자체의 동작은 검증하지 않는다."""
import io, json, glob, os, ast, re
import matplotlib
matplotlib.use("Agg")

ROOT = os.path.dirname(os.path.dirname(__file__))
NBS = sorted(glob.glob(os.path.join(ROOT, "data_sources", "*.ipynb")))

def load(path):
    return json.load(open(path, encoding="utf-8"))

def code_cells(nb):
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]

def test_six_notebooks():
    assert len(NBS) == 6

def test_code_compiles_and_no_keys():
    for p in NBS:
        for src in code_cells(load(p)):
            ast.parse(src)
            assert not re.search(r"(api[_-]?key|apikey)\s*=\s*['\"][A-Za-z0-9]{8,}", src, re.I)

def test_fallback_runs_offline(monkeypatch):
    """네트워크 차단 상태에서 모든 노트북이 합성 대체로 끝까지 실행되고 DATA_KIND를 표시한다."""
    import urllib.request
    def boom(*a, **k): raise OSError("offline")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    for p in NBS:
        ns = {}
        for src in code_cells(load(p)):
            exec(compile(src, p, "exec"), ns)
        assert "SYNTHETIC" in str(ns.get("DATA_KIND")), p

def _parsers(name):
    p = [x for x in NBS if name in x][0]
    nb = load(p)
    ns = {}
    exec(compile(code_cells(nb)[0], p, "exec"), ns)          # 공통 헬퍼
    for c in nb["cells"]:
        if c["cell_type"] == "code" and "parsers" in c["metadata"].get("tags", []):
            exec("".join(c["source"]), ns)
    return ns

def test_fred_headers():
    ns = _parsers("01_Finance")
    for h in ("DATE", "observation_date"):
        s = ns["parse_fred_csv"](f"{h},DGS10\n2024-01-02,3.95\n2024-01-03,.\n2024-01-04,4.01\n")
        assert len(s) == 3 and s.isna().sum() == 1

def test_noaa_missing():
    ns = _parsers("05_Energy")
    txt = "# comment\n# comment\nyear,month,decimal date,average,deseasonalized\n1958,3,1958.2,315.7,314.4\n1958,4,1958.3,-99.99,-99.99\n"
    s = ns["parse_noaa_co2"](txt)
    assert len(s) == 2 and s.isna().sum() == 1

def test_prop99_semicolon():
    ns = _parsers("04_Public")
    df = ns["parse_prop99"]("State;Year;PacksPerCapita;treated\nCalifornia;1989;82.4;1\nUtah;1989;90.1;0\n")
    assert list(df.columns) == ["State", "Year", "PacksPerCapita", "treated"] and len(df) == 2

def test_openmeteo_and_wikimedia():
    ns = _parsers("05_Energy")
    s = ns["parse_openmeteo_daily"]({"daily": {"time": ["2024-01-01", "2024-01-02"], "temperature_2m_max": [4, 6], "temperature_2m_min": [-2, 0]}})
    assert list(s.values) == [1.0, 3.0]
    ns = _parsers("06_Business")
    s = ns["parse_wikimedia_pageviews"]({"items": [{"timestamp": "2023010100", "views": 10}, {"timestamp": "2023010200", "views": 12}]})
    assert list(s.values) == [10, 12]


# ---- 학생 예제에서 이식한 로더 (추가) ----
def test_noaa_co2_any_csv_and_txt():
    ns = _parsers("05_Energy")
    csv = ("# c\n# c\nyear,month,decimal date,average,deseasonalized,ndays,sdev,unc\n"
           "1958,3,1958.2,315.71,314.4,-1,-9.99,-0.99\n1958,4,1958.3,-99.99,-99.99,-1,-9.99,-0.99\n1958,5,1958.4,317.51,315.0,-1,-9.99,-0.99\n")
    txt = ("# c\n# c\n1958   3    1958.2  315.71   314.44     -1     -9.99     -0.99\n"
           "1958   4    1958.3  -99.99   -99.99     -1     -9.99     -0.99\n"
           "1958   5    1958.4  317.51   315.00     -1     -9.99     -0.99\n")
    for raw in (csv, txt, txt.encode()):
        s = ns["parse_noaa_co2_any"](raw)
        assert len(s) == 3 and s.isna().sum() == 1 and abs(s.iloc[0] - 315.71) < 1e-9


def test_co2_range_check_rejects_missing_code():
    ns = _parsers("05_Energy")
    import pandas as pd, pytest
    bad = pd.Series([-99.99] * 700, index=pd.date_range("1958-03-01", periods=700, freq="MS"))
    with pytest.raises(AssertionError):
        ns["check_co2"](bad)


def test_daily_min_temp_and_tides():
    ns = _parsers("05_Energy")
    s = ns["parse_daily_min_temp"]("Date,Temp\n1981-01-01,20.7\n1981-01-02,17.9\n1981-01-03,?\n")
    assert len(s) == 3 and s.isna().sum() == 1
    js = {"metadata": {}, "data": [{"t": "2023-01-01 00:00", "v": "2.801", "s": "0.010", "f": "0,0,0,0", "q": "v"},
                                    {"t": "2023-01-01 01:00", "v": "", "s": "", "f": "", "q": "v"}]}
    t = ns["parse_tides_json"](js)
    assert len(t) == 2 and t.isna().sum() == 1
    import pytest
    with pytest.raises(ValueError):
        ns["parse_tides_json"]({"error": {"message": "No data"}})


def test_macro_panel_inflation_after_monthly_alignment():
    ns = _parsers("01_Finance")
    import pandas as pd, numpy as np
    idx = pd.date_range("2000-01-01", periods=30, freq="MS")
    cpi = pd.Series(100 * 1.002 ** np.arange(30), idx)
    m = ns["build_macro_panel"]({"FEDFUNDS": pd.Series(1.0, idx), "UNRATE": pd.Series(5.0, idx), "CPI": cpi})
    assert m["INFL_YOY"].iloc[:12].isna().all() and abs(m["INFL_YOY"].iloc[12] - (1.002 ** 12 - 1) * 100) < 1e-9
    ns["check_macro"](m)


def test_airline_embedded():
    p = [x for x in NBS if "06_Business" in x][0]
    ns = {}
    for src in code_cells(load(p)):
        exec(compile(src, p, "exec"), ns)
    a = ns["air"]
    assert len(a) == 144 and a.iloc[0] == 112 and a.iloc[-1] == 432 and a.idxmax().year == 1960


def test_gold_csv_in_repo_is_used():
    import os
    p = [x for x in NBS if "01_Finance" in x][0]
    cwd = os.getcwd(); os.chdir(ROOT)
    try:
        ns = {}
        for src in code_cells(load(p)):
            exec(compile(src, p, "exec"), ns)
    finally:
        os.chdir(cwd)
    g = ns["gold"]
    assert ns["KIND_GOLD"].startswith("REAL(file)") and len(g) == 2510 and str(g.index[0].date()) == "2016-02-05"


# ---- 제조 소형 공개 자료 로더 (모의 입력) ----
def test_mfg_parsers():
    import numpy as np, pandas as pd, pytest
    ns = _parsers("03_Manufacturing")
    # AI4I: 열 이름 정규화, 고장유형 열 보존, 짧은 표 거부
    ai = ns["synthetic_ai4i"]()
    raw = ai.rename(columns={"air_temperature": "Air temperature [K]", "machine_failure": "Machine failure", "tool_wear": "Tool wear [min]",
                             "process_temperature": "Process temperature [K]", "rotational_speed": "Rotational speed [rpm]",
                             "torque": "Torque [Nm]", "type": "Type", "twf": "TWF", "hdf": "HDF", "pwf": "PWF", "osf": "OSF", "rnf": "RNF"})
    out = ns["parse_ai4i"](raw)
    assert "machine_failure" in out and "hdf" in out and 0.01 < out["machine_failure"].mean() < 0.12
    with pytest.raises(ValueError):
        ns["parse_ai4i"](raw.head(100))
    # C-MAPSS: 26열, RUL 계산
    rows = []
    for u in (1, 2):
        for c in range(1, 4):
            rows.append(" ".join([str(u), str(c)] + ["0.1"] * 24))
    with pytest.raises(ValueError):                       # 엔진 수 부족
        ns["parse_cmapss_train"]("\n".join(rows) + "\n")
    cm = ns["synthetic_cmapss"]()
    assert cm["unit"].nunique() == 100 and (cm.groupby("unit")["rul"].min() == 0).all()
    txt = "\n".join(" ".join(map(str, [r.unit, r.cycle] + [r[f"op{i}"] for i in (1, 2, 3)] + [r[f"s{i}"] for i in range(1, 22)]))
                    for _, r in cm.head(500).iterrows())
    # 500행에는 엔진이 적어 거부되는 것이 정상, 전체는 통과해야 한다
    with pytest.raises(ValueError):
        ns["parse_cmapss_train"](txt)
    full = "\n".join(" ".join(map(str, row)) for row in cm.drop(columns="rul").itertuples(index=False))
    assert ns["parse_cmapss_train"](full).shape[1] == 27
    # SECOM: 라벨/타임스탬프
    data = "1.0 NaN 3.0\n4.0 5.0 NaN\n"
    labs = "-1 19/07/2008 11:55:00\n1 19/07/2008 12:32:00\n"
    X, y = ns["parse_secom"](data, labs)
    assert X.shape == (2, 3) and list(y) == [0, 1] and X.index[0].month == 7 and X.isna().sum().sum() == 2
    with pytest.raises(ValueError):
        ns["parse_secom"](data, "-1 a b\n")
    # Steel: 결함 지시열 -> 클래스
    cols = {f"x{i}": np.random.rand(1600) for i in range(27)}
    st = pd.DataFrame(cols)
    for k, c in enumerate(ns["STEEL_CLASSES"]):
        st[c] = (np.arange(1600) % 7 == k).astype(int)
    Xs, ys = ns["parse_steel"](st)
    assert Xs.shape == (1600, 27) and ys.nunique() == 7


def test_cwru_parser_and_bearing_features():
    import io, numpy as np
    from scipy.io import savemat
    ns = _parsers("03_Manufacturing")
    buf = io.BytesIO(); savemat(buf, {"X097_DE_time": np.random.randn(1000, 1), "X097RPM": np.array([[1797]])})
    assert ns["parse_cwru_mat"](buf.getvalue()).shape == (1000,)
    import pytest
    buf2 = io.BytesIO(); savemat(buf2, {"foo": np.zeros((3, 1))})
    with pytest.raises(ValueError):
        ns["parse_cwru_mat"](buf2.getvalue())
    f0 = ns["bearing_features"](ns["synthetic_bearing"](fault_hz=0.0)); f1 = ns["bearing_features"](ns["synthetic_bearing"](fault_hz=105.0))
    assert f1["kurtosis"] > f0["kurtosis"] + 1       # 충격이 있으면 첨도가 커진다 (합성 확인)

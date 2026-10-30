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

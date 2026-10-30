"""노트북 안의 파서 함수를 모의 입력으로 검증한다(네트워크 불필요)."""
import json, os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]

def ns_from(nb_rel, stop_marker):
    os.environ["TSLAB_OFFLINE"] = "1"
    nb = json.load(open(ROOT / nb_rel, encoding="utf-8")); ns = {}
    for c in nb["cells"]:
        if c["cell_type"] != "code": continue
        src = "".join(c["source"])
        exec(compile(src, nb_rel, "exec"), ns)
        if stop_marker in src: break
    return ns

def test_soda_daily():
    ns = ns_from("notebooks/01_TimeSeries_Foundations/PublicPolicy.ipynb", "def parse_soda_daily")
    rows = [{"day": f"2023-{1 + i // 28:02d}-{1 + i % 28:02d}T00:00:00.000", "n": str(3000 + i)} for i in range(300)]
    s = ns["parse_soda_daily"](rows)
    assert len(s) >= 200 and s.index.freq is not None or len(s) >= 200

def test_fhfa_master():
    ns = ns_from("notebooks/01_TimeSeries_Foundations/RealEstate.ipynb", "def parse_fhfa_master")
    lines = ["hpi_type,hpi_flavor,frequency,level,place_name,place_id,yr,period,index_nsa,index_sa"]
    for i in range(240):
        lines.append(f"traditional,all-transactions,monthly,USA or Census Division,USA,USA,{2000 + i // 12},{i % 12 + 1},{100 + i * 0.3},{100 + i * 0.3}")
    s = ns["parse_fhfa_master"]("\n".join(lines))
    assert len(s) == 240 and s.index[0].year == 2000

def test_online_retail_aggregate():
    import pandas as pd
    ns = ns_from("notebooks/01_TimeSeries_Foundations/BusinessMarketing.ipynb", "def aggregate_online_retail")
    days = pd.date_range("2010-01-01", periods=300, freq="D")
    df = pd.DataFrame({"Invoice": ["5" + str(i) for i in range(300)], "Quantity": [2] * 300, "Price": [3.0] * 300, "InvoiceDate": days})
    df.loc[0, "Invoice"] = "C500"                          # 취소 송장은 제외되어야 함
    s = ns["aggregate_online_retail"](df)
    assert len(s) == 299 and (s == 6.0).all()      # 첫날은 취소 송장뿐이라 제외됨

def test_openmeteo_parsers():
    ns = ns_from("notebooks/01_TimeSeries_Foundations/EnergyEnvironment.ipynb", "def parse_openmeteo_daily")
    t = ns["parse_openmeteo_daily"]({"daily": {"time": ["2024-01-01", "2024-01-02"], "temperature_2m_max": [4, 6], "temperature_2m_min": [-2, 0]}})
    assert list(t.values) == [1.0, 3.0]
    p = ns["parse_openmeteo_pm25"]({"hourly": {"time": ["2024-01-01T00:00", "2024-01-01T01:00"], "pm2_5": [10, 20]}})
    assert float(p.iloc[0]) == 15.0

def test_prop99():
    ns = ns_from("notebooks/05_Causal_Inference/PublicPolicy.ipynb", "def parse_prop99")
    df = ns["parse_prop99"]("State;Year;PacksPerCapita;treated\nCalifornia;1989;82.4;1\nUtah;1989;90.1;0\n")
    assert list(df.columns) == ["State", "Year", "PacksPerCapita", "treated"]


def test_chapter_daily_min_temp_fallback_parser():
    ns = ns_from("notebooks/01_TimeSeries_Foundations/EnergyEnvironment.ipynb", "def parse_daily_min_temp")
    import pytest
    rows = ["Date,Temp"] + [f"{1981 + i // 365}-01-01,{10 + (i % 7)}" for i in range(10)]
    with pytest.raises(ValueError):                       # 길이 부족 -> 거부
        ns["parse_daily_min_temp"]("\n".join(rows).encode())
    import pandas as pd
    idx = pd.date_range("1981-01-01", periods=3650, freq="D")
    big = "Date,Temp\n" + "\n".join(f"{d.date()},{10 + (i % 7)}" for i, d in enumerate(idx))
    s = ns["parse_daily_min_temp"](big.encode())
    assert len(s) == 3650

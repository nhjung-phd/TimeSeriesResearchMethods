"""48개 챕터 노트북을 네트워크 없이(합성 대체 경로) 끝까지 실행한다. statsmodels 등 필수 패키지가 없으면 건너뛴다.
온라인 로더의 실제 성공 여부는 이 테스트가 보장하지 않는다(CI에 네트워크가 있어도 TSLAB_OFFLINE=1로 합성 경로만 검증)."""
import importlib.util, os, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
NBS = sorted((ROOT / "notebooks").rglob("*.ipynb"))
need = ["statsmodels", "sklearn", "scipy", "pandas", "matplotlib"]
missing = [m for m in need if importlib.util.find_spec(m) is None]

@pytest.mark.skipif(bool(missing), reason=f"필수 패키지 없음: {missing}")
@pytest.mark.parametrize("path", NBS, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_notebook_runs_offline(path, monkeypatch):
    monkeypatch.setenv("TSLAB_OFFLINE", "1")
    import matplotlib; matplotlib.use("Agg")
    import run_notebooks
    err = run_notebooks.run(str(path))
    assert err is None, err

"""노트북 코드 셀을 순서대로 실행한다(nbclient 불필요). 네트워크 없이 합성 대체 경로를 검증하는 용도.
사용: TSLAB_OFFLINE=1 python tools/run_notebooks.py [노트북 경로 ...]   (인자 없으면 notebooks/ 전체)"""
import json, os, sys, time, traceback
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
ROOT = Path(__file__).resolve().parents[1]

def run(path):
    nb = json.load(open(path, encoding="utf-8"))
    ns = {"__name__": "__main__"}
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        try:
            exec(compile(src, f"{Path(path).name}#cell{i}", "exec"), ns)
        except Exception:
            return f"cell {i}: " + traceback.format_exc(limit=3)
        finally:
            import matplotlib.pyplot as plt; plt.close("all")
    return None

if __name__ == "__main__":
    os.environ.setdefault("TSLAB_OFFLINE", "1")
    paths = [str(Path(a).resolve()) for a in sys.argv[1:]] or sorted(str(p) for p in (ROOT / "notebooks").rglob("*.ipynb"))
    bad = 0
    for p in paths:
        t = time.time(); err = run(p)
        print(("FAIL " if err else "ok   ") + str(Path(p).relative_to(ROOT)) + f"  {time.time()-t:.1f}s")
        if err: bad += 1; print(err)
    sys.exit(1 if bad else 0)

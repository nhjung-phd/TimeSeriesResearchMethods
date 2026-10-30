"""48개 챕터×도메인 실습 노트북 생성기.
사용: python tools/build_notebooks.py [--chapters 1 2 ...]
노트북 코드는 tools/nbgen/*.py 의 문자열에서 만들어진다. 노트북을 고치려면 여기 소스를 고치고 다시 생성한다."""
import json, sys, uuid, importlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

CHAPTER_DIRS = {1: "01_TimeSeries_Foundations", 2: "02_Statistical_Forecasting", 3: "03_Machine_Deep_Learning",
                4: "04_Foundation_Models", 5: "05_Causal_Inference", 6: "06_Panel_Data_Analysis",
                7: "07_Validation_Robustness", 8: "08_Research_Integration"}
DOMAINS = ["Finance", "RealEstate", "Manufacturing", "PublicPolicy", "EnergyEnvironment", "BusinessMarketing"]
KO = {"Finance": "금융·투자", "RealEstate": "부동산", "Manufacturing": "제조·품질", "PublicPolicy": "공공정책",
      "EnergyEnvironment": "에너지·환경", "BusinessMarketing": "경영·마케팅"}
TITLES = json.load(open(ROOT / "tools" / "assignment_titles.json", encoding="utf-8"))
from nbgen.questions import QUESTIONS

def to_nb(cells, name):
    out = []
    for kind, text in cells:
        src = text.splitlines(True)
        if kind == "md":
            out.append({"cell_type": "markdown", "id": uuid.uuid4().hex[:8], "metadata": {}, "source": src})
        else:
            out.append({"cell_type": "code", "execution_count": None, "id": uuid.uuid4().hex[:8],
                        "metadata": {}, "outputs": [], "source": src})
    return {"cells": out, "metadata": {"colab": {"name": name, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}

def main(chapters):
    for ch in chapters:
        mod = importlib.import_module(f"nbgen.ch{ch}")
        for dom in DOMAINS:
            title = TITLES[f"{ch:02d}"][DOMAINS.index(dom)][1]
            q = QUESTIONS[(ch, dom)]
            cells = mod.build(dom, title, q)
            p = ROOT / "notebooks" / CHAPTER_DIRS[ch] / f"{dom}.ipynb"
            nb = to_nb(cells, f"{dom}.ipynb")
            p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print("wrote", p.relative_to(ROOT), len(cells), "cells")

if __name__ == "__main__":
    args = [int(a) for a in sys.argv[2:]] if len(sys.argv) > 2 and sys.argv[1] == "--chapters" else list(range(1, 9))
    main(args)

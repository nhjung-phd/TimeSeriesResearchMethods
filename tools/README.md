# tools

- `build_notebooks.py`: `notebooks/` 48개 노트북을 `tools/nbgen/` 소스에서 생성합니다. `python tools/build_notebooks.py [--chapters 1 2 ...]`
- `run_notebooks.py`: 노트북 코드 셀을 순서대로 실행합니다(nbclient 불필요). `TSLAB_OFFLINE=1 python tools/run_notebooks.py [경로...]`
- `nbgen/common.py`: 공통 설정·지표·OLS(HC1/HAC/군집)·패널 생성기. `nbgen/data_cells.py`: 도메인별 데이터 로더(온라인 → 합성 대체). `nbgen/chN.py`: 챕터별 본문.

노트북을 고칠 때는 이 소스를 수정한 뒤 다시 생성하세요. 노트북 파일을 직접 고치면 다음 생성 때 덮어쓰입니다.
- `gen_data_sources.py`: `data_sources/` 6개 노트북을 생성합니다(`python tools/gen_data_sources.py`). 학생 예제에서 이식한 로더 셀은 `data_source_extras.py`에 있고, 항공 승객 내장 데이터는 `_airline.csv`입니다.

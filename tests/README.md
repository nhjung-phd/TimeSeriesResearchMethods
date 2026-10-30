# Testing

- `test_notebooks.py`: 노트북 구조(nbformat) 검증.
- `test_run_notebooks.py`: 48개 챕터 노트북을 **네트워크 없이 합성 대체 경로로** 끝까지 실행합니다(`TSLAB_OFFLINE=1`). statsmodels 등이 필요합니다.
- `test_data_parsers.py`: 노트북 내 파서(NYC 311, FHFA, Online Retail II, Open-Meteo, Prop 99)를 모의 입력으로 검증합니다.
- `test_data_source_notebooks.py`: `data_sources/` 입문 노트북 검증.

**검증하지 않는 것:** 온라인 로더가 실제 서버에서 성공하는지(스키마 변경 포함), Colab 환경에서의 동작, 사전학습 모델(Chronos) 호출.
노트북은 `python tools/build_notebooks.py`로 재생성합니다(소스: `tools/nbgen/`). 직접 수정 시 다음 재생성에서 덮어쓰이므로 소스를 고치세요.

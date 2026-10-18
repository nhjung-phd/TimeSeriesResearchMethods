# Domain Data Source Catalog

| 분야 | 출처 | 접근 | 기본 관측 단위 | 주의사항 |
|---|---|---|---|---|
| 금융 | [Yahoo Finance](https://finance.yahoo.com/), [FRED](https://fred.stlouisfed.org/) | yfinance / FRED API·CSV | 일·월 | 가격 조정, 비공식 접근 및 재배포 조건, 발표 시점 |
| 부동산 | [공공데이터포털](https://www.data.go.kr/), [국토부 실거래](https://rt.molit.go.kr/) | API 키 / CSV | 거래→월별 집계 | 품질·면적 구성 변화, 지역코드 |
| 제조 | [UCI](https://archive.ics.uci.edu/), [AI Hub](https://www.aihub.or.kr/) | 다운로드 | 센서시각·설비 | 실제 타임스탬프 있는 자료인지 확인 |
| 공공정책 | [KOSIS](https://kosis.kr/), [공공데이터포털](https://www.data.go.kr/) | API 키 / CSV | 지역×월 | 정책시점·지표 개정·단위 |
| 에너지·환경 | [기상자료개방포털](https://data.kma.go.kr/), [전력거래소](https://www.kpx.or.kr/) | 신청 / CSV | 시간·일·월 | 관측시간대·주기·결측 |
| 경영·마케팅 | [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) | Excel/CSV | 거래→일별 집계 | 반품/취소·개인정보·데이터 라이선스 |

**실행 예제 정책:** 별도 API 키가 없는 기본 노트북은 작은 합성 데이터를 제공하고 `data_sources/`에서 공개데이터 수집 절차를 설명합니다. 실제 원자료의 라이선스 확인 전 GitHub 재배포 금지.

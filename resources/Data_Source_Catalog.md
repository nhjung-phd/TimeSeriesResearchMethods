# Domain Data Source Catalog (무료·공개 시계열 데이터)

실습용으로 쓸 수 있는 무료 출처를 도메인별로 정리했습니다. **검증 상태**는 아래 기준입니다.

- **A (페이지 확인)**: 작성자가 출처 페이지에서 데이터셋 존재·형식·라이선스 문구를 확인함. 단, 노트북 로더를 Colab에서 끝까지 실행해 본 것은 아닙니다.
- **B (부분 확인)**: 출처 존재는 확인했으나 URL 경로, 열 이름, 라이선스, 이용약관 중 일부가 확인되지 않음. 수업 전 직접 열어보세요.
- **C (확인 필요)**: 이 저장소 작성 환경에서 페이지를 열지 못했거나 조건이 불명확함. 사용 전 반드시 확인.

접근 유형: **무키** = 인증 없이 요청 / **무료키** = 무료 가입 후 키 발급 / **신청** = 승인·로그인 필요 / **수동** = 웹에서 직접 내려받기.

> API 키를 파일·노트북·커밋에 넣지 마세요. `getpass.getpass()` 또는 환경변수(`os.environ`)만 사용합니다.
> 원자료는 라이선스 확인 전 이 저장소에 재배포하지 않습니다. `data/`에는 합성자료와 README만 둡니다.
> 표의 라이선스는 해당 페이지에서 본 문구이며 법률 자문이 아닙니다. 출판 전 원 약관을 다시 확인하세요.

## 1. 금융·투자

| 출처 | 접근 | 내용·주기 | 라이선스/조건 | 검증 | 비고 |
|---|---|---|---|---|---|
| Yahoo Finance via `yfinance` | 무키 (비공식) | 주가·ETF·환율 일/주/월 | 비공식 접근, Yahoo 약관 확인 필요 | B | 기존 `Finance.ipynb` 방식. 접근이 막힐 수 있어 합성 대체 유지 |
| FRED `fredgraph.csv` | 무키 | 금리·VIX·거시 일/월/분기 | 시리즈별 출처 조건 상이 | B | 헤더가 `DATE` 또는 `observation_date`일 수 있어 로더가 둘 다 처리. 엔드포인트 동작은 수업 전 확인 |
| FRED API | 무료키 | 위와 동일 + 빈티지(발표시점) | FRED 약관 | C | 실시간 빈티지 실습 시 사용 |
| 한국은행 ECOS | 무료키 | 금리·물가·환율 등 | 확인 필요 | C | 키 발급 후 사용. 코드·URL 형식은 공식 문서 확인 |
| Ken French Data Library | 수동 CSV | 팩터·산업포트폴리오 일/월 | 인용 요청 여부 확인 필요 | C | 작성 환경에서 페이지 열람 실패 |

## 2. 부동산

| 출처 | 접근 | 내용·주기 | 라이선스/조건 | 검증 | 비고 |
|---|---|---|---|---|---|
| FHFA House Price Index (`hpi_master`, `hpi_at_state`, `hpi_at_metro` 등 CSV) | 무키 | 미국 주택가격지수 월/분기 | 다운로드 페이지에 별도 약관 문구 없음 (확인 필요) | A (파일명) / B (전체 URL) | 지역 패널 → Ch.5 패널·DID 실습 가능 |
| 한국부동산원 R-ONE | 신청/무료키 | 매매·전세가격지수 월/주 | 확인 필요 | C | 국내 실습용 후보 |
| 국토교통부 실거래가 (공공데이터포털) | 무료키 | 거래 단위 → 월 집계 | 이용허락범위 확인 필요 | C | 면적·단지 구성 변화 주의 |
| Zillow Research Data | 수동 CSV | 미국 주택가격지수 | 확인 필요 | C | 약관 확인 후 사용 |

## 3. 제조·품질

제조 도메인은 **달력 시간이 있는 무료 자료가 가장 빈약**합니다. 아래는 후보이며, 어느 것도 이 저장소에서 내려받아 검증하지 않았습니다.

| 출처 | 접근 | 내용·주기 | 라이선스/조건 | 검증 | 비고 |
|---|---|---|---|---|---|
| UCI SECOM (id 179) | 수동/`ucimlrepo` | 반도체 공정 센서 + 합불 라벨 | 확인 필요 | C | 타임스탬프 제공 여부·형식 직접 확인 필요 |
| NASA C-MAPSS / PHM08 | 수동 | 엔진 열화 시뮬레이션 (사이클 단위) | 라이선스 불명확, 저장소 URL 변경 이력 | C | 달력 시간이 아니라 사이클 지표. 생존·열화 실습용 |
| UCI Steel Industry Energy | 수동 | 설비 전력 15분 | 확인 필요 | C | 에너지 도메인과 겹침 |
| 합성 공정 시계열 (`data/synthetic`) | 내장 | 관리도·변화점 실습 | 해당 없음 | — | 실제 자료가 아님. 노트북에서 `NOT real data`로 표시 |

## 4. 공공정책

| 출처 | 접근 | 내용·주기 | 라이선스/조건 | 검증 | 비고 |
|---|---|---|---|---|---|
| California Proposition 99 (`synthdid` 저장소 `california_prop99.csv`) | 무키 (GitHub raw) | 주×연도 1인당 담배 판매, 처치 표시 | 저장소 라이선스 확인 필요 | A (열 구성) / B (라이선스) | 구분자 `;`. 열: State, Year, PacksPerCapita, treated. Ch.7 SCM·DID 대표 사례 |
| World Bank API v2 | 무키 | 국가×연도 지표 | 지표별 조건 (대체로 CC BY 4.0, 확인 필요) | A | 정책 전후 비교 · 패널 |
| NYC 311 (Socrata, `erm2-nwe9`) | 무키 (제한 있음) | 민원 건수 일/주 | NYC Open Data 약관 | A | 건수 자료 → Ch.6 포아송/ITS |
| KOSIS | 무료키 | 국내 통계 | 확인 필요 | C | 통계표 ID·분류코드 직접 확인 |
| 공공데이터포털 (data.go.kr) | 무료키 | 부처별 API | 데이터별 이용허락 | C | 서비스별 승인 절차 |
| 서울 열린데이터광장 | 무료키 | 서울시 통계 | 데이터별 | C | |

## 5. 에너지·환경

| 출처 | 접근 | 내용·주기 | 라이선스/조건 | 검증 | 비고 |
|---|---|---|---|---|---|
| NOAA GML Mauna Loa CO₂ (`co2_mm_mlo.csv`) | 무키 | 월별 CO₂ 1958~ | NOAA 공개 자료 (인용 권장) | A | `#` 주석 행, 결측 −99.99 처리 필요. 추세·계절성 교과서 사례 |
| Open-Meteo Historical Weather (`archive-api.open-meteo.com/v1/archive`) | 무키 | 격자 기반 재분석 일/시간, 1940~ | 비상업 무료, CC BY 4.0, 호출 제한 있음 | A | 관측소 값이 아닌 재분석(ERA5)임을 명시. 일평균 변수명은 응답으로 확인 |
| Open-Meteo Air Quality (`air-quality-api.open-meteo.com/v1/air-quality`) | 무키 | PM10/PM2.5 시간. 유럽 재분석 2013~, 글로벌 예측 2022-08~ | 비상업 무료 | A | 한국 지점은 글로벌 모델(0.4°, 3시간)이라 해상도가 낮음. 예측 자료는 실측이 아님 |
| Open Power System Data `time_series` | 무키 | 유럽 전력 부하·발전 시간 | 파일 라이선스 확인 필요 | B | 버전 날짜 경로 확인 필요 |
| UCI Individual Household Electric Power (id 235) | 수동 | 가구 전력 1분 | CC BY 4.0 | A | 대용량. 일/시간 집계 권장 |
| `statsmodels` 내장 (co2, sunspots, macrodata, nile) | 내장 | 교육용 | 패키지 포함 | A | 네트워크 불필요한 최후 대체 |
| 기상자료개방포털 (KMA) | 무료키/신청 | 국내 관측 | 확인 필요 | C | |
| AirKorea | 무료키 | 국내 대기질 | 확인 필요 | C | |

## 6. 경영·마케팅

| 출처 | 접근 | 내용·주기 | 라이선스/조건 | 검증 | 비고 |
|---|---|---|---|---|---|
| UCI Online Retail II (id 502) | 수동 (`openpyxl`) | 영국 소매 거래 2009–2011 | CC BY 4.0 | A | 취소·반품 행 처리 필요 |
| UCI Bike Sharing (id 275) | 수동 | 일/시간 대여량 + 기상 | CC BY 4.0 | A | 건수 시계열 · 외생변수 |
| Wikimedia Pageviews REST API | 무키 (User-Agent 권장) | 문서별 일 조회수 | Wikimedia 약관 | A | 관심도 대리변수 |
| Google Trends (`pytrends`) | 비공식 | 검색관심도 | 비공식, 약관 확인 필요 | C | 안정성 낮아 권장하지 않음 |

## 7. 챕터 × 도메인 권장 데이터 (실습 과제 48개용)

괄호는 **권장 후보**이며 "해당 방법에 맞는 구조를 가졌을 가능성이 높은 자료"입니다. 실제 적합성은 노트북에서 점검해야 합니다.

| 챕터 | 금융 | 부동산 | 제조 | 공공정책 | 에너지·환경 | 경영·마케팅 |
|---|---|---|---|---|---|---|
| 1 기초·정상성 | FRED/yfinance | FHFA (전국) | 합성 공정 | World Bank | NOAA CO₂ | Online Retail 일 매출 |
| 2 ARIMA | FRED 금리 | FHFA 월 | 합성 | World Bank | NOAA CO₂ | Bike Sharing 일 |
| 3 계절·분해 | FRED 월 | FHFA | 합성 | NYC 311 주별 | NOAA CO₂, Open-Meteo | Online Retail |
| 4 변동성·GARCH | yfinance 수익률 | — (부적합) | — | — | 전력 가격 확인 필요 | — |
| 5 패널·다변량 | FRED 다변량 | FHFA 주(state) 패널 | — | Prop 99 / World Bank | Open-Meteo 다지점 | — |
| 6 건수·GLM | — | — | 합성 불량 건수 | NYC 311 | — | Bike Sharing 건수 |
| 7 인과·정책평가 | 이벤트 연구(수익률) | FHFA 지역 비교 | — | **Prop 99 (SCM·DID)** | Open-Meteo | Wikimedia (개입일 필요) |
| 8 ML·평가 | yfinance | FHFA | SECOM(확인 필요) | — | UCI Household Power | Bike Sharing |

"—"는 해당 방법을 무료 공개자료로 실습하기에 적합한 자료를 확인하지 못했다는 뜻이며, 합성자료를 쓰고 합성임을 표시합니다.

## 8. 실행 정책

1. 모든 `data_sources` 노트북은 온라인 로더를 `try/except`와 timeout으로 감싸고, 실패하면 합성자료로 대체하며 `DATA_KIND`를 출력합니다.
2. 합성자료로 얻은 추정치는 **방법 시연**이며 실제 현상에 대한 증거가 아닙니다.
3. 수업 전 점검: 각 노트북을 Colab에서 실행해 `DATA_KIND == 'REAL'`인지 확인하고, 이 카탈로그의 검증 상태를 갱신하세요.

## 9. 학생 예제(Example 01~07)에서 편입한 소스

학생 제출 노트북에 저장된 실행 출력으로 "그 시점에는 로드됨"을 확인했다(실행 날짜 미상, 현재 동작은 Colab 재실행 필요). 편입 코드는 `data_sources/` 노트북의 "추가" 셀과 `tools/data_source_extras.py`에 있다.

| 소스 | 편입 위치 | 등급 | 비고 |
|---|---|---|---|
| FRED FEDFUNDS·UNRATE·CPIAUCSL (`fredgraph.csv`) | 01 Finance 추가 A | B | 원 예제는 `pandas_datareader`. 물가상승률은 월 정렬 후 계산하도록 수정 |
| 금 일별 가격 (`data/finance/gold_historical_data.csv`, 저장소 포함) | 01 Finance 추가 B | C | 출처·라이선스 미표기(GC=F 계열 추정, 확인 필요). 파일 → yfinance → 합성 순 |
| NOAA CO₂ csv/txt 다중 URL | 05 Energy 추가 C | B | 평균열 결측 −99.99. 원 예제 04번의 결측 치환 코드는 평균열에 해당 안 됨(확인 필요) |
| Melbourne 일 최저기온 1981–1990 (jbrownlee/Datasets) | 05 추가 C, 챕터 Energy 2순위 대체 | B | 개인 저장소: 영구성 미보장. 서울 자료가 아님 |
| NOAA Tides & Currents, Boston 8443970 hourly_height | 05 Energy 추가 C | B | 연 단위 요청. 주 조석 주기 약 12.42시간 |
| Box–Jenkins 국제선 항공 승객 1949–1960 | 06 Business 추가 D (내장) | A | 네트워크 불필요, 144행 |

원칙: 모든 로더는 `온라인 → 값 범위 검증 → 합성 대체`이며 `KIND_*`/`DATA_KIND`로 실제·합성을 표시한다. API 키는 저장하지 않는다.

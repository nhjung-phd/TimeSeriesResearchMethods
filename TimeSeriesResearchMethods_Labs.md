# AI 기반 시계열 연구방법론 — Colab 실습 가이드
> **Doctoral Research Labs · 자유 선택형(Free-Choice)**  
> *Research Question → Theory → Formula → Method → Colab → Interpretation → Validation → Research Assignment*

[🏠 저장소 첫 화면](README.md) · [🔬 전체 연구 프로세스](docs/Research_Workflow.md) · [📘 강의계획](COURSE_SYLLABUS.md) · [🚀 시작하기](GETTING_STARTED.md) · [🗂 데이터 출처](resources/Data_Source_Catalog.md) · [📝 과제 제출](assignments/Student_Submission_Guide.md)

---

## 실습 전에: 연구 프로세스에서 내 위치 확인

모든 실습은 **연구질문 → 개념·수식 → 방법론 → 데이터·Colab → 결과 → 해석 → 검증 → 제출**을 따릅니다. 단, 논문 전체의 연구과정에는 이보다 앞선 **현상 관찰·선행연구·Research Gap**과 이후의 **연구 기여·논문화**가 포함됩니다.

**[📖 시계열 연구의 5 Phases · 12 Steps 전체 보기](docs/Research_Workflow.md)**

## 1. 이 가이드 사용법

1. **Chapter 선택:** 강의 주제 또는 관심 있는 분석방법을 고릅니다.
2. **도메인 자유 선택:** 금융·투자, 부동산, 제조·품질, 공공정책, 에너지·환경, 경영·마케팅 중 해당 장에서 하나를 선택합니다. 다음 장에서 다른 도메인을 골라도 됩니다.
3. **실행 상태 확인:** 아래 상태가 `✅ 예제`인 노트북은 구현 코드가 포함되어 있고, `📝 템플릿`은 연구질문·설계 초안이므로 분석 코드가 완성되지 않았습니다.
4. **Colab 실행:** `▶ Colab`을 눌러 개인 사본에서 실행합니다. 최초 실행 때 환경·데이터·라이선스를 확인하세요.
5. **제출:** 연구질문, 방법·수식, 실행 결과, 결과 해석, 검증, 한계를 함께 제출합니다.

> ⚠️ **구현 상태(초기 공개본 기준):** 48개 도메인 과제 가운데 금융 Chapter 1은 코드 예제가 들어 있고, **나머지 47개는 미완성 연구실습 템플릿**입니다. 샘플 코드가 있다고 해서 모든 Google Colab 런타임에서 즉시 성공한다는 의미는 아닙니다. 개발 진행에 따라 이 표기를 갱신해야 합니다.

## 2. 한눈에 보는 8개 챕터

| Ch | 핵심 질문 | 분석 핵심 | 연구 산출물 | 바로가기 |
|---|---|---|---|---|
| **01** | 시간의 변화에는 어떤 규칙이 존재하는가? | 시계열 구조·정상성·자기상관 | 기초 데이터 진단표와 가정 해석 | [실습 보기](#chapter-01) |
| **02** | 과거의 데이터로 미래를 예측할 수 있는가? | ARIMA·SARIMA·기준선 | 예측 성능표와 잔차진단 | [실습 보기](#chapter-02) |
| **03** | 인공지능은 시간의 패턴을 어떻게 학습하는가? | 특징공학·RF·XGBoost·LSTM | 외표본 모델 비교 | [실습 보기](#chapter-03) |
| **04** | AI는 경험하지 못한 미래도 예측할 수 있는가? | Foundation Model·Zero-shot | 제로샷과 기준선 비교 | [실습 보기](#chapter-04) |
| **05** | 함께 변화하는 현상은 인과관계가 있는가? | ITS·DID·Synthetic Control | 반사실·식별가정 진단 | [실습 보기](#chapter-05) |
| **06** | 같은 변화가 모든 대상에게 동일하게 나타나는가? | FE·RE·TWFE·상호작용 | 개체 이질성 추정표 | [실습 보기](#chapter-06) |
| **07** | 분석 결과는 얼마나 신뢰할 수 있는가? | 누수·Walk-forward·강건성 | 검증·재현성 보고서 | [실습 보기](#chapter-07) |
| **08** | 연구질문에 적합한 시계열 분석방법은 무엇인가? | 목적·데이터·방법 통합 | 논문형 연구설계 초안 | [실습 보기](#chapter-08) |

## 3. 6개 도메인 데이터 수집 입문

각 장의 실습은 **독립 실행**을 지향합니다. `data_sources/`는 데이터 탐색을 위한 입문 노트북입니다. 각 노트북은 무료 공개 출처를 `try/except`로 시도하고, 연결이 실패하면 **합성자료로 대체하며 `DATA_KIND`로 구분**합니다. 출처의 접근 유형·라이선스·검증 상태(A/B/C)는 [출처 카탈로그](resources/Data_Source_Catalog.md)에 있고, 노트북의 온라인 로더는 Colab 실행으로 확인하기 전에는 "동작 보장"이 아닙니다.

| 도메인 | 데이터 수집 입문 | 기본 무료 출처 (검증 상태) | 데이터 관련 안내 |
|---|---|---|---|
| 금융·투자 | [📓 Notebook](data_sources/01_Finance_Data.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/data_sources/01_Finance_Data.ipynb) | FRED 금리 시계열 (B) | [출처 카탈로그](resources/Data_Source_Catalog.md) |
| 부동산 | [📓 Notebook](data_sources/02_RealEstate_Data.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/data_sources/02_RealEstate_Data.ipynb) | FHFA HPI (A/B) | [출처 카탈로그](resources/Data_Source_Catalog.md) |
| 제조·품질 | [📓 Notebook](data_sources/03_Manufacturing_Data.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/data_sources/03_Manufacturing_Data.ipynb) | 무료 시계열 부족: 합성 + SECOM 선택 (C) | [출처 카탈로그](resources/Data_Source_Catalog.md) |
| 공공정책 | [📓 Notebook](data_sources/04_PublicPolicy_Data.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/data_sources/04_PublicPolicy_Data.ipynb) | California Prop 99 (A/B) | [출처 카탈로그](resources/Data_Source_Catalog.md) |
| 에너지·환경 | [📓 Notebook](data_sources/05_EnergyEnvironment_Data.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/data_sources/05_EnergyEnvironment_Data.ipynb) | NOAA CO₂, Open-Meteo (A) | [출처 카탈로그](resources/Data_Source_Catalog.md) |
| 경영·마케팅 | [📓 Notebook](data_sources/06_BusinessMarketing_Data.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/data_sources/06_BusinessMarketing_Data.ipynb) | Wikimedia 조회수 (A) | [출처 카탈로그](resources/Data_Source_Catalog.md) |

## 4. Chapter별 자유 선택 실습

아래 48개 노트북은 GitHub 파일 경로와 Colab 실행 경로를 함께 제공합니다. **제목은 설계된 연구과제이며, 분석 실증이 완료되었다는 의미는 아닙니다.**

<a id="chapter-01"></a>
### Chapter 01. 시간의 변화에는 어떤 규칙이 존재하는가?
**핵심 개념:** 시계열 구조·정상성·자기상관  
**제출 예시:** 기초 데이터 진단표와 가정 해석  
**공통 이론:** [Lecture note](lecture_notes/Chapter01_TimeSeries_Foundations.md)

| 분야 | 연구실습 과제 | 상태 | 실습 바로가기 |
|---|---|---|---|
| 금융·투자 | ETF 수익률 정상성·변동성 | ✅ 코드 예제 | [📓 Notebook](notebooks/01_TimeSeries_Foundations/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/01_TimeSeries_Foundations/Finance.ipynb) |
| 부동산 | 주택가격 추세·계절성 | 📝 설계 템플릿 | [📓 Notebook](notebooks/01_TimeSeries_Foundations/RealEstate.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/01_TimeSeries_Foundations/RealEstate.ipynb) |
| 제조·품질 | 센서 신호 시간 패턴 | 📝 설계 템플릿 | [📓 Notebook](notebooks/01_TimeSeries_Foundations/Manufacturing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/01_TimeSeries_Foundations/Manufacturing.ipynb) |
| 공공정책 | 민원·교통 시계열 구조 | 📝 설계 템플릿 | [📓 Notebook](notebooks/01_TimeSeries_Foundations/PublicPolicy.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/01_TimeSeries_Foundations/PublicPolicy.ipynb) |
| 에너지·환경 | 기온·대기질 계절성 | 📝 설계 템플릿 | [📓 Notebook](notebooks/01_TimeSeries_Foundations/EnergyEnvironment.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/01_TimeSeries_Foundations/EnergyEnvironment.ipynb) |
| 경영·마케팅 | 매출·거래량 계절성 | 📝 설계 템플릿 | [📓 Notebook](notebooks/01_TimeSeries_Foundations/BusinessMarketing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/01_TimeSeries_Foundations/BusinessMarketing.ipynb) |

[↑ 챕터 목록으로](#2-한눈에-보는-8개-챕터)

---

<a id="chapter-02"></a>
### Chapter 02. 과거의 데이터로 미래를 예측할 수 있는가?
**핵심 개념:** ARIMA·SARIMA·기준선  
**제출 예시:** 예측 성능표와 잔차진단  
**공통 이론:** [Lecture note](lecture_notes/Chapter02_Statistical_Forecasting.md)

| 분야 | 연구실습 과제 | 상태 | 실습 바로가기 |
|---|---|---|---|
| 금융·투자 | 수익률 ARIMA·변동성 GARCH | 📝 설계 템플릿 | [📓 Notebook](notebooks/02_Statistical_Forecasting/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/02_Statistical_Forecasting/Finance.ipynb) |
| 부동산 | 거래량 SARIMA | 📝 설계 템플릿 | [📓 Notebook](notebooks/02_Statistical_Forecasting/RealEstate.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/02_Statistical_Forecasting/RealEstate.ipynb) |
| 제조·품질 | 제조 수요 SARIMA | 📝 설계 템플릿 | [📓 Notebook](notebooks/02_Statistical_Forecasting/Manufacturing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/02_Statistical_Forecasting/Manufacturing.ipynb) |
| 공공정책 | 민원 건수 통계예측 | 📝 설계 템플릿 | [📓 Notebook](notebooks/02_Statistical_Forecasting/PublicPolicy.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/02_Statistical_Forecasting/PublicPolicy.ipynb) |
| 에너지·환경 | 전력수요 SARIMA | 📝 설계 템플릿 | [📓 Notebook](notebooks/02_Statistical_Forecasting/EnergyEnvironment.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/02_Statistical_Forecasting/EnergyEnvironment.ipynb) |
| 경영·마케팅 | 일별 매출 SARIMA | 📝 설계 템플릿 | [📓 Notebook](notebooks/02_Statistical_Forecasting/BusinessMarketing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/02_Statistical_Forecasting/BusinessMarketing.ipynb) |

[↑ 챕터 목록으로](#2-한눈에-보는-8개-챕터)

---

<a id="chapter-03"></a>
### Chapter 03. 인공지능은 시간의 패턴을 어떻게 학습하는가?
**핵심 개념:** 특징공학·RF·XGBoost·LSTM  
**제출 예시:** 외표본 모델 비교  
**공통 이론:** [Lecture note](lecture_notes/Chapter03_Machine_Deep_Learning.md)

| 분야 | 연구실습 과제 | 상태 | 실습 바로가기 |
|---|---|---|---|
| 금융·투자 | 금융 수익률 RF·XGBoost | 📝 설계 템플릿 | [📓 Notebook](notebooks/03_Machine_Deep_Learning/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/03_Machine_Deep_Learning/Finance.ipynb) |
| 부동산 | 주택가격 ML 예측 | 📝 설계 템플릿 | [📓 Notebook](notebooks/03_Machine_Deep_Learning/RealEstate.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/03_Machine_Deep_Learning/RealEstate.ipynb) |
| 제조·품질 | 설비 이상·품질 예측 | 📝 설계 템플릿 | [📓 Notebook](notebooks/03_Machine_Deep_Learning/Manufacturing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/03_Machine_Deep_Learning/Manufacturing.ipynb) |
| 공공정책 | 교통량 XGBoost | 📝 설계 템플릿 | [📓 Notebook](notebooks/03_Machine_Deep_Learning/PublicPolicy.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/03_Machine_Deep_Learning/PublicPolicy.ipynb) |
| 에너지·환경 | 전력수요 LSTM | 📝 설계 템플릿 | [📓 Notebook](notebooks/03_Machine_Deep_Learning/EnergyEnvironment.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/03_Machine_Deep_Learning/EnergyEnvironment.ipynb) |
| 경영·마케팅 | 판매량 RF·XGBoost | 📝 설계 템플릿 | [📓 Notebook](notebooks/03_Machine_Deep_Learning/BusinessMarketing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/03_Machine_Deep_Learning/BusinessMarketing.ipynb) |

[↑ 챕터 목록으로](#2-한눈에-보는-8개-챕터)

---

<a id="chapter-04"></a>
### Chapter 04. AI는 경험하지 못한 미래도 예측할 수 있는가?
**핵심 개념:** Foundation Model·Zero-shot  
**제출 예시:** 제로샷과 기준선 비교  
**공통 이론:** [Lecture note](lecture_notes/Chapter04_Foundation_Models.md)

| 분야 | 연구실습 과제 | 상태 | 실습 바로가기 |
|---|---|---|---|
| 금융·투자 | ETF Zero-shot 예측 | 📝 설계 템플릿 | [📓 Notebook](notebooks/04_Foundation_Models/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/04_Foundation_Models/Finance.ipynb) |
| 부동산 | 가격지수 Zero-shot | 📝 설계 템플릿 | [📓 Notebook](notebooks/04_Foundation_Models/RealEstate.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/04_Foundation_Models/RealEstate.ipynb) |
| 제조·품질 | 제조 수요 Zero-shot | 📝 설계 템플릿 | [📓 Notebook](notebooks/04_Foundation_Models/Manufacturing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/04_Foundation_Models/Manufacturing.ipynb) |
| 공공정책 | 공공서비스 Zero-shot | 📝 설계 템플릿 | [📓 Notebook](notebooks/04_Foundation_Models/PublicPolicy.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/04_Foundation_Models/PublicPolicy.ipynb) |
| 에너지·환경 | 전력수요 Zero-shot | 📝 설계 템플릿 | [📓 Notebook](notebooks/04_Foundation_Models/EnergyEnvironment.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/04_Foundation_Models/EnergyEnvironment.ipynb) |
| 경영·마케팅 | 판매량 Zero-shot | 📝 설계 템플릿 | [📓 Notebook](notebooks/04_Foundation_Models/BusinessMarketing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/04_Foundation_Models/BusinessMarketing.ipynb) |

[↑ 챕터 목록으로](#2-한눈에-보는-8개-챕터)

---

<a id="chapter-05"></a>
### Chapter 05. 함께 변화하는 현상은 인과관계가 있는가?
**핵심 개념:** ITS·DID·Synthetic Control  
**제출 예시:** 반사실·식별가정 진단  
**공통 이론:** [Lecture note](lecture_notes/Chapter05_Causal_Inference.md)

| 분야 | 연구실습 과제 | 상태 | 실습 바로가기 |
|---|---|---|---|
| 금융·투자 | 금융 이벤트 ITS | 📝 설계 템플릿 | [📓 Notebook](notebooks/05_Causal_Inference/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/05_Causal_Inference/Finance.ipynb) |
| 부동산 | 부동산 정책 DID | 📝 설계 템플릿 | [📓 Notebook](notebooks/05_Causal_Inference/RealEstate.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/05_Causal_Inference/RealEstate.ipynb) |
| 제조·품질 | 공정 개선 ITS | 📝 설계 템플릿 | [📓 Notebook](notebooks/05_Causal_Inference/Manufacturing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/05_Causal_Inference/Manufacturing.ipynb) |
| 공공정책 | 정책 개입 ITS·DID | 📝 설계 템플릿 | [📓 Notebook](notebooks/05_Causal_Inference/PublicPolicy.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/05_Causal_Inference/PublicPolicy.ipynb) |
| 에너지·환경 | 환경규제 효과 분석 | 📝 설계 템플릿 | [📓 Notebook](notebooks/05_Causal_Inference/EnergyEnvironment.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/05_Causal_Inference/EnergyEnvironment.ipynb) |
| 경영·마케팅 | 광고 캠페인 DID | 📝 설계 템플릿 | [📓 Notebook](notebooks/05_Causal_Inference/BusinessMarketing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/05_Causal_Inference/BusinessMarketing.ipynb) |

[↑ 챕터 목록으로](#2-한눈에-보는-8개-챕터)

---

<a id="chapter-06"></a>
### Chapter 06. 같은 변화가 모든 대상에게 동일하게 나타나는가?
**핵심 개념:** FE·RE·TWFE·상호작용  
**제출 예시:** 개체 이질성 추정표  
**공통 이론:** [Lecture note](lecture_notes/Chapter06_Panel_Data_Analysis.md)

| 분야 | 연구실습 과제 | 상태 | 실습 바로가기 |
|---|---|---|---|
| 금융·투자 | 산업 포트폴리오 FE | 📝 설계 템플릿 | [📓 Notebook](notebooks/06_Panel_Data_Analysis/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/06_Panel_Data_Analysis/Finance.ipynb) |
| 부동산 | 지역별 주택가격 FE | 📝 설계 템플릿 | [📓 Notebook](notebooks/06_Panel_Data_Analysis/RealEstate.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/06_Panel_Data_Analysis/RealEstate.ipynb) |
| 제조·품질 | 공장별 생산성 패널 | 📝 설계 템플릿 | [📓 Notebook](notebooks/06_Panel_Data_Analysis/Manufacturing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/06_Panel_Data_Analysis/Manufacturing.ipynb) |
| 공공정책 | 지자체 패널 FE | 📝 설계 템플릿 | [📓 Notebook](notebooks/06_Panel_Data_Analysis/PublicPolicy.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/06_Panel_Data_Analysis/PublicPolicy.ipynb) |
| 에너지·환경 | 지역 배출량 패널 | 📝 설계 템플릿 | [📓 Notebook](notebooks/06_Panel_Data_Analysis/EnergyEnvironment.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/06_Panel_Data_Analysis/EnergyEnvironment.ipynb) |
| 경영·마케팅 | 점포별 매출 FE | 📝 설계 템플릿 | [📓 Notebook](notebooks/06_Panel_Data_Analysis/BusinessMarketing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/06_Panel_Data_Analysis/BusinessMarketing.ipynb) |

[↑ 챕터 목록으로](#2-한눈에-보는-8개-챕터)

---

<a id="chapter-07"></a>
### Chapter 07. 분석 결과는 얼마나 신뢰할 수 있는가?
**핵심 개념:** 누수·Walk-forward·강건성  
**제출 예시:** 검증·재현성 보고서  
**공통 이론:** [Lecture note](lecture_notes/Chapter07_Validation_Robustness.md)

| 분야 | 연구실습 과제 | 상태 | 실습 바로가기 |
|---|---|---|---|
| 금융·투자 | 금융 누수·Walk-forward | 📝 설계 템플릿 | [📓 Notebook](notebooks/07_Validation_Robustness/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/07_Validation_Robustness/Finance.ipynb) |
| 부동산 | 지역·기간 강건성 | 📝 설계 템플릿 | [📓 Notebook](notebooks/07_Validation_Robustness/RealEstate.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/07_Validation_Robustness/RealEstate.ipynb) |
| 제조·품질 | 센서 누수·경보 정확도 | 📝 설계 템플릿 | [📓 Notebook](notebooks/07_Validation_Robustness/Manufacturing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/07_Validation_Robustness/Manufacturing.ipynb) |
| 공공정책 | 정책 Placebo | 📝 설계 템플릿 | [📓 Notebook](notebooks/07_Validation_Robustness/PublicPolicy.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/07_Validation_Robustness/PublicPolicy.ipynb) |
| 에너지·환경 | 기상 체제변화 강건성 | 📝 설계 템플릿 | [📓 Notebook](notebooks/07_Validation_Robustness/EnergyEnvironment.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/07_Validation_Robustness/EnergyEnvironment.ipynb) |
| 경영·마케팅 | 프로모션 누수 | 📝 설계 템플릿 | [📓 Notebook](notebooks/07_Validation_Robustness/BusinessMarketing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/07_Validation_Robustness/BusinessMarketing.ipynb) |

[↑ 챕터 목록으로](#2-한눈에-보는-8개-챕터)

---

<a id="chapter-08"></a>
### Chapter 08. 연구질문에 적합한 시계열 분석방법은 무엇인가?
**핵심 개념:** 목적·데이터·방법 통합  
**제출 예시:** 논문형 연구설계 초안  
**공통 이론:** [Lecture note](lecture_notes/Chapter08_Research_Integration.md)

| 분야 | 연구실습 과제 | 상태 | 실습 바로가기 |
|---|---|---|---|
| 금융·투자 | 금융 연구설계 | 📝 설계 템플릿 | [📓 Notebook](notebooks/08_Research_Integration/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/08_Research_Integration/Finance.ipynb) |
| 부동산 | 부동산 연구설계 | 📝 설계 템플릿 | [📓 Notebook](notebooks/08_Research_Integration/RealEstate.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/08_Research_Integration/RealEstate.ipynb) |
| 제조·품질 | 제조 연구설계 | 📝 설계 템플릿 | [📓 Notebook](notebooks/08_Research_Integration/Manufacturing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/08_Research_Integration/Manufacturing.ipynb) |
| 공공정책 | 정책 연구설계 | 📝 설계 템플릿 | [📓 Notebook](notebooks/08_Research_Integration/PublicPolicy.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/08_Research_Integration/PublicPolicy.ipynb) |
| 에너지·환경 | 에너지 연구설계 | 📝 설계 템플릿 | [📓 Notebook](notebooks/08_Research_Integration/EnergyEnvironment.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/08_Research_Integration/EnergyEnvironment.ipynb) |
| 경영·마케팅 | 경영 연구설계 | 📝 설계 템플릿 | [📓 Notebook](notebooks/08_Research_Integration/BusinessMarketing.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/08_Research_Integration/BusinessMarketing.ipynb) |

[↑ 챕터 목록으로](#2-한눈에-보는-8개-챕터)

---

## 5. 박사과정 연구실습의 공통 구성

| 순서 | 연구 요소 | 필수 질문 |
|---|---|---|
| ① | **Research Question** | 무엇을 설명·예측·식별하려는가? |
| ② | **Theory / Formula** | 핵심 개념과 수식의 가정은 무엇인가? |
| ③ | **Method / Data** | 왜 이 분석방법이며, 시점별 데이터 이용 가능성은 확보됐는가? |
| ④ | **Colab Analysis** | 원본부터 재현되는 분석 코드인가? |
| ⑤ | **Results / Interpretation** | 결과의 크기·방향·경제적/실무적 의미는? |
| ⑥ | **Validation** | 예측은 외표본·누수, 인과는 식별가정·반사실을 검증했는가? |
| ⑦ | **Research Assignment** | 검증 가능한 결론·한계·재현 자료를 제출했는가? |

## 6. 공통 연구설계·검증 도구

| 자료 | 목적 |
|---|---|
| [Research Question Template](research_design/Research_Question_Template.md) | 검증 가능한 RQ 작성 |
| [Method Selection Guide](research_design/Method_Selection_Guide.md) | 분석 목적에 맞는 방법 선정 |
| [Identification Assumptions](research_design/Identification_Assumptions.md) | 인과적 주장 범위 점검 |
| [Forecast Evaluation](validation/Forecast_Evaluation.md) | 외표본 성능·기준선 |
| [Leakage Checklist](validation/Leakage_Checklist.md) | 시간 누수 방지 |
| [Causal Validity](validation/Causal_Validity.md) | 평행추세·동시충격·반사실 |
| [Robustness Checklist](validation/Robustness_Checklist.md) | 민감도·대체설정 |
| [Reproducibility Checklist](validation/Reproducibility_Checklist.md) | 코드·데이터·환경 재현성 |
| [Research Report Template](assignments/Research_Report_Template.md) | 논문형 결과 보고 |
| [Evaluation Rubric](assignments/Evaluation_Rubric.md) | 과제 평가 기준 |

## 7. 즉시 확인할 수 있는 샘플

- **금융 정상성 예제:** [📓 Notebook](notebooks/01_TimeSeries_Foundations/Finance.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/notebooks/01_TimeSeries_Foundations/Finance.ipynb). `yfinance` 수집 시도가 실패하면 합성자료로 대체될 수 있으므로 출력의 데이터 유형을 반드시 확인합니다.
- **ITS 인과추론 합성 예제:** [📓 Notebook](examples/Causal_Research_Example/ITS_Synthetic_Demo.ipynb) · [▶ Colab](https://colab.research.google.com/github/nhjung-phd/TimeSeriesResearchMethods/blob/main/examples/Causal_Research_Example/ITS_Synthetic_Demo.ipynb). 추정된 효과는 실제 정책효과가 아닙니다.

## 8. 제출 및 연구 윤리

- 최소 제출 내용: 연구질문 1개, 주요 수식·선정 근거, 결과 그래프/표, 결과 해석, 검증, 한계, 데이터 출처.
- 합성자료 분석은 실제 시장·정책·공정의 실증 결과로 표현하지 않습니다.
- 무료 데이터라도 GitHub에 공개 재배포하기 전 라이선스·API 약관을 확인합니다.
- API 키, 개인식별정보, 비공개 원자료는 공개 저장소에 업로드하지 않습니다.
- 실습 코드와 결과는 교육·연구용이며 투자 자문이나 정책효과의 확정적 증거가 아닙니다.

---
**Next Steps:** [석사 시계열 분석 저장소](https://github.com/nhjung-phd/TimeSeriesAnalysis)

# AI 기반 시계열 연구방법론 | Time Series Research Methods

**AI-Assisted Time Series Research Methods — From Temporal Patterns to Research Evidence**

연구자를 위한 **총 15시간(2회 × 7.5시간)**의 자유 선택형 Google Colab 연구실습 저장소입니다.

본 강의는 시계열의 구조를 이해하고, 통계·AI 기반 예측방법을 학습하며, 인과추론·패널분석·연구결과 검증을 거쳐 **인과추론 및 의사결정과학 심화 연구로 발전하기 위한 기초 연구역량**을 형성하는 것을 목표로 합니다.

기존 석사과정 [TimeSeriesAnalysis](https://github.com/nhjung-phd/TimeSeriesAnalysis)의 학습자료 및 Colab 운영방식을 참고하되, 박사과정에 필요한 **연구질문, 분석방법 선택, 식별가정, 강건성 및 재현성 검증**을 강화한 독립적인 교육·연구 프로젝트입니다.

> 📚 **[전체 실습 가이드 — 8 Chapters × 6 Domains / Google Colab 바로 실행](TimeSeriesResearchMethods_Labs.md)**
>
> 각 챕터에서 관심 도메인을 자유롭게 선택하고, 데이터 수집부터 분석·결과 해석·검증·연구과제 제출까지 진행할 수 있습니다.

---

## 🎯 Learning Objectives

본 강의의 학습목표는 다음과 같습니다.

1. 시계열 데이터의 시간적 구조와 통계적 특성을 이해한다.
2. 연구질문과 데이터 특성에 적합한 통계·AI 분석방법을 선택한다.
3. 예측과 인과적 설명의 차이를 이해하고 분석의 기본 가정을 검토한다.
4. 표본외 평가, 강건성 분석 및 재현성 검증을 수행한다.
5. 연구결과를 학술적으로 해석하고 후속 인과추론·의사결정 연구로 확장한다.

## 📚 Chapters — Course Curriculum

| Ch | 연구질문 (Chapter Title) | 핵심 방법론 | 시간 |
|:---:|---|---|:---:|
| **01** | **시간의 변화에는 어떤 규칙이 존재하는가?** | 추세·계절성, 정상성, ACF/PACF, ADF/KPSS | 1.5 h |
| **02** | **과거의 데이터로 미래를 예측할 수 있는가?** | AR·MA·ARIMA·SARIMA, 예측 및 잔차진단 | 2 h |
| **03** | **인공지능은 시간의 패턴을 어떻게 학습하는가?** | Lag Features, Random Forest, XGBoost, LSTM, Transformer | 2 h |
| **04** | **AI는 경험하지 못한 미래도 예측할 수 있는가?** | Foundation Models, Chronos, TimesFM, Zero-shot Forecasting | 2 h |
| **05** | **함께 변화하는 현상은 인과관계가 있는가?** | 반사실, ITS, DID, Synthetic Control | 2.5 h |
| **06** | **같은 변화가 모든 대상에게 동일하게 나타나는가?** | Panel Data, FE, RE, TWFE, 이질성 | 2 h |
| **07** | **분석 결과는 얼마나 신뢰할 수 있는가?** | 외표본 검증, 데이터 누수, 강건성, 재현성 | 1.5 h |
| **08** | **연구질문에 적합한 시계열 분석방법은 무엇인가?** | 연구설계, 방법론 선택, 결과 해석 및 검증 | 1.5 h |
| | **Total** | | **15 h** |

## 🔬 Research Learning Workflow

모든 챕터는 연구방법론 중심의 공통 학습 구조를 따릅니다.

**Research Question → Theory → Formula → Method → Colab → Results → Interpretation → Validation → Research Assignment**

- **Research Question:** 분석할 현상과 연구질문 정의
- **Theory & Formula:** 핵심 개념과 수학적 모형 이해
- **Method:** 연구질문과 데이터에 적합한 방법 선택
- **Colab:** 공개데이터를 이용한 Python 실습
- **Results & Interpretation:** 결과표·그래프 해석
- **Validation:** 가정·성능·강건성·재현성 검증
- **Research Assignment:** 분석 결과를 연구보고서로 정리

## 🌐 Free-Choice Domain Labs

수강생은 각 챕터에서 관심 분야를 자유롭게 선택할 수 있습니다.

| Domain | 주요 분석 대상 |
|---|---|
| **Finance & Investment** | 주가, 수익률, 변동성, 금융시장 사건 |
| **Real Estate** | 주택가격, 거래량, 지역별 부동산시장 |
| **Manufacturing & Quality** | 설비 센서, 품질, 불량, 공정 변화 |
| **Public Policy** | 공공통계, 정책개입, 지역별 정책효과 |
| **Energy & Environment** | 전력수요, 기상, 대기질, 발전량 |
| **Business & Marketing** | 매출, 판매량, 고객 행동, 마케팅 효과 |

**[전체 도메인별 Colab 실습 목록 바로가기](TimeSeriesResearchMethods_Labs.md)**

## 🚀 Start Here

1. [강의계획서](COURSE_SYLLABUS.md) 확인
2. [Google Colab 시작하기](GETTING_STARTED.md)
3. [전체 실습 가이드](TimeSeriesResearchMethods_Labs.md)에서 Chapter 선택
4. 6개 도메인 중 관심 분야 선택
5. Colab 실행 → 결과 해석 → 검증
6. [연구과제 제출 안내](assignments/Student_Submission_Guide.md)에 따라 결과 제출

### 즉시 실행 가능한 샘플

- [금융시계열 정상성 실습](notebooks/01_TimeSeries_Foundations/Finance.ipynb): 가격·수익률, ADF/KPSS, ACF, ARCH-LM
- [인과추론 ITS 합성데이터 실습](examples/Causal_Research_Example/ITS_Synthetic_Demo.ipynb): 개입효과 추정, HAC 표준오차
- [데이터 수집 입문 노트북 6종](data_sources/): 도메인별 데이터 형식 및 수집 방법 안내

> **실습 제작 상태:** 현재 48개 도메인별 연구과제 중 일부는 실행 가능한 샘플이며, 나머지는 실습 확장을 위한 템플릿입니다. 완성형 실습과 템플릿은 전체 실습 가이드에서 구분하여 안내합니다.

## 🧪 Research Design & Validation

박사과정에서는 단순한 모델 실행보다 연구설계와 결과 검증을 중시합니다.

- [Research Design](research_design/) — 연구질문, 변수, 모형 선택, 연구계획서
- [Validation](validation/) — 외표본 검증, 데이터 누수, 인과적 타당성, 강건성
- [Assignments](assignments/) — 연구보고서 양식과 평가기준
- [AI Research Prompts](prompts/) — 연구질문 설정, 코드 검토, 결과 해석

## 🔗 Pathways to Advanced Research

본 강의는 다음 심화 연구방법론으로 연결됩니다.

**Time Series Research Methods → Causal Inference / Decision Science**

- **Causal Inference:** 반사실, 인과효과 식별, 고급 DID, 이질적 처치효과
- **Decision Science:** 예측 기반 최적화, 정책선택, 의사결정이론, 강화학습

## 📌 Repository Notes

- Python 그래프의 제목·축·범례는 한글 폰트 호환성을 고려하여 영어 표기를 기본으로 합니다.
- 공개데이터의 출처·수집일·전처리·라이선스를 명시합니다.
- API 키, 개인정보 및 민감정보는 GitHub에 업로드하지 않습니다.
- AI 생성 코드는 연구자가 직접 실행하고 결과 및 가정을 검증합니다.
- 학생 프로젝트는 공개 동의를 받은 자료에 한하여 업로드합니다.

---

**Instructor:** Dr. Nak Hyun Jung

**Purpose:** Academic research and education. Not investment advice.
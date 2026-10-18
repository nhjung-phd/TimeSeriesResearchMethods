# AI 기반 시계열 연구방법론 | Time Series Research Methods

**AI-Assisted Time Series Research Methods — From Temporal Patterns to Research Evidence**

박사과정 15시간(2회 × 7.5시간) 자유선택형 Colab 연구실습 저장소. **예측 → 인과추론 입문 → 패널 분석 → 검증 → 의사결정 연구로의 연결**을 목표로 합니다.

기존 석사과정 [`TimeSeriesAnalysis`](https://github.com/nhjung-phd/TimeSeriesAnalysis)의 `lecture_notes / notebooks / practice / prompts / docs / examples` 구조와 Colab 안내 방식을 참고해 박사과정용 연구설계와 검증 모듈을 추가했습니다. 이 저장소는 새로운 독립 프로젝트입니다.

> 📚 **[전체 실습 가이드 — 8 Chapters × 6 Domains / Google Colab 바로 실행](TimeSeriesResearchMethods_Labs.md)**  
> 각 챕터에서 도메인을 자유롭게 선택하고, 실행 가능 상태·데이터 수집·연구설계·검증·제출까지 한 페이지에서 확인하세요.

## Start here

1. [강의계획](COURSE_SYLLABUS.md) → [Colab 시작하기](GETTING_STARTED.md)
2. [8개 챕터 실습 목록](docs/Domain_Lab_Catalog.md)에서 Chapter 선택
3. 6개 도메인(금융·투자, 부동산, 제조·품질, 공공정책, 에너지·환경, 경영·마케팅) 중 자유롭게 선택
4. Colab 실행 → 결과 해석 → 검증 → [연구과제](assignments/Student_Submission_Guide.md) 제출

### 즉시 실행할 수 있는 샘플

- [금융 시계열 정상성 전체 실습](notebooks/01_TimeSeries_Foundations/Finance.ipynb): 공개 시세 다운로드 시도, 실패 시 합성 데이터 **명시적 대체**, ADF/KPSS, ACF, ARCH-LM
- [인과추론 ITS 실습](examples/Causal_Research_Example/ITS_Synthetic_Demo.ipynb): 효과를 알고 있는 합성 개입자료로 HAC 추정
- [데이터 수집 샘플 6종](data_sources/): 각 도메인 소개 및 합성자료 기반의 실행 가능한 데이터 형식 확인. 실제 API와 키가 필요한 소스는 별도 안내

> **제작 상태:** 전체 디렉터리, 48개 도메인별 과제 초안 노트북, 실행 가능한 샘플 2개, 6개 수집 입문 노트북, 연구설계·검증·과제 문서가 포함됩니다. **48개 중 모든 과제가 완성형 분석 노트북인 것은 아닙니다.**

## End-to-End Time Series Research Process

> **현상 관찰 → 선행연구·Research Gap → 연구질문 → 연구설계 → 데이터·시계열 분석 → 모형·결과 → 검증·강건성 → 학술적 기여**
>
> 단순한 예측 실습을 넘어 연구질문부터 재현 가능한 근거까지 이어지는 **5 Phases · 12 Steps** 연구 프로세스를 학습합니다. 모든 챕터의 Colab 실습에서 연구질문·방법·결과 해석·검증을 연결합니다.
>
> 📖 **[시계열 연구 전체 프로세스: 단계별 가이드](docs/Research_Workflow.md)**  
> 📓 **[48개 자유선택형 도메인 실습](TimeSeriesResearchMethods_Labs.md)**

## Course research workflow

**Research Question → Theory → Formula → Method → Colab → Results → Interpretation → Validation → Research Assignment**

## Chapters

| Ch | 내용 | 시간 |
|---|---|---:|
| 01 | 정상성·자기상관 | 1.5 h |
| 02 | ARIMA·SARIMA 통계예측 | 2 h |
| 03 | ML·DL 시계열 | 2 h |
| 04 | Foundation Models·Zero-shot | 2 h |
| 05 | ITS·DID·Synthetic Control | 2.5 h |
| 06 | FE·RE·TWFE | 2 h |
| 07 | 신뢰성·강건성 | 1.5 h |
| 08 | 연구질문과 방법 통합 | 1.5 h |

## Repository notes

- Python 그래프는 한글 폰트 문제를 피하기 위해 영문 축·제목을 기본으로 합니다.
- `.ipynb`를 Colab으로 열려면 GitHub 업로드 후 **Open in Colab** 버튼 또는 `https://colab.research.google.com/github/<owner>/<repo>/blob/main/<path>` 경로를 사용하세요.
- 데이터와 라이선스: [데이터 출처 카탈로그](resources/Data_Source_Catalog.md), [data README](data/README.md). API 키와 개인·민감정보는 커밋하지 마세요.
- 학생 프로젝트는 공개 허락을 받은 경우에만 업로드하며, 개인 데이터는 제출하지 않습니다.

**Instructor:** Dr. Nak Hyun Jung · 교육·연구용, 투자 자문 아님.

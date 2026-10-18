# Course Syllabus

**AI 기반 시계열 연구방법론** · 박사과정 · 총 15시간(7.5시간 × 2일)

## 학습목표
1. 연구질문에 적절한 시계열 데이터 구조와 분석 단위를 선택한다.
2. 통계·AI 예측을 표본외 검증과 비교 기준선으로 평가한다.
3. 시계열 변화와 인과적 효과를 구분하고 식별가정을 설명한다.
4. 패널 분석으로 개체와 시간의 이질성을 분석한다.
5. 분석 결과를 재현 가능한 연구 증거로 제시한다.

## Day 1 — 예측과 일반화 (7.5h)
- Chapter 1 (1.5h): 정상성·자기상관·시계열 특성
- Chapter 2 (2h): AR·MA·ARIMA·SARIMA
- Chapter 3 (2h): RF·XGBoost·RNN·LSTM·Transformer
- Chapter 4 (2h): Chronos·TimesFM·Zero-shot

## Day 2 — 인과·이질성·검증 (7.5h)
- Chapter 5 (2.5h): 반사실, ITS, DID, Synthetic Control
- Chapter 6 (2h): Pooled OLS, FE, RE, Two-way FE
- Chapter 7 (1.5h): 누수, walk-forward, HAC, 강건성·재현성
- Chapter 8 (1.5h): 방법 선택과 연구설계 워크숍

**실습 방식:** 모든 챕터에서 6개 도메인 중 자유 선택. 챕터별 독립 노트북; 공통 발표·피드백.

**제출:** 연구질문 → 수식·모형 → 결과표/그림 → 해석 → 타당성 검증 → 제한점. 점수표는 `assignments/Evaluation_Rubric.md`.

**후속 과정 연계:** 고급 인과추론(식별·이질적 효과), 의사결정과 경영과학(예측 이후 최적 행동 선택). 본 강의에서는 입문과 교량에 집중.

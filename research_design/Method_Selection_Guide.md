# Method Selection

- 패턴·정상성: decomposition, ADF/KPSS, ACF
- 예측: Naive → ARIMA → ML/DL → TSFM; 외표본 성능 우선
- 정책효과: ITS(동시충격 주의), DID(평행추세), Synthetic Control(사전 적합)
- 패널: pooled / FE / RE / TWFE; FE 자체가 효과 이질성을 식별하지는 않음
- 의사결정: 예측 오차만으로 의사결정 품질을 보장할 수 없음

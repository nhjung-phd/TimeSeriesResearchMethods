# Getting Started — Google Colab

1. 저장소를 GitHub 계정에 업로드하거나 Git으로 클론합니다.
2. `notebooks/01_TimeSeries_Foundations/Finance.ipynb`를 GitHub에서 열어 Colab을 선택합니다.
3. **런타임 → 모두 실행**. yfinance 인터넷 접근이 안 되면 명시적으로 합성 데이터로 대체됩니다. 합성 데이터는 실데이터 결과로 주장하지 마세요.
4. 다른 노트북은 초기 **과제 설계용 템플릿**입니다. 연구문제·데이터 출처·실험 설계를 수정하여 실습을 확장하세요.
5. GPU를 요구하는 Foundation Model 실습은 별도 버전·가중치·Colab 런타임 설정 후 실행해야 합니다.

## 환경 설치
```bash
python -m pip install -r requirements.txt
```
개별 노트북은 Colab 기본 라이브러리를 우선 사용합니다. pandas / numpy / matplotlib / scipy / statsmodels / yfinance 등의 버전을 수업 전에 확인하세요.

## 데이터 원칙
- 출처·버전·수집일·이용조건을 문서화합니다.
- 인과 실습은 합성 데이터로 먼저 효과 복원 여부를 검증합니다.
- 학습·검증·시험 시점 이후의 데이터나 사후 발표된 값은 예측 특징으로 쓰지 않습니다.
- API 키는 GitHub에 커밋하지 않습니다.

diff --git a/README.md b/README.md
index fdfcb9517ef9c99acf2ac1ae4aaf3ec13c8a4f56..9e705dc8d647d619ef00f42dcca7fc7f006b9389 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,86 @@
-# Lauren
\ No newline at end of file
+# Lauren Brick Market
+
+레고 및 브릭 수집가를 위한 간단한 마켓플레이스로, [Bricklink](https://www.bricklink.com/v2/main.page)를 참고해 제작했습니다. 사용자는 원하는 언어로 프로필을 설정하고, 상품을 올려 판매하거나 다른 사용자의 상품을 구매할 수 있으며, 거래 중에는 자동 번역되는 채팅으로 소통할 수 있습니다.
+
+## 주요 기능
+
+1. **상품 등록/구매** – 로그인한 사용자는 상품을 등록할 수 있고, 다른 사용자의 상품에 대해 구매 채팅을 시작할 수 있습니다.
+2. **거래 채팅** – 구매를 시작하면 판매자와 구매자만 접근할 수 있는 채팅 룸이 생성됩니다.
+3. **자동 번역** – 채팅 메시지는 상대방의 설정 언어로 번역되어 보여집니다. `deep-translator` 라이브러리를 우선 사용하며, 네트워크 제한 시에는 소규모 오프라인 사전을 이용한 폴백을 제공합니다.
+
+## 실행 방법
+
+아래 예시는 macOS/Linux 기준입니다. Windows PowerShell에서는 `source .venv/bin/activate` 대신 `.venv\\Scripts\\Activate.ps1`을 실행하면 됩니다.
+
+1. **Python 가상환경 생성 및 진입**
+   ```bash
+   python -m venv .venv
+   source .venv/bin/activate
+   ```
+
+2. **필수 패키지 설치** – 네트워크가 제한된 환경에서는 `deep-translator` 설치가 실패할 수 있습니다. 이 경우 내장 오프라인 사전이 자동으로 폴백되어 앱은 정상 구동됩니다.
+   ```bash
+   pip install --upgrade pip
+   pip install -r requirements.txt
+   ```
+
+3. **데이터베이스 초기화** – `instance/brickmarket.sqlite`가 생성됩니다.
+   ```bash
+   flask --app app.py init-db
+   ```
+
+4. **데모 데이터 시드(선택)** – 테스트용 사용자/상품을 등록하려면 실행합니다.
+   ```bash
+   flask --app app.py seed-demo
+   ```
+
+5. **개발 서버 실행**
+   ```bash
+   flask --app app.py run --debug
+   ```
+
+브라우저에서 <http://127.0.0.1:5000> 으로 접속하면 홈 화면이 나타납니다. 종료 시에는 터미널에서 `Ctrl+C`로 서버를 중지한 후 `deactivate`로 가상환경을 빠져나올 수 있습니다.
+
+## GitHub에 올리고 다른 PC에서 불러오기
+
+이 프로젝트를 자신의 GitHub 저장소에 올린 뒤, 로컬 PC에서 `git clone`으로 불러와 실행하려면 다음 절차를 따르면 됩니다.
+
+1. **현재 디렉터리에서 새 원격 저장소 연결**
+   - GitHub에서 빈 저장소를 만든 후, 아래 명령어로 원격을 추가합니다.
+   ```bash
+   git remote add origin https://github.com/<your-username>/<repo-name>.git
+   git push -u origin main
+   ```
+
+2. **다른 PC에서 클론 후 실행**
+   ```bash
+   git clone https://github.com/<your-username>/<repo-name>.git
+   cd <repo-name>
+   python -m venv .venv
+   # macOS/Linux
+   source .venv/bin/activate
+   # Windows (PowerShell)
+   .venv\\Scripts\\Activate.ps1
+   pip install -r requirements.txt
+   flask --app app.py init-db
+   flask --app app.py run --debug
+   ```
+
+   홈 화면은 <http://127.0.0.1:5000>에서 확인할 수 있습니다. 이미 `init-db`를 한 번 실행했다면 이후에는 건너뛰어도 됩니다.
+
+## 데이터 모델
+
+- **User** – 사용자 이름, 선호 언어, 소개글을 저장합니다.
+- **Item** – 판매 상품. 제목, 설명, 가격, 판매자, 상태(available, negotiating, sold)를 포함합니다.
+- **Purchase** – 특정 아이템에 대해 생성되는 거래 방입니다. 구매자와 상태 정보를 가집니다.
+- **Message** – 거래 방 안에서 주고받는 채팅 메시지를 저장합니다.
+
+## 번역 동작
+
+`services/translator.py` 모듈이 번역을 담당합니다.
+
+- `deep_translator.GoogleTranslator` 사용을 시도합니다.
+- 실패 시에는 내장 사전에서 간단한 문장을 번역합니다.
+- 두 방식 모두 실패하면 "translation unavailable" 메시지로 감싸 원문을 그대로 보여줍니다.
+
+새로운 언어를 지원하고 싶다면 `SUPPORTED_LANGUAGES`와 사전 항목을 추가하면 됩니다.

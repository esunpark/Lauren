# Lauren Brick Market

레고 및 브릭 수집가를 위한 간단한 마켓플레이스로, [Bricklink](https://www.bricklink.com/v2/main.page)를 참고해 제작했습니다. 사용자는 원하는 언어로 프로필을 설정하고, 상품을 올려 판매하거나 다른 사용자의 상품을 구매할 수 있으며, 거래 중에는 자동 번역되는 채팅으로 소통할 수 있습니다.

## 주요 기능

1. **상품 등록/구매** – 로그인한 사용자는 상품을 등록할 수 있고, 다른 사용자의 상품에 대해 구매 채팅을 시작할 수 있습니다.
2. **거래 채팅** – 구매를 시작하면 판매자와 구매자만 접근할 수 있는 채팅 룸이 생성됩니다.
3. **자동 번역** – 채팅 메시지는 상대방의 설정 언어로 번역되어 보여집니다. `deep-translator` 라이브러리를 우선 사용하며, 네트워크 제한 시에는 소규모 오프라인 사전을 이용한 폴백을 제공합니다.

## 실행 방법

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app.py init-db
flask --app app.py seed-demo  # 선택: 데모 사용자/상품 생성
flask --app app.py run --debug
```

앱이 실행되면 <http://127.0.0.1:5000> 에 접속해 사용할 수 있습니다.

## 데이터 모델

- **User** – 사용자 이름, 선호 언어, 소개글을 저장합니다.
- **Item** – 판매 상품. 제목, 설명, 가격, 판매자, 상태(available, negotiating, sold)를 포함합니다.
- **Purchase** – 특정 아이템에 대해 생성되는 거래 방입니다. 구매자와 상태 정보를 가집니다.
- **Message** – 거래 방 안에서 주고받는 채팅 메시지를 저장합니다.

## 번역 동작

`services/translator.py` 모듈이 번역을 담당합니다.

- `deep_translator.GoogleTranslator` 사용을 시도합니다.
- 실패 시에는 내장 사전에서 간단한 문장을 번역합니다.
- 두 방식 모두 실패하면 "translation unavailable" 메시지로 감싸 원문을 그대로 보여줍니다.

새로운 언어를 지원하고 싶다면 `SUPPORTED_LANGUAGES`와 사전 항목을 추가하면 됩니다.

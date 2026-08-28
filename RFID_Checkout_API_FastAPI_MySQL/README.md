# RFID FastAPI + MySQL (Graduation Project Template)

이 프로젝트는 **RFID 계산대** 졸업작품을 위한 FastAPI + MySQL 서버 템플릿입니다.

## 1. 구조

```bash
rfid-fastapi-mysql-full/
├─ app/
│  ├─ __init__.py
│  ├─ main.py          # FastAPI 엔드포인트 (장바구니 + 스캔 포함)
│  ├─ crud.py          # DB CRUD 로직 (사용자 제공 코드)
│  ├─ models.py        # SQLAlchemy 모델 (사용자 제공 코드)
│  ├─ schemas.py       # Pydantic 스키마 (사용자 제공 코드)
│  └─ database.py      # DB 연결 (get_db)
├─ .env                # DB_URL 설정 (직접 비밀번호/DB명 맞게 수정)
├─ .vscode/
│  ├─ launch.json      # VSCode로 uvicorn 실행
│  └─ settings.json
├─ init_db.sql         # (선택) MySQL 테이블 생성 스크립트
└─ requirements.txt    # 필요한 파이썬 패키지
```

## 2. 설치 및 실행

```bash
# 1) 간편 실행 (Mac/Linux)
./run_server.sh

# 2) 수동 설치 및 실행
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# .env 파일 확인 (DB 설정 등)

# 서버 실행
python -m app.main
```

## 3. 주요 엔드포인트

- `GET  /health`               : 서버 상태 체크
- `GET  /products`             : 상품 목록
- `GET  /products-with-qty`    : 상품 + 재고 수량
- `POST /products`             : 새 상품 + 태그 등록
- `POST /products/{id}/tags`   : 기존 상품에 태그 추가

### 스캔 & 장바구니 (라즈베리 + 웹용)

- `POST /scan/start`
  - start.html에서 "한국어"/"English" 버튼 눌렀을 때 호출
  - 장바구니 초기화

- `POST /scan`
  - 단일/다중 태그 모두 처리
  - `{ "rfid": "TAG1" }` 또는 `{ "rfids": ["TAG1", "TAG2"] }`
  - 태그에 연결된 상품을 메모리 장바구니에 누적

- `POST /scan/confirm`
  - scan_guide(한/영)에서 "올려놓았습니다" 버튼을 눌렀을 때 호출

- `GET /cart`
  - pay.html / pay_en.html에서 1초마다 폴링
  - 현재 장바구니에 담긴 상품 목록 + 수량 + 가격 반환

### 수량 추가 (데모용)

- `POST /inventory/add`
  - add.html에서 사용
  - 상품명을 기준으로 찾아서, 가상의 in_stock RFID 태그를 여러 개 생성하여
    재고가 증가한 것처럼 보이게 함 (데모용 구현).

## 4. 주의사항

- 실제 UHF RFID 태그와 1:1 매핑을 엄밀하게 관리하고 싶다면
  `/inventory/add`를 **진짜 태그 등록 방식**으로 변경하는 것을 추천합니다.
- 현재 장바구니는 메모리(`current_cart`)에만 저장되므로,
  서버 재시작 시 장바구니 내용은 초기화됩니다.

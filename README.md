# RFID Smart Checkout

RFID Smart Checkout은 RFID 태그 기반 상품 인식, 무인마트 고객/직원 화면, FastAPI + MySQL 서버, 라즈베리파이 RFID 리더 연동, iOS YOLO/Aruco 비전 앱, GPT 기반 마트 AI 도우미를 함께 정리한 졸업작품 프로젝트 묶음입니다.

이 저장소는 여러 실험과 산출물을 하나로 모은 형태입니다. 실제 시연에서는 서버, 라즈베리파이 RFID 리더, 웹 화면, iOS 비전 앱이 서로 API로 연결됩니다.

## 프로젝트 목표

- RFID 태그를 이용해 상품을 빠르게 인식합니다.
- 고객용 화면에서 스캔, 장바구니, 결제 흐름을 제공합니다.
- 직원용 화면에서 상품 등록, 재고 확인, 삭제, 영수증, 매출 확인을 지원합니다.
- 라즈베리파이에서 UHF RFID 리더를 제어하고, 웹 화면이 사용할 수 있는 `/latest-tag`, `/tags`, `/scan/start`, `/scan/stop` API를 제공합니다.
- FastAPI 서버와 MySQL 데이터베이스로 상품, RFID 태그, 구매 이력, 재고 정보를 관리합니다.
- iOS 앱에서 카메라 프레임을 이용해 YOLO 또는 ArUco 기반 비전 인식 흐름을 실험합니다.
- GPT API와 MySQL 조회 도구를 연결해 무인마트 AI 도우미를 구성합니다.

## 전체 구성

```text
RFID/
├─ RFID_Checkout_API_FastAPI_MySQL/   # 메인 FastAPI + MySQL 서버
├─ RaspberryPi_RFID_Files/            # 라즈베리파이 RFID 리더 + 고객/직원 화면
├─ Graduation_Web_Screens/            # 졸업작품 웹 화면 HTML 묶음
├─ RFIDVisionIOSStarter_YOLO_iOS/     # iOS 카메라 + YOLO/Aruco 비전 앱
├─ GPT_Mart_AI_Assistant/             # GPT API + 무인마트 DB 질의 도우미
├─ RFID_DB_Dump_20260105/             # MySQL DB 덤프
├─ _Original_Zips/                    # 원본 압축 파일 보관
├─ tts.js                             # 고객용 TTS ON/OFF 및 태그 감지 음성 안내
├─ RFID_Smart_Checkout.pptx           # 발표자료
└─ RFID_Smart_Checkout_Demo.mp4       # 데모 영상
```

## 시스템 흐름

```text
고객 화면
  ↓ scan/start
라즈베리파이 RFID 리더
  ↓ latest-tag / tags
FastAPI 서버
  ↓ 상품/태그/장바구니/구매 이력 처리
MySQL DB
  ↓
직원 화면 / 매출 화면 / 영수증 화면
```

iOS 비전 앱은 별도 흐름으로 동작합니다.

```text
iPhone 또는 iPad 카메라
  ↓
YOLO / ArUco 인식
  ↓
서버 API 또는 온디바이스 추론
  ↓
상품 인식 보조 및 비전 테스트
```

## 1. RFID_Checkout_API_FastAPI_MySQL

메인 백엔드 서버입니다. FastAPI, SQLAlchemy, MySQL을 사용하며 RFID 계산대와 직원 관리 화면에서 사용하는 API를 제공합니다.

### 주요 역할

- 상품 목록 조회
- 상품별 재고 수량 조회
- RFID 태그 스캔 처리
- 장바구니 메모리 상태 관리
- 결제 및 구매 이력 저장
- 재입고 처리
- 상품 추가 및 RFID 태그 등록
- ArUco 마커와 상품 연결 조회
- GPT 기반 마트 AI 도우미 API
- ngrok 터널 생성

### 주요 파일

```text
RFID_Checkout_API_FastAPI_MySQL/
├─ app/
│  ├─ main.py          # FastAPI 엔드포인트
│  ├─ crud.py          # DB CRUD 로직
│  ├─ models.py        # SQLAlchemy 모델
│  ├─ schemas.py       # Pydantic 스키마
│  └─ database.py      # DB 연결 설정
├─ init_db.sql         # 초기 테이블 생성용 SQL
├─ requirements.txt    # Python 패키지 목록
├─ run_server.sh       # 서버 실행 스크립트
└─ check_db_connection.py
```

### 대표 API

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/health` | 서버 상태 확인 |
| `GET` | `/products` | 상품 목록 조회 |
| `GET` | `/products-with-qty` | 상품 + 재고 수량 조회 |
| `POST` | `/products` | 상품 등록 |
| `POST` | `/products/{product_id}/tags` | 기존 상품에 RFID 태그 추가 |
| `POST` | `/scan/start` | 장바구니 초기화 및 스캔 시작 상태 처리 |
| `POST` | `/scan` | 단일/다중 RFID 태그 스캔 처리 |
| `POST` | `/scan/confirm` | 고객이 상품을 올려놓았음을 확인 |
| `GET` | `/cart` | 현재 장바구니 조회 |
| `POST` | `/checkout` | 결제 처리 및 구매 이력 저장 |
| `GET` | `/purchase-history` | 구매 이력 및 매출 조회 |
| `GET` | `/latest-tag` | 최근 태그 조회 |
| `POST` | `/inventory/register-tag` | 재고/태그 등록 |
| `GET` | `/aruco/resolve/{marker_id}` | ArUco 마커와 상품 매핑 조회 |
| `POST` | `/api/chat` | 마트 AI 도우미 채팅 |

### 실행 예시

```bash
cd RFID_Checkout_API_FastAPI_MySQL
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

또는:

```bash
cd RFID_Checkout_API_FastAPI_MySQL
./run_server.sh
```

### 환경 변수

실제 DB 접속 정보와 API 키는 `.env`에 넣어 사용합니다. `.env`는 GitHub 업로드에서 제외됩니다.

필요한 대표 값:

```env
DB_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/rfid_database?charset=utf8mb4
OPENAI_API_KEY=your_openai_api_key
```

## 2. RaspberryPi_RFID_Files

라즈베리파이에서 사용하는 RFID 리더 제어 파일과 고객/직원 화면입니다. 원래 `캡스톤2` 압축 파일에 들어 있던 파일을 풀어서 정리한 폴더입니다.

### 주요 역할

- JRD-4035 UHF RFID 리더 제어
- `/dev/serial0` 또는 USB 시리얼 포트로 RFID 태그 읽기
- RFID 출력 전력 조절로 인식 범위 조절
- 한 세션 동안 읽힌 태그 중복 제거
- Flask 로컬 API 제공
- 고객 화면과 직원 화면에서 RFID 태그 값을 가져갈 수 있게 연결

### 주요 파일

```text
RaspberryPi_RFID_Files/
├─ start.py      # 라즈베리파이 RFID 리더 + Flask API
├─ 고객/
│  ├─ first.html
│  ├─ second.html
│  ├─ third.html
│  ├─ fourth.html
│  └─ mart_app.py
└─ 직원/
   ├─ add.html
   ├─ check.html
   ├─ del.html
   ├─ receipt.html
   ├─ sales.html
   └─ startsf.html
```

### 라즈베리파이 API

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/latest-tag` | 마지막으로 새로 인식된 태그 1개 반환 |
| `GET` | `/tags` | 현재 세션에서 인식된 모든 태그 목록 반환 |
| `POST` | `/scan/start` | 스캔 시작 및 세션 상태 초기화 |
| `POST` | `/scan/stop` | 스캔 중지 |

### 라즈베리파이 실행 예시

```bash
cd RaspberryPi_RFID_Files
python3 start.py
```

기본 설정은 `start.py` 안에서 조정합니다.

```python
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 115200
TX_POWER_DBM = 7
POLL_COUNT = 15
```

USB RFID 동글을 사용할 경우 `SERIAL_PORT`를 `/dev/ttyUSB0` 등으로 변경해야 할 수 있습니다.

## 3. Graduation_Web_Screens

졸업작품용 웹 화면 HTML 묶음입니다. 고객 시작 화면, 스캔 화면, 결제 화면, 관리자 화면, 상품 추가/삭제 화면 등을 빠르게 확인할 수 있습니다.

```text
Graduation_Web_Screens/
├─ first.html
├─ second.html
├─ third.html
├─ fourth.html
├─ manager.html
├─ add.html
├─ delete.html
└─ code.html
```

## 4. RFIDVisionIOSStarter_YOLO_iOS

iPhone/iPad 카메라를 사용해 YOLO 또는 ArUco 기반 인식을 실험하는 iOS 앱 프로젝트입니다.

### 주요 역할

- 카메라 권한 요청 및 세션 관리
- 실시간 프레임 처리
- 온디바이스 YOLO 모델 연결 준비
- 서버 기반 YOLO 추론 API 호출
- Bounding Box 오버레이 표시
- ArUco 인식 흐름 확장 준비

### 주요 구조

```text
RFIDVisionIOSStarter_YOLO_iOS/
├─ RFIDVisionIOSStarter.xcodeproj
├─ OnDeviceModelGuide.md
└─ RFIDVisionIOSStarter/
   ├─ App/
   ├─ Camera/
   ├─ Detectors/
   ├─ Models/
   ├─ Resources/
   ├─ Services/
   ├─ ViewModels/
   └─ Views/
```

### 모델 파일 위치

온디바이스 YOLO 모델은 아래 폴더에 넣는 구조입니다.

```text
RFIDVisionIOSStarter/Resources/Models/
```

사용 가능한 모델 파일명 예:

```text
YOLOv8n.mlpackage
YOLOv8n.mlmodel
```

## 5. GPT_Mart_AI_Assistant

OpenAI API와 MySQL 데이터베이스 조회 함수를 연결한 무인마트 AI 도우미 프로젝트입니다.

### 주요 역할

- GPT API 호출
- MySQL `rfid_database` 조회
- 상품 위치, 상품 정보, 재고, 결제 안내 등 마트 도우미 응답 생성
- FastAPI 기반 웹 채팅 화면 제공

### 주요 파일

```text
GPT_Mart_AI_Assistant/
├─ main.py
├─ mart_app.py
├─ requirements.txt
├─ run.sh
├─ run_mart.sh
├─ templates/
│  └─ index.html
└─ saved_chats/
```

`saved_chats/`는 개인 대화 로그가 포함될 수 있으므로 GitHub 업로드에서는 제외됩니다.

## 6. tts.js

고객 화면에 음성 안내 ON/OFF 버튼을 추가하고, RFID 태그가 새로 감지되면 음성으로 안내하는 공통 스크립트입니다.

### 주요 기능

- 브라우저 `localStorage`로 TTS ON/OFF 상태 저장
- 상단 고정 음성 안내 버튼 자동 주입
- Web Speech API를 이용한 한국어 음성 안내
- `/latest-tag`를 0.5초마다 폴링
- 새 태그 감지 시 "상품이 추가되었습니다." 안내

### 서버 주소 변경

`tts.js` 상단의 `SERVER_URL` 중 환경에 맞는 값 하나만 활성화합니다.

```javascript
// 같은 장치 테스트
// const SERVER_URL = "http://127.0.0.1:5000";

// 라즈베리파이 내부 IP
const SERVER_URL = "http://192.168.47.80:5000";

// ngrok 외부 접속
// const SERVER_URL = "https://xxxxx.ngrok-free.app";
```

HTML에서 사용할 때는 아래처럼 추가합니다.

```html
<script src="../tts.js"></script>
```

경로는 HTML 파일 위치에 맞게 조정해야 합니다.

## 7. DB 덤프

`RFID_DB_Dump_20260105`에는 MySQL DB 백업 SQL이 들어 있습니다.

```text
RFID_DB_Dump_20260105/
├─ rfid_dabase_products.sql
├─ rfid_dabase_purchase_history.sql
└─ rfid_dabase_rfid_tags.sql
```

테이블 예:

- `products`
- `rfid_tags`
- `purchase_history`

## 발표 자료

- `RFID_Smart_Checkout.pptx`: 발표자료
- `RFID_Smart_Checkout_Demo.mp4`: 데모 영상
- `_Original_Zips/`: 원본 압축 파일 보관

## 설치 전 준비물

- Python 3.9 이상
- MySQL 또는 MariaDB
- 라즈베리파이
- JRD-4035 UHF RFID 리더 또는 호환 RFID 리더
- iPhone/iPad 및 Xcode
- OpenAI API 키
- ngrok 계정 또는 외부 접속 환경

## 보안 주의

이 저장소에는 `.env`, 가상환경, 캐시, 개인 대화 로그가 올라가지 않도록 `.gitignore`가 설정되어 있습니다.

GitHub에 올리기 전에 특히 아래 파일은 포함하지 않습니다.

- `.env`
- `.env.*`
- `venv/`
- `.venv/`
- `__pycache__/`
- `.DS_Store`
- `saved_chats/`
- Xcode `xcuserdata/`

코드 안에 데모용 DB 비밀번호나 로컬 IP가 남아 있을 수 있습니다. 실제 배포 전에는 환경 변수로 분리하는 것을 권장합니다.

## 현재 상태

- RFID 원본 프로젝트들은 `/Users/khj/Desktop/RFID` 아래에 실제 폴더로 이동되어 있습니다.
- 라즈베리파이용 `캡스톤2` 압축 파일은 `RaspberryPi_RFID_Files`로 정리되어 있습니다.
- 원본 압축 파일은 `_Original_Zips`에 보관되어 있습니다.
- 고객용 음성 안내 스크립트는 `tts.js`로 추가되어 있습니다.

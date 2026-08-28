# GPT LLM Starter (Python)

이 프로젝트는 OpenAI GPT API를 **바로 실행해볼 수 있는 최소 예제**입니다.  
로컬에서 간단한 터미널 챗봇을 돌려보면서 LLM 연동 구조를 확인할 수 있습니다.

## 1. 준비물

- Python 3.9 이상
- OpenAI API 키

> ⚠️ 보안을 위해 **키는 `.env` 파일에만 넣고, 코드나 깃허브에 올리지 마세요.**

---

## 2. 설치 방법

```bash
# 1) 폴더로 이동
cd gpt-llm-starter

# 2) 가상환경 생성 및 활성화 (macOS / Linux)
python3 -m venv venv
source venv/bin/activate

# 3) 패키지 설치
pip install -r requirements.txt
```

---

## 3. API 키 설정

`.env.example` 파일을 복사해서 `.env`를 만든 뒤,  
`OPENAI_API_KEY`에 **본인 키를 입력**하세요.

```bash
cp .env.example .env
```

`.env` 내용 예시:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

> 실제 키는 GitHub에 올리지 말고 로컬 `.env` 파일에만 저장하세요.

---

## 4. 실행 방법

```bash
# 가상환경 활성화 후
python main.py
```

실행 화면 예시:

```text
✅ GPT LLM CLI 시작!
종료하려면 'quit', 'exit', 'q' 중 하나를 입력하세요.

You: 안녕
Assistant: 안녕하세요! 무엇을 도와드릴까요?

You:
```

터미널에서 바로 GPT와 대화할 수 있습니다.

---

## 5. 구조 설명

```text
gpt-llm-starter/
├─ main.py          # GPT API 호출하는 실제 실행 코드
├─ requirements.txt # 필요한 파이썬 패키지 목록
├─ .env.example     # 환경 변수 템플릿 (API 키 자리)
└─ README.md        # 사용 방법 설명
```

---

## 6. 다음 확장 아이디어

- FastAPI 서버로 감싸서 `/chat` 같은 HTTP 엔드포인트 만들기
- 대화 로그를 MySQL에 저장해서 분석/추천 기능 만들기
- 시스템 프롬프트를 바꿔서 “전문 도메인 보조 AI” 만들기 (예: 코딩 도우미, 쇼핑 도우미 등)

이 zip만 풀어서 실행해보고, 그 다음 단계로 **네 졸업 작품 구조(FastAPI + MySQL + LLM)**로 확장하면 됩니다.

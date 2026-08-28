#!/bin/bash
# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 (존재하는 경우)
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# 필수 패키지 설치 확인 및 설치
echo "Installing/Updating required packages..."
pip install -r requirements.txt

# 기존에 실행중인 백그라운드 uvicorn이 있다면 먼저 종료 (선택사항, 포트 충돌 방지)
pkill -f "uvicorn mart_app:app"

# FastAPI 서버 백그라운드 실행
echo "Starting FastAPI server on port 8000..."
uvicorn mart_app:app --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

# 잠시 서버가 뜰 때까지 대기
sleep 2

# Ngrok 실행 - 8000 포트를 노출
echo "Starting ngrok on port 8000..."
ngrok http 8000

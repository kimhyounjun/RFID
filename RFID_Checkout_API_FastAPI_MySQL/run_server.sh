#!/bin/bash
cd "$(dirname "$0")"

# 가상환경 없으면 생성
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 가상환경 활성화
source .venv/bin/activate

# 패키지 설치 확인 (uvicorn 없으면 설치)
if ! pip freeze | grep -q "uvicorn"; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting server..."
# ngrok 로그 등 보이게 실행
/Users/khj/졸작/11-22\ api/.venv/bin/python -m app.main

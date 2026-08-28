#!/bin/bash
# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
source venv/bin/activate

# 메인 스크립트 실행
python main.py

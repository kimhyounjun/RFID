#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JRD-4035 + Flask + 다중인식 + 범위(출력 전력) 조절 버전

- g.py 에서 아래 함수들을 import 해서 사용:
  - set_tx_power(ser, db_value)
  - poll_multiple(ser, count=20)
  - get_version(ser)

- 범위(읽히는 거리)를 줄이고 싶으면
  TX_POWER_DBM 값을 줄이면 됨 (아래 참고)
"""

import serial
import time
import threading
import sys
from flask import Flask, jsonify, make_response

# g.py 에서 프로토콜 관련 함수들 import
from g import set_tx_power, poll_multiple, get_version

# ─────────────────────────────────────
# 1. 기본 시리얼 & 전력/폴링 설정
# ─────────────────────────────────────
# UART 로 쓴다면 "/dev/serial0"
# USB 동글이라면 "/dev/ttyUSB0" 등으로 변경
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 115200

# 📡 출력 전력 (dBm 단위, 내부에서는 *100 해서 사용)
#   - 26 dBm → 2600 (거의 최대, 범위 넓음)
#   - 20 dBm → 2000 (조금 줄어듦)
#   - 15 dBm → 1500 (더 줄어듦)
#   - 10 dBm → 1000 (가까운 태그 위주)
TX_POWER_DBM = 7  # ← 여기 숫자를 줄이면 범위가 줄어듦
TX_POWER_RAW = TX_POWER_DBM * 100  # set_tx_power 에 넣을 값

# 다중 폴링 시 한 번에 내부 반복 횟수
#   - 너무 크면 같은 태그를 계속 읽어서 멀리 있는 애들도 잘 잡힘
#   - 너무 작으면 가까운 태그도 빠르게 지나가면 못 잡을 수도 있음
POLL_COUNT = 15  # 예: 10~30 사이에서 테스트 추천

# 폴링 사이 대기 시간
LOOP_SLEEP_SEC = 0.05


# ─────────────────────────────────────
# 2. 전역 상태 (다중 인식용)
# ─────────────────────────────────────
SCAN_ENABLED = False          # /scan/start 로 True
LATEST_EPC = ""               # 마지막으로 새로 인식된 태그
SEEN_TAGS_SET = set()         # 한 세션 동안 중복 제거용
SEEN_TAGS_LIST = []           # 프론트로 넘길 순서 있는 리스트


# ─────────────────────────────────────
# 3. 리더기 스캔 스레드
#    → SCAN_ENABLED 동안 poll_multiple() 반복
# ─────────────────────────────────────
def read_uhf_tag_continuous():
    """
    별도 스레드에서 계속 돌면서:
      - SCAN_ENABLED 가 True 일 때만
      - poll_multiple(ser, POLL_COUNT) 호출
      - 새로 인식된 EPC 들을 전역 리스트/셋에 저장
    """
    global SCAN_ENABLED, LATEST_EPC, SEEN_TAGS_SET, SEEN_TAGS_LIST
    ser = None

    print("✨ UHF RFID (JRD-4035) 다중 인식 + 범위조절 스캐너 스레드 시작")

    while True:
        try:
            if not SCAN_ENABLED:
                time.sleep(LOOP_SLEEP_SEC)
                continue

            # 시리얼 연결 확인/재연결
            if ser is None or not ser.is_open:
                print(f"🔗 시리얼 포트 연결 시도... ({SERIAL_PORT})")
                ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                print("✅ 시리얼 포트 연결 성공")

                # ─────────────────────────────
                # 📡 1회만 송신 전력 세팅
                # ─────────────────────────────
                ok = set_tx_power(ser, TX_POWER_RAW)
                print(f"📡 TX POWER SET ({TX_POWER_DBM} dBm): {ok}")

                # 버전 정보 확인 (테스트용)
                ver = get_version(ser)
                print(f"📦 READER VERSION: {ver}")

            # ─────────────────────────────
            # 핵심: 다중 폴링 (범위는 TX_POWER_DBM 에서 사실상 결정)
            # ─────────────────────────────
            tags = poll_multiple(ser, count=POLL_COUNT)

            if not tags:
                time.sleep(LOOP_SLEEP_SEC)
                continue

            # 새로 인식된 EPC들만 전역 상태에 반영
            for epc in tags:
                if epc not in SEEN_TAGS_SET:
                    SEEN_TAGS_SET.add(epc)
                    SEEN_TAGS_LIST.append(epc)
                    LATEST_EPC = epc
                    print(f"🔍 새 태그 인식: {epc} (총 {len(SEEN_TAGS_LIST)}개)")

            time.sleep(LOOP_SLEEP_SEC)

        except serial.SerialException as e:
            print(f"🚨 시리얼 포트 오류: {e}. 3초 후 재시도.")
            if ser:
                ser.close()
            ser = None
            time.sleep(3)

        except Exception as e:
            print(f"🚨 예기치 못한 오류: {e}", file=sys.stderr)
            time.sleep(0.5)


# ─────────────────────────────────────
# 4. Flask 서버
#    - /scan/start  : 스캔 시작 + 상태 초기화
#    - /scan/stop   : 스캔 중지
#    - /latest-tag  : 마지막으로 인식된 태그 1개
#    - /tags        : 현재 세션에서 인식된 모든 태그 리스트
# ─────────────────────────────────────
app = Flask(__name__)


def cors_json(payload, status_code=200):
    resp = make_response(jsonify(payload), status_code)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.route("/latest-tag", methods=["GET"])
def get_latest_tag():
    """
    마지막으로 새로 인식된 태그 1개만 반환
    (기존 start5.py 와 동일한 인터페이스)
    """
    return cors_json({"tag_id": LATEST_EPC})


@app.route("/tags", methods=["GET"])
def get_all_tags():
    """
    이 세션(/scan/start 이후) 동안 인식된
    모든 EPC 리스트를 반환 (다중 인식 결과)
    """
    return cors_json({"tags": SEEN_TAGS_LIST})


@app.route("/scan/start", methods=["POST"])
def start_scan():
    global SCAN_ENABLED, LATEST_EPC, SEEN_TAGS_SET, SEEN_TAGS_LIST

    # 새 세션 시작 → 상태 초기화
    SCAN_ENABLED = True
    LATEST_EPC = ""
    SEEN_TAGS_SET = set()
    SEEN_TAGS_LIST = []

    print("▶️ SCAN_ENABLED = True (다중 스캔 시작, 상태 초기화)")
    return cors_json({"status": "scan_started", "tx_power_dbm": TX_POWER_DBM})


@app.route("/scan/stop", methods=["POST"])
def stop_scan():
    global SCAN_ENABLED
    SCAN_ENABLED = False
    print("⏸ SCAN_ENABLED = False (스캔 정지)")
    return cors_json({"status": "scan_stopped"})


# ─────────────────────────────────────
# 5. 메인
# ─────────────────────────────────────
if __name__ == "__main__":
    scanner_thread = threading.Thread(
        target=read_uhf_tag_continuous,
        daemon=True,
    )
    scanner_thread.start()

    print("🌐 Flask 로컬 서버 시작 (http://127.0.0.1:5000)")
    print(f"   - 사용 포트: {SERIAL_PORT}")
    print(f"   - TX 전력: {TX_POWER_DBM} dBm (내부값 {TX_POWER_RAW})")
    print(f"   - poll_multiple count: {POLL_COUNT}")
    app.run(host="127.0.0.1", port=5000, debug=False)

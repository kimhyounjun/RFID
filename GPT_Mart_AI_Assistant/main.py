from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
import time
import json
from datetime import datetime
from duckduckgo_search import DDGS
import pymysql

# 안전하게 디렉토리 생성
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# .env 파일 로드
load_dotenv()

# 환경 변수에서 설정 가져오기
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.4")

# OpenAI 클라이언트 생성
client = OpenAI(api_key=API_KEY)

# --- 도구(Tools) 정의 ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "실시간 정보나 날씨, 뉴스 등이 필요할 때 웹 검색을 수행합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 키워드 또는 질문 (예: '오늘 서울 날씨', '아이폰 16 출시일')",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "MySQL 데이터베이스(rfid_database)에 접근하여 데이터를 조회하거나 조작합니다. 어떤 테이블이 있는지 모를 땐 'SHOW TABLES;' 쿼리로 확인하고, 스키마를 모를 땐 'DESCRIBE 테이블명;' 쿼리로 확인하세요.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "실행할 올바른 SQL 구문 (예: 'SELECT * FROM users LIMIT 10')",
                    },
                },
                "required": ["query"],
            },
        },
    }
]

def search_web(query):
    """DuckDuckGo를 사용하여 웹 검색을 수행하고 결과를 반환합니다."""
    print(f"\n🔍 웹 검색 중: '{query}'...", end="", flush=True)
    try:
        results = DDGS().text(query, max_results=3)
        if results:
            summary = "\n".join([f"- {r['title']}: {r['body']} ({r['href']})" for r in results])
            print(" 완료!")
            return summary
        else:
            print(" 실패 (결과 없음)")
            return "검색 결과가 없습니다."
    except Exception as e:
        print(f" 오류 ({e})")
        return f"검색 중 오류 발생: {e}"

def execute_sql_query(query):
    """MySQL 데이터베이스에 SQL 쿼리를 실행하고 결과를 반환합니다."""
    print(f"\n💾 데이터베이스 조회 중: '{query}'...", end="", flush=True)
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='1234',
            database='rfid_database',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute(query)
            # SELECT 구문 등이면 결과 반환, 그 외엔 commit
            if query.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
                result = cursor.fetchall()
                print(" 완료!")
                return json.dumps(result, ensure_ascii=False, default=str)
            else:
                connection.commit()
                print(" 완료!")
                return "성공적으로 실행되었습니다."
    except Exception as e:
        print(f" 오류 ({e})")
        return f"데이터베이스 오류: {e}"

def save_conversation(messages):
    """대화 내용을 파일로 저장합니다."""
    if not messages or len(messages) <= 1:
        return

    ensure_directory("saved_chats")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"saved_chats/chat_{timestamp}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            for msg in messages:
                role = msg["role"].upper()
                content = msg.get("content") or "" # content가 None일 수 있음 (tool call 경우)
                
                # Tool calls가 있는 경우 표시
                if "tool_calls" in msg and msg["tool_calls"]:
                    for tool_call in msg["tool_calls"]:
                        f.write(f"[{role} - TOOL CALL: {tool_call.function.name}]\nArguments: {tool_call.function.arguments}\n\n")
                
                # 일반 메시지 내용
                if content:
                    f.write(f"[{role}]\n{content}\n\n")
        print(f"\n💾 대화 내용이 '{filename}'에 저장되었습니다.")
    except Exception as e:
        print(f"\n⚠️ 대화 저장 중 오류 발생: {e}")

def run_chat():
    print("✅ GPT LLM CLI 시작! (웹 검색 기능 포함 🌐)")
    print(f"사용 모델: {MODEL_NAME}")
    print("종료하려면 'quit', 'exit', 'q' 중 하나를 입력하세요.\n")

    system_prompt = (
        "너는 한국어로 대답하는 친절한 개발 도우미야. "
        "사용자가 최신 정보나 날씨 등을 물어보면 'search_web' 도구를 적극적으로 사용해. "
        "사용자가 데이터베이스나 장비(RFID 등)에 대해 물어보면 'execute_sql_query' 도구를 사용해서 mySQL DB 데이터를 확인한 뒤 대답해줘."
    )
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 종료합니다.")
            save_conversation(messages)
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 종료합니다.")
            save_conversation(messages)
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        
        # 1. AI에게 요청 (도구 사용 가능성 있음)
        try:
            # 스트리밍과 도구 호출을 함께 쓰려면 로직이 복잡해지므로, 
            # 일단 첫 호출은 stream=False로 하여 도구 사용 여부를 판단합니다.
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # 2. 도구 호출이 필요한 경우
            if tool_calls:
                # AI의 "나 도구 쓸래" 메시지를 대화 내역에 추가 (필수)
                messages.append(response_message)

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "search_web":
                        function_response = search_web(function_args.get("query"))
                    elif function_name == "execute_sql_query":
                        function_response = execute_sql_query(function_args.get("query"))
                    else:
                        function_response = "알 수 없는 도구 호출"
                        
                    # 도구 결과를 대화 내역에 추가
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    })

                # 3. 도구 결과를 바탕으로 최종 답변 스트리밍
                print("Assistant: ", end="", flush=True)
                stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    stream=True,
                )
                
                assistant_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content_chunk = chunk.choices[0].delta.content
                        print(content_chunk, end="", flush=True)
                        assistant_response += content_chunk
                print()

                messages.append({"role": "assistant", "content": assistant_response})

            # 4. 도구 호출이 없는 일반 답변인 경우
            else:
                print("Assistant: ", end="", flush=True)
                # 이미 받은 응답을 출력하거나, 다시 스트리밍으로 요청할 수도 있지만
                # 여기서는 그냥 받은 내용을 출력합니다 (단순화를 위해)
                # *더 자연스러운 경험을 위해 그냥 바로 출력합니다.*
                assistant_response = response_message.content
                print(assistant_response)
                messages.append({"role": "assistant", "content": assistant_response})

        except Exception as e:
            print(f"\n⚠️ API 호출 중 오류 발생: {e}")
            continue

if __name__ == "__main__":
    if not API_KEY:
        print("⚠️ OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
    else:
        run_chat()

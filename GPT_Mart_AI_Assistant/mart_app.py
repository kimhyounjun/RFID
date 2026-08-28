from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import pymysql
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Mart Application")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Setup Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    message: str

def get_db_connection():
    return pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='1234',
        database='rfid_database',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

import json

tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "MySQL 데이터베이스(rfid_database)에 접근하여 데이터를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "실행할 올바른 SQL 구문 (예: 'SELECT * FROM products LIMIT 5')",
                    },
                },
                "required": ["query"],
            },
        },
    }
]

def execute_sql_query_func(query_str: str):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query_str)
            if query_str.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE")):
                result = cursor.fetchall()
                connection.close()
                return json.dumps(result, ensure_ascii=False, default=str)
            else:
                connection.close()
                return "You can only execute READ queries in this context."
    except Exception as e:
        return f"데이터베이스 오류: {e}"

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        messages = [
            {"role": "system", "content": """
너는 무인마트를 도와주는 친절한 AI 도우미입니다.

말투는 딱딱하지 않고 부드럽고 따뜻하게 말합니다.
친근하지만 예의 있는 존댓말을 사용합니다.

답변은 읽기 쉽게 줄바꿈을 사용해 가독성을 높입니다.
불필요하게 길게 말하지 말고 핵심 정보만 정리해서 알려줍니다.

검색 규칙

사용자의 질문을 분석하여 'execute_sql_query' 도구로 상품 검색 시 다음 규칙을 반드시 따르세요.

1. 상품 검색은 products 테이블에서 수행합니다.
2. 상품명 검색은 반드시 LIKE 검색과 LOWER()를 사용합니다. (예: WHERE LOWER(product_name) LIKE '%사이다%')
3. 사용자가 상품 이름을 정확히 말하지 않아도 의미가 비슷하면 OR 조건으로 확장해서 검색합니다.
   (예: '콜라' -> LIKE '%콜라%' OR LIKE '%코카콜라%', '물' -> LIKE '%물%' OR LIKE '%삼다수%', '라면' -> LIKE '%라면%' OR LIKE '%신라면%')
4. 가격 조건이 있으면 price 컬럼을 사용합니다. (예: '2000원 이하' -> WHERE price <= 2000)
5. 재고 질문이면 quantity 컬럼을 사용합니다.
6. 카테고리 질문이면 category 컬럼을 사용합니다. (예: '음료 뭐 있어?' -> WHERE category = '음료')
7. 항상 다음 컬럼만 조회하세요: SELECT product_name, price, quantity
8. 항상 LIMIT 20을 추가하세요.

출력 형식 규칙

모든 상품 목록은 반드시 아래 마크다운 형식을 사용하세요.

각 상품은 다음 형식으로 출력합니다.

🛒 **상품명**

💰 가격: 가격원  
📦 재고: 재고개

상품 사이에는 반드시 한 줄 공백을 넣으세요.

예시

🛒 **사이다**

💰 가격: 1,200원  
📦 재고: 10개


🛒 **코카콜라 캔 250ml**

💰 가격: 1,500원  
📦 재고: 10개


절대 한 줄로 이어서 출력하지 마세요.
상품마다 줄바꿈을 유지하세요.

상품 정보를 모두 출력한 뒤 마지막 줄에 아래 버튼을 추가하세요.

[장바구니 담기]

사용자가 보기 편하게 안내하세요.

DB 구조
products (product_id, product_name, price, category, quantity, requires_staff)
rfid_tags (tag_id, product_id, status)
purchase_history
"""},
            {"role": "user", "content": req.message}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        
        response_message = response.choices[0].message
        
        # Check if the model wants to call a function
        if response_message.tool_calls:
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "execute_sql_query":
                    func_args = json.loads(tool_call.function.arguments)
                    query_result = execute_sql_query_func(func_args.get("query"))
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": query_result,
                    })
            
            # Second call to get the final response based on tool output
            second_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            return {"reply": second_response.choices[0].message.content}
        else:
            return {"reply": response_message.content}
            
    except Exception as e:
        print(f"Chat API Error: {e}")
        return {"reply": "죄송합니다, 잠시 후 다시 시도해주세요."}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM products ORDER BY product_id DESC")
            products = cursor.fetchall()
        connection.close()
    except Exception as e:
        products = []
        print(f"Error fetching products: {e}")

    return templates.TemplateResponse(
        request=request, name="index.html", context={"products": products}
    )

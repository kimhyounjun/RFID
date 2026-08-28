from typing import List, Dict, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from collections import defaultdict
from datetime import datetime, timedelta  # ← timedelta 사용

# 내부 모듈
from contextlib import asynccontextmanager
from pyngrok import ngrok
from .database import get_db, engine
from . import models, crud, schemas

models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) Start ngrok tunnel
    #    포트 8000번을 ngrok으로 노출
    #    (이미 ngrok에 로그인되어 있다면 그 계정 설정 따름)
    print("Starting ngrok tunnel...")
    
    # 🔥 기존 ngrok 프로세스 강제 종료 (중복 실행 방지)
    # pyngrok의 kill()만으로는 부족할 수 있어 시스템 명령어로 정리
    import os
    os.system("killall ngrok 2>/dev/null") 
    ngrok.kill()
    
    public_url = ngrok.connect(8000).public_url
    print(f"✅ ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:8000\"")

    # 2) Update config or print info if needed
    yield

    # 3) Shutdown logic (optional)
    #    앱 종료 시 ngrok도 같이 끌고 싶으면:
    # ngrok.disconnect(public_url)

app = FastAPI(title="RFID Checkout API (MySQL + Cart)", version="1.0.0", lifespan=lifespan)

# CORS 전체 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 메모리 기반 장바구니 및 최근 태그
current_cart: Dict[int, int] = {}
LATEST_TAG: str = ""
LATEST_TTS_TEXT: str = ""


# ------------------------------------------
# 기본 API
# ------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products", response_model=List[schemas.ProductOut])
def list_products(db: Session = Depends(get_db)):
    return crud.list_products(db)


@app.get("/products-with-qty", response_model=List[schemas.ProductWithQty])
def list_products_with_qty(db: Session = Depends(get_db)):
    """
    상품 + 재고 수량 + 성인인증 플래그까지 함께 내려주는 엔드포인트.
    ⚠ crud.list_products_with_qty 쿼리에서 Product.requires_staff도 SELECT 되도록 해야 함.
    """
    rows = crud.list_products_with_qty(db)
    return [
        schemas.ProductWithQty(
            product_id=r.product_id,
            product_name=r.product_name,
            price=r.price,
            category=r.category,
            qty=r.qty or 0,
            requires_staff=getattr(r, "requires_staff", False),  # 🔥 추가
        )
        for r in rows
    ]


@app.post("/scan-single", response_model=schemas.TagScanResult)
def scan_single(data: schemas.TagScanRequest, db: Session = Depends(get_db)):
    global LATEST_TAG
    LATEST_TAG = data.rfid

    tag, prod = crud.get_product_by_rfid_tag(db, data.rfid)
    if not tag:
        return {"found": False, "product": None, "status": None}
    out = schemas.ProductOut.model_validate(prod) if prod else None
    return {"found": True, "product": out, "status": tag.status}


@app.post("/purchase/{rfid}", response_model=schemas.ProductOut)
def purchase(rfid: str, db: Session = Depends(get_db)):
    tag, prod, err = crud.purchase_by_tag(db, rfid)
    if tag is None:
        raise HTTPException(status_code=404, detail="RFID not found")
    if err == "ALREADY_SOLD":
        raise HTTPException(status_code=409, detail="이미 판매된 태그입니다.")
    if not prod:
        raise HTTPException(status_code=409, detail="태그에 연결된 상품이 없습니다.")
    return prod


@app.put("/restock/{rfid}")
def restock_product(rfid: str, db: Session = Depends(get_db)):
    tag, prod, err = crud.restock_by_tag(db, rfid)
    if tag is None:
        raise HTTPException(status_code=404, detail="RFID not found")
    out = schemas.ProductOut.model_validate(prod) if prod else None
    return {"restocked": True, "rfid": rfid, "status": tag.status, "product": out}


@app.post("/products", response_model=schemas.ProductOut)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    """
    상품 생성 + 태그 등록. (관리자용)
    ProductCreate 안에 requires_staff 가 있다면 성인상품도 생성 가능.
    """
    prod = crud.create_product_with_tags(
        db=db,
        product_name=payload.product_name,
        price=payload.price,
        category=payload.category,
        tag_ids=payload.tags or [],
        # 필요하면 crud.create_product_with_tags 내부에서 requires_staff 처리
    )
    return prod


@app.post("/products/{product_id}/tags")
def add_tag(product_id: int, body: schemas.NewTag, db: Session = Depends(get_db)):
    tag, err = crud.add_tag_to_product(db, product_id, body.tag_id)
    if err == "TAG_ALREADY_EXISTS":
        raise HTTPException(status_code=409, detail="이미 존재하는 태그입니다.")
    if err == "PRODUCT_NOT_FOUND":
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    return {"added": True, "product_id": product_id, "tag_id": body.tag_id, "status": "in_stock"}
# ------------------------------------------
# ArUco API
# ------------------------------------------

@app.get("/aruco/resolve/{marker_id}", response_model=schemas.ArucoResolveResponse)
def resolve_aruco_marker(marker_id: int, db: Session = Depends(get_db)):
    tag, prod = crud.get_product_by_aruco_marker(db, marker_id)
    if not prod:
        raise HTTPException(
            status_code=404,
            detail="해당 ArUco 마커에 연결된 상품이 없습니다."
        )
    
    return schemas.ArucoResolveResponse(
        marker_id=marker_id,
        product_id=prod.product_id,
        product_name=prod.product_name,
        price=prod.price,
        category=prod.category,
        requires_staff=prod.requires_staff,
        quantity=prod.quantity
    )


# ------------------------------------------
# 스캔 & 장바구니
# ------------------------------------------

class ScanRequest(BaseModel):
    rfid: Optional[str] = None
    rfids: Optional[List[str]] = None


class CartItem(BaseModel):
    product_id: int
    name: str
    price: int
    quantity: int


@app.post("/scan/start")
def scan_start():
    current_cart.clear()
    global LATEST_TAG, LATEST_TTS_TEXT
    LATEST_TAG = ""
    LATEST_TTS_TEXT = ""
    return {"cleared": True}


@app.post("/scan", response_model=schemas.TagScanResult)
def scan_multi(data: ScanRequest, db: Session = Depends(get_db)):
    """
    여러 RFID 태그를 한 번에 스캔하는 엔드포인트.
    - 일반 상품: current_cart 에 수량 추가
    - 성인/직원 호출 상품 (requires_staff=True): 장바구니에 넣지 않고, 프론트에서 직원 호출 모달만 띄우도록 처리
    """
    global LATEST_TAG, LATEST_TTS_TEXT
    rfids: List[str] = []
    if data.rfid:
        rfids.append(data.rfid)
    if data.rfids:
        rfids.extend(data.rfids)

    if not rfids:
        return {"found": False, "product": None, "status": None}

    found_any = False
    first_product_out = None
    first_status = None

    for code in rfids:
        LATEST_TAG = code

        tag, prod = crud.get_product_by_rfid_tag(db, code)
        if not tag:
            continue

        found_any = True

        if prod:
            # 🔥 성인 인증/직원 호출 상품이면 장바구니에 추가하지 않는다.
            if getattr(prod, "requires_staff", False):
                # 여기서는 카트에 넣지 않고, 프론트에서 product.requires_staff 값을 보고
                # "직원 호출 / 성인인증" 모달을 띄우게 된다.
                pass
            else:
                pid = prod.product_id
                current_cart[pid] = current_cart.get(pid, 0) + 1

        if first_product_out is None:
            first_product_out = schemas.ProductOut.model_validate(prod) if prod else None
            first_status = tag.status

    if not found_any:
        return {"found": False, "product": None, "status": None}

    # --- 실시간 장바구니 TTS 요약문 생성 로직 시작 ---
    cart_names = []
    total_cnt = 0
    for c_pid, c_qty in list(current_cart.items()):
        c_prod = db.query(models.Product).filter(models.Product.product_id == c_pid).first()
        if c_prod:
            cart_names.append(c_prod.product_name)
        total_cnt += c_qty

    if cart_names:
        # 가독성을 위해 앞 2개 이름만 나열
        preview_str = ", ".join(cart_names[:2])
        has_more = " 등 " if len(cart_names) > 2 else " "
        summary_msg = f"{preview_str}{has_more}총 {total_cnt}개의 상품이 인식되었습니다."

        LATEST_TTS_TEXT = summary_msg
        # 무조건 클라이언트 발화가 유도되도록 유니크 타임스탬프 ID 할당
        LATEST_TAG = f"SCAN_{int(datetime.now().timestamp() * 1000)}"
    # --- 끝 ---

    return {"found": True, "product": first_product_out, "status": first_status}


@app.post("/scan/confirm")
def scan_confirm():
    return {"status": "ok"}


@app.get("/cart", response_model=Dict[str, List[CartItem]])
def get_cart(db: Session = Depends(get_db)):
    items: List[CartItem] = []

    for product_id, qty in list(current_cart.items()):
        prod = db.query(models.Product).filter(models.Product.product_id == product_id).first()
        if not prod:
            continue
        items.append(
            CartItem(
                product_id=product_id,
                name=prod.product_name,
                price=prod.price,
                quantity=qty,
            )
        )

    return {"items": items}


# ------------------------------------------
# 🔥 구매 기록 관리 (3000개 유지 + 90일 이전 기록 자동 삭제)
# ------------------------------------------

def trim_purchase_history(
    db: Session,
    max_count: int = 3000,     # 최대 3000개까지 유지
    max_age_days: int = 90,    # 90일(약 3달) 지난 기록 삭제
):
    # 🔥 1) 날짜 기준 삭제 (서버 로컬 시간 기준; 한국에서 실행 → KST)
    cutoff_dt = datetime.now() - timedelta(days=max_age_days)
    db.query(models.PurchaseHistory).filter(
        models.PurchaseHistory.purchased_at < cutoff_dt
    ).delete(synchronize_session=False)

    db.flush()

    # 🔥 2) 개수 기준 삭제 (최근 3000개만 유지)
    total = db.query(models.PurchaseHistory).count()
    if total > max_count:
        subq = (
            select(models.PurchaseHistory.id)
            .order_by(models.PurchaseHistory.purchased_at.desc())
            .offset(max_count)
        )
        old_ids = db.execute(subq).scalars().all()

        if old_ids:
            db.query(models.PurchaseHistory).filter(
                models.PurchaseHistory.id.in_(old_ids)
            ).delete(synchronize_session=False)


class CheckoutRequest(BaseModel):
    tag_ids: List[str]


@app.post("/checkout")
def checkout(request: CheckoutRequest, db: Session = Depends(get_db)):
    if not request.tag_ids:
        raise HTTPException(status_code=400, detail="tag_ids가 비어 있습니다.")

    tags = db.query(models.RfidTag).filter(
        models.RfidTag.tag_id.in_(request.tag_ids)
    ).all()

    if not tags:
        raise HTTPException(status_code=404, detail="해당 태그를 찾을 수 없습니다.")

    items_map = defaultdict(lambda: {"name": None, "unit_price": 0, "qty": 0})

    for tag in tags:
        prod = tag.product
        if not prod:
            continue

        # 여기까지 오면 이미 장바구니에 들어간 태그들만 결제 처리하는 단계라
        # requires_staff 상품은 애초에 카트에 안 넣었으므로 별도 체크는 필요 없음.
        pid = prod.product_id
        items_map[pid]["name"] = prod.product_name
        items_map[pid]["unit_price"] = prod.price or 0
        items_map[pid]["qty"] += 1

    items_list = list(items_map.values())
    total_price = sum(item["unit_price"] * item["qty"] for item in items_list)

    # 🔥 구매 기록 DB 저장 (서버 로컬 시간 사용 → 한국이면 KST)
    history = models.PurchaseHistory(
        purchased_at=datetime.now(),
        total_price=total_price,
        items=items_list,
    )
    db.add(history)

    try:
        # 태그 삭제
        for tag in tags:
            db.delete(tag)

        # 🔥 90일 + 3000개 유지 규칙 적용
        trim_purchase_history(db)

        db.commit()
        current_cart.clear()
        global LATEST_TAG, LATEST_TTS_TEXT
        LATEST_TAG = ""
        LATEST_TTS_TEXT = ""

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"결제 처리 중 오류 발생: {e}")

    return {
        "status": "ok",
        "total_price": total_price,
        "items": items_list,
    }


# ------------------------------------------
# 🔥 구매 기록 조회 (전체 반환 + 날짜 필터 + 페이징)
# ------------------------------------------

@app.get("/purchase-history")
def get_purchase_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    date: Optional[str] = None,
    all: bool = False,  # 🔥 전체 요청 모드
    db: Session = Depends(get_db),
):
    query = db.query(models.PurchaseHistory)

    # 🔥 all=true → 전체 기록 반환 (프론트에서 페이징)
    if all:
        return (
            query.order_by(models.PurchaseHistory.purchased_at.desc()).all()
        )

    # 날짜 필터
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="date는 YYYY-MM-DD 형식이어야 합니다.")
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())
        query = query.filter(
            models.PurchaseHistory.purchased_at >= start_dt,
            models.PurchaseHistory.purchased_at <= end_dt,
        )

    rows = (
        query.order_by(models.PurchaseHistory.purchased_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return rows


# ------------------------------------------
# 라즈베리 ↔ 웹 연동
# ------------------------------------------

class ScanTagRequest(BaseModel):
    tag_id: str


@app.post("/scan-tag")
def scan_tag(data: ScanTagRequest):
    global LATEST_TAG
    LATEST_TAG = data.tag_id
    return {"status": "ok", "tag_id": LATEST_TAG}


@app.get("/latest-tag")
def get_latest_tag():
    return {"tag_id": LATEST_TAG, "message": LATEST_TTS_TEXT}


# ------------------------------------------
# 태그 직접 등록 API
# ------------------------------------------

class RegisterTagRequest(BaseModel):
    tag_id: str
    product_name: str
    price: Optional[int] = None
    category: Optional[str] = None
    requires_staff: Optional[bool] = None  # 🔥 선택적으로 성인상품 여부도 같이 등록 가능


@app.post("/inventory/register-tag")
def register_tag(body: RegisterTagRequest, db: Session = Depends(get_db)):
    existing = db.query(models.RfidTag).filter(
        models.RfidTag.tag_id == body.tag_id
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="이미 등록된 태그입니다.")

    product = (
        db.query(models.Product)
        .filter(models.Product.product_name == body.product_name)
        .first()
    )

    if not product:
        product = models.Product(
            product_name=body.product_name,
            price=body.price or 0,
            category=body.category or "",
            # 🔥 요청에서 명시하면 그 값 사용, 아니면 기본 False
            requires_staff=bool(body.requires_staff) if body.requires_staff is not None else False,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

    new_tag = models.RfidTag(
        tag_id=body.tag_id,
        product_id=product.product_id,
        status="in_stock",
    )
    db.add(new_tag)
    db.commit()

    return {
        "registered": True,
        "tag_id": body.tag_id,
        "product_id": product.product_id,
        "product_name": product.product_name,
    }



# ------------------------------------------
# AI Chatbot Integration
# ------------------------------------------
import os
import json
import pymysql
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    admin: bool = False

def get_chat_db_connection():
    return pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='1234',
        database='rfid_database',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

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

def execute_sql_query_func(query_str: str, admin: bool = False):
    try:
        connection = get_chat_db_connection()
        with connection.cursor() as cursor:
            q_upper = query_str.strip().upper()
            if q_upper.startswith(("SELECT", "SHOW", "DESCRIBE")):
                cursor.execute(query_str)
                result = cursor.fetchall()
                connection.close()
                return json.dumps(result, ensure_ascii=False, default=str)
            elif admin and q_upper.startswith(("UPDATE", "INSERT", "DELETE")):
                # 추가, 조회, 삭제 조건 구체화
                if "RFID_TAGS" in q_upper:
                    if q_upper.startswith("INSERT"):
                        connection.close()
                        return "보안 정책 위반: 태그 ID(rfid_tags)를 임의로 추가하는 것은 금지되어 있습니다."
                    if q_upper.startswith("UPDATE") and "TAG_ID" in q_upper:
                        connection.close()
                        return "보안 정책 위반: 태그 ID(tag_id) 값을 수정하는 것은 금지되어 있습니다."
                cursor.execute(query_str)
                connection.commit()
                affected = cursor.rowcount
                connection.close()
                return json.dumps({"success": True, "affected_rows": affected}, ensure_ascii=False)
            else:
                connection.close()
                return "권한이 없습니다. 관리자 모드에서만 수정 쿼리를 실행할 수 있습니다."
    except Exception as e:
        return f"데이터베이스 오류: {e}"

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        if req.admin:
            sys_prompt = """
너는 무인마트 관리자를 돕는 AI 어시스턴트입니다. 관리자 모드로 실행 중입니다.

말투는 명확하고 간결하게 합니다.

[조회 규칙]
사용자의 질문을 분석하여 'execute_sql_query' 도구로 상품 검색 시 다음 규칙을 반드시 따르세요.
1. 상품 검색은 products 테이블에서 수행합니다.
2. 상품명 검색은 반드시 LIKE 검색과 LOWER()를 사용합니다. (예: WHERE LOWER(product_name) LIKE '%사이다%')
3. 사용자가 상품 이름을 정확히 말하지 않아도 의미가 비슷하면 OR 조건으로 확장해서 검색합니다.
   (예: '콜라' -> LIKE '%콜라%' OR LIKE '%코카콜라%', '물' -> LIKE '%물%' OR LIKE '%삼다수%', '라면' -> LIKE '%라면%' OR LIKE '%신라면%')
4. 가격 조건이 있으면 price 컬럼을 사용합니다.
5. 재고 질문이면 quantity 컬럼을 사용합니다.
6. 카테고리 질문이면 category 컬럼을 사용합니다.
7. 항상 다음 컬럼만 조회하세요: SELECT product_name, price, quantity
8. 항상 LIMIT 20을 추가하세요.

[수정 규칙 - 관리자 전용]
1. 가격 수정: UPDATE products SET price = ? WHERE LOWER(product_name) LIKE '%?%'
2. 재고 수정: UPDATE products SET quantity = ? WHERE LOWER(product_name) LIKE '%?%'
3. 카테고리 수정: UPDATE products SET category = '?' WHERE LOWER(product_name) LIKE '%?%'
4. 수정 후 반드시 SELECT로 변경 결과를 확인하여 사용자에게 알려주세요.
5. UPDATE/DELETE 실행 전에는 WHERE 조건을 정확하게 지정하세요.
6. 🚨 주의 (RFID 권한): rfid_tags 테이블 조회(SELECT) 및 삭제(DELETE)는 가능합니다. 단, 임의로 태그를 추가(INSERT)하거나 태그 번호 자체(tag_id)를 다른 번호로 수정(UPDATE)하는 것은 보안 상 엄격히 금지됩니다. 사용자가 요청하면 정중히 권한이 없어 불가능하다고 안내하세요.

[매출 분석]
- purchase_history 테이블로 매출 집계 가능합니다. (purchased_at, total_price, items)

출력 형식 규칙
모든 상품 목록은 반드시 아래 마크다운 형식을 사용하세요.

각 상품은 다음 형식으로 출력합니다.

🛒 **상품명**

💰 가격: 가격원  
📦 재고: 재고개

상품 사이에는 반드시 한 줄 공백을 넣으세요.
절대 한 줄로 이어서 출력하지 마세요. 상품마다 줄바꿈을 유지하세요.

DB 구조
products (product_id, product_name, price, category, quantity, requires_staff)
rfid_tags (tag_id, product_id, status)
purchase_history
"""
        else:
            sys_prompt = """
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

DB 구조
products (product_id, product_name, price, category, quantity, requires_staff)
rfid_tags (tag_id, product_id, status)
purchase_history
"""
        messages = [
            {"role": "system", "content": sys_prompt},
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
                    query_result = execute_sql_query_func(func_args.get("query"), admin=req.admin)
                    
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


if __name__ == "__main__":
    import uvicorn
    # 💡 직접 실행 시: python -m app.main
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

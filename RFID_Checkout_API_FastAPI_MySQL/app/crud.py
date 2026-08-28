# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from typing import Optional, List
from .models import Product, RfidTag, ArucoTag

# ─────────────────────────────────────────────────────────
# 상품 목록 (기존)
def list_products(db: Session):
    return db.execute(select(Product)).scalars().all()

# ✅ [예시용 추가] 수량(= in_stock 상태의 태그 개수) 포함 상품 목록
def list_products_with_qty(db: Session):
    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            Product.price,
            Product.category,
            func.count(RfidTag.tag_id).label("qty"),
        )
        .select_from(Product)
        .outerjoin(
            RfidTag,
            and_(
                RfidTag.product_id == Product.product_id,
                (RfidTag.status == "in_stock") | (RfidTag.status.is_(None)),
            ),
        )
        .group_by(Product.product_id)
        .order_by(Product.product_id.asc())
    )
    return db.execute(stmt).all()  # list of Row(product_id=..., qty=...)

# 태그로 상품/태그 조회 (기존)
def get_product_by_rfid_tag(db: Session, tag_id: str):
    tag = db.execute(select(RfidTag).where(RfidTag.tag_id == tag_id)).scalar_one_or_none()
    if not tag:
        return None, None
    prod = None
    if tag.product_id is not None:
        prod = db.execute(select(Product).where(Product.product_id == tag.product_id)).scalar_one_or_none()
    return tag, prod

# 구매 처리: 태그 상태를 sold로 변경 (기존)
def purchase_by_tag(db: Session, tag_id: str):
    tag, prod = get_product_by_rfid_tag(db, tag_id)
    if tag is None:
        return None, None, "NOT_FOUND"
    if (tag.status or "").lower() == "sold":
        return tag, prod, "ALREADY_SOLD"
    tag.status = "sold"
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag, prod, None

# 재입고(상태 복구): 태그 상태를 in_stock으로 변경 (기존)
def restock_by_tag(db: Session, tag_id: str):
    tag, prod = get_product_by_rfid_tag(db, tag_id)
    if tag is None:
        return None, None, "NOT_FOUND"
    tag.status = "in_stock"
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag, prod, None

# ✅ [예시용 추가] 신규 상품 생성 (+ 선택적으로 초기 RFID 태그 목록 등록)
def create_product_with_tags(
    db: Session,
    product_name: str,
    price: int,
    category: Optional[str],
    tag_ids: Optional[List[str]],
):
    # 1) 상품 생성
    prod = Product(product_name=product_name, price=price, category=category)
    db.add(prod)
    db.commit()
    db.refresh(prod)

    # 2) 초기 태그들 등록 (모두 in_stock)
    if tag_ids:
        for t in tag_ids:
            db.add(RfidTag(tag_id=t, product_id=prod.product_id, status="in_stock"))
        db.commit()

    return prod

# ✅ [예시용 추가] 기존 상품에 RFID 태그 1개 추가
def add_tag_to_product(db: Session, product_id: int, tag_id: str):
    # 중복 태그 방지
    exists = db.execute(select(RfidTag).where(RfidTag.tag_id == tag_id)).scalar_one_or_none()
    if exists:
        return None, "TAG_ALREADY_EXISTS"

    prod = db.execute(select(Product).where(Product.product_id == product_id)).scalar_one_or_none()
    if not prod:
        return None, "PRODUCT_NOT_FOUND"

    tag = RfidTag(tag_id=tag_id, product_id=product_id, status="in_stock")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag, None

# ─────────────────────────────────────────────────────────
# ✅ ArUco 마커로 상품 조회
def get_product_by_aruco_marker(db: Session, marker_id: int):
    tag = db.execute(select(ArucoTag).where(ArucoTag.marker_id == marker_id)).scalar_one_or_none()
    if not tag:
        return None, None
    prod = None
    if tag.product_id is not None:
        prod = db.execute(select(Product).where(Product.product_id == tag.product_id)).scalar_one_or_none()
    return tag, prod

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,  # 🔥 추가: 성인상품 플래그용
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# ───────────────────────────────────────────────
# 상품 테이블
# ───────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    product_name: Mapped[str] = mapped_column(String(255))
    price: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 🔥 성인/직원 호출 여부 (DB의 TINYINT(1) NOT NULL DEFAULT 0 과 매핑)
    requires_staff: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # 재고 (수량) – 지금은 안 써도 DB에 컬럼 있으면 그대로 둬도 됨
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # 역참조 → RfidTag 리스트
    tags: Mapped[List["RfidTag"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )

    # 🔥 역참조 → ArucoTag 리스트
    aruco_tags: Mapped[List["ArucoTag"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


# ───────────────────────────────────────────────
# RFID 태그 테이블
# ───────────────────────────────────────────────
class RfidTag(Base):
    __tablename__ = "rfid_tags"

    tag_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.product_id"),
        nullable=True,
    )

    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stocked_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Product ↔ RfidTag 양방향 관계
    product: Mapped[Optional[Product]] = relationship(
        back_populates="tags",
    )


# ───────────────────────────────────────────────
# 구매 기록 테이블
# ───────────────────────────────────────────────
class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)

    # items: [{ name, unit_price, qty }, ...] 형태로 저장
    items: Mapped[Dict] = mapped_column(
        JSON,
        nullable=False,
    )


# ───────────────────────────────────────────────
# ArUco 마커 테이블
# ───────────────────────────────────────────────
class ArucoTag(Base):
    __tablename__ = "aruco_tags"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    
    marker_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.product_id"),
        nullable=True,
    )

    # Product ↔ ArucoTag 양방향 관계
    product: Mapped[Optional[Product]] = relationship(
        back_populates="aruco_tags",
    )

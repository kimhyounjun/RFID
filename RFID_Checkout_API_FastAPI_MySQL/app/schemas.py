from pydantic import BaseModel
from typing import Optional, List

# ✅ 상품 정보 출력용
class ProductOut(BaseModel):
    product_id: int
    product_name: str
    price: int
    category: Optional[str] = None

    class Config:
        from_attributes = True

# ✅ RFID 태그 스캔 요청
class TagScanRequest(BaseModel):
    rfid: str  # = tag_id

# ✅ RFID 태그 스캔 결과
class TagScanResult(BaseModel):
    found: bool
    product: Optional[ProductOut] = None
    status: Optional[str] = None

# ✅ [예시] 수량 포함 상품 출력용
class ProductWithQty(BaseModel):
    product_id: int
    product_name: str
    price: int
    category: Optional[str] = None
    qty: int

# ✅ [예시] 신규 상품 생성용
class ProductCreate(BaseModel):
    product_name: str
    price: int
    category: Optional[str] = None
    tags: Optional[List[str]] = None  # 초기 등록할 RFID 태그들 (선택)

# ✅ [예시] 기존 상품에 RFID 태그 추가용
class NewTag(BaseModel):
    tag_id: str

# ✅ ArUco 마커 조회 응답용
class ArucoResolveResponse(BaseModel):
    marker_id: int
    product_id: int
    product_name: str
    price: int
    category: Optional[str] = None
    requires_staff: bool
    quantity: int

    class Config:
        from_attributes = True

# routers/order_request.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import logging

# 로깅 설정 (오류만 로깅)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL과 KEY를 환경 변수로 설정해주세요.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# APIRouter 인스턴스 생성
router = APIRouter()

# 데이터 모델 정의
class OrderItem(BaseModel):
    product_name: str = Field(..., example="상품명1")
    quantity: int = Field(..., gt=0, example=2)
    price: float = Field(..., gt=0, example=15000.0)

class OrderRequest(BaseModel):
    customer_name: str = Field(..., example="홍길동")
    delivery_address: str = Field(..., example="서울특별시 강남구")
    phone_number: str = Field(..., example="010-1234-5678")
    order_date: str  # YYYY-MM-DD 형식의 문자열
    total_price: float = Field(..., gt=0, example=30000.0)
    items: List[OrderItem]

class OrderStatusUpdate(BaseModel):
    order_id: int = Field(..., example=123)

# 주문 요청 처리 엔드포인트
@router.post("/submitRequest", response_model=Dict[str, Any])
async def submit_order_request(order_request: OrderRequest):
    try:
        # RPC 함수 호출을 위한 아이템 데이터 준비 (리스트 형태)
        items_json = [item.dict() for item in order_request.items]
        logger.info("Submitting order with data: %s", order_request.dict())

        # RPC 함수 호출
        response = supabase.rpc("submit_order", {
            "customer_name": order_request.customer_name,
            "delivery_address": order_request.delivery_address,
            "phone_number": order_request.phone_number,
            "order_date": order_request.order_date,
            "total_price": order_request.total_price,
            "items": items_json,  # JSON 배열 형태로 전달
        }).execute()

        # RPC 호출 결과 로그
        logger.info("RPC Response: %s", response)
        logger.info("RPC Response Data: %s", response.data)
        rpc_error = getattr(response, 'error', None)
        logger.info("RPC Response Error: %s", rpc_error)

        # RPC 호출 결과 확인
        if rpc_error:
            logger.error("RPC 호출 오류: %s", rpc_error)
            raise HTTPException(status_code=500, detail="주문 요청 처리 중 오류가 발생했습니다.")

        # 반환 데이터 확인 (submit_order가 JSONB를 반환)
        if not response.data:
            logger.error("RPC 호출 결과가 비정상적입니다.")
            raise HTTPException(status_code=500, detail="주문 요청 처리 중 오류가 발생했습니다.")

        # response.data는 리스트로 반환되므로 첫 번째 요소를 가져옴
        order_info = response.data[0] if isinstance(response.data, list) else response.data
        logger.info("Order info: %s", order_info)

        return {
            "success": True,
            "message": "주문 요청이 성공적으로 처리되었습니다.",
            "order_info": order_info
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error("Exception: %s", e)
        raise HTTPException(status_code=500, detail="주문 요청 처리 중 오류가 발생했습니다.")

# 부품 타입별 아이템 가져오기 엔드포인트
@router.get("/items_by_type", response_model=Dict[str, List[Dict[str, Any]]])
async def get_items_by_type():
    try:
        # 'item' 테이블에서 필요한 필드 선택
        response = supabase.table("item").select("type, name, price").execute()

        # 응답 데이터 확인
        rpc_error = getattr(response, 'error', None)
        if rpc_error:
            logger.error("아이템 데이터 가져오기 오류: %s", rpc_error)
            raise HTTPException(status_code=500, detail="아이템 데이터를 가져오는 중 오류가 발생했습니다.")

        items_by_type = {}
        for item in response.data:
            item_type = item["type"]
            if item_type not in items_by_type:
                items_by_type[item_type] = []

            items_by_type[item_type].append({
                "name": item["name"],
                "price": item["price"]
            })

        return items_by_type
    except Exception as e:
        logger.error("Exception: %s", e)
        raise HTTPException(status_code=500, detail="아이템 데이터를 가져오는 중 오류가 발생했습니다.")

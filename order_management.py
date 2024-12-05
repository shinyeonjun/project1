# order_management.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)  # 개발 중: INFO, 배포 시: ERROR
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL과 KEY를 환경 변수로 설정해주세요.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI 라우터 설정
router = APIRouter()

class OrderStatusUpdate(BaseModel):
    order_id: int = Field(..., example=123)

# 주문 목록 조회
@router.get("/getOrders", response_model=dict)
async def get_orders():
    try:
        # orders 테이블과 customer 테이블 조인, 상태(status)가 0인 항목만 필터링
        orders_response = supabase.table('orders').select(
            'order_id, order_date, total_price, status, customer(customer_name, delivery_address, phone_number)'
        ).eq('status', 0).execute()

        # 응답 객체에서 data 확인
        if not orders_response or not hasattr(orders_response, 'data') or not isinstance(orders_response.data, list):
            logger.error(f"Unexpected response format: {orders_response}")
            raise HTTPException(status_code=500, detail="주문 데이터를 불러오는 중 오류가 발생했습니다.")

        # 데이터 구성
        orders = []
        for order in orders_response.data:
            customer = order.get('customer', {})
            orders.append({
                "order_id": order.get('order_id'),
                "order_date": order.get('order_date'),
                "total_price": order.get('total_price'),
                "status": order.get('status'),
                "customer_name": customer.get('customer_name', "미등록"),
                "delivery_address": customer.get('delivery_address', "미등록"),
                "phone_number": customer.get('phone_number', "미등록")
            })

        return {"success": True, "orders": orders}
    except Exception as e:
        logger.error(f"Exception in get_orders: {e}")
        raise HTTPException(status_code=500, detail="주문 데이터를 불러오는 중 오류가 발생했습니다.")

# 주문 승인
@router.post("/approveOrder", response_model=dict)
async def approve_order(order_update: OrderStatusUpdate):
    try:
        update_response = supabase.table('orders').update({"status": 1}).eq('order_id', order_update.order_id).execute()
        
        # 응답 객체의 모든 속성 로그로 출력 (디버깅용)
        logger.info(f"Approve Order Response: {update_response}")
        for attr in dir(update_response):
            if not attr.startswith("_"):
                logger.info(f"{attr}: {getattr(update_response, attr)}")
        
        # Supabase-Python 클라이언트의 APIResponse 객체 구조에 따라 처리
        # 'error' 속성이 없는 경우, 'data'와 'count'로 확인
        if hasattr(update_response, 'error') and update_response.error:
            logger.error(f"API 호출 오류: {update_response.error}")
            raise HTTPException(status_code=500, detail="주문 승인 중 오류가 발생했습니다.")
        
        # 업데이트된 행의 개수 확인
        if hasattr(update_response, 'count') and update_response.count == 0:
            logger.error(f"No rows updated for order_id {order_update.order_id}")
            raise HTTPException(status_code=404, detail="해당 주문을 찾을 수 없습니다.")
        
        return {"success": True, "message": "주문이 승인되었습니다."}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Exception in approve_order: {e}")
        raise HTTPException(status_code=500, detail="주문 승인 중 오류가 발생했습니다.")

# 주문 반려
@router.post("/rejectOrder", response_model=dict)
async def reject_order(order_update: OrderStatusUpdate):
    try:
        # PostgreSQL 함수 호출
        response = supabase.rpc('reject_order_function', {'p_order_id': order_update.order_id}).execute()
        
        # 응답 객체의 데이터 로깅 (디버깅용)
        logger.info(f"Reject Order Response: {response}")

        # Supabase-Python 클라이언트의 APIResponse 객체 구조에 따라 처리
        if not response.data:
            logger.error(f"RPC 함수 반환값이 False입니다. order_id: {order_update.order_id}")
            raise HTTPException(status_code=500, detail="주문 반려 중 오류가 발생했습니다.")
        
        # 'response.data'가 True일 경우 성공 처리
        if response.data is True:
            logger.info(f"Order {order_update.order_id} successfully rejected.")
            return {"success": True, "message": "주문이 반려되었습니다."}
        else:
            # 예상치 못한 값이 반환된 경우
            logger.error(f"Unexpected RPC response: {response.data}")
            raise HTTPException(status_code=500, detail="주문 반려 처리 중 예상치 못한 오류가 발생했습니다.")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Exception in reject_order: {e}")
        raise HTTPException(status_code=500, detail="주문 반려 중 오류가 발생했습니다.")


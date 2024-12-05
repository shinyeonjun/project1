from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# 로깅 설정
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

# FastAPI 라우터 설정
router = APIRouter()

# 요청 데이터 모델 정의
class MarkAsCompletedRequest(BaseModel):
    order_id: int

@router.get("/getApprovedOrders", response_model=dict)
async def get_approved_orders():
    try:
        # Orders 데이터 가져오기
        orders_response = supabase.table("orders").select("*").eq("status", 1).execute()
        orders = orders_response.data

        if not orders:
            logger.info("승인된 주문이 없습니다.")
            return {"success": True, "orders": []}

        # Customer 데이터 매핑
        customer_ids = [order["customer_id"] for order in orders]
        customers_response = supabase.table("customer").select("*").in_("customer_id", customer_ids).execute()
        customers = {customer["customer_id"]: customer["customer_name"] for customer in customers_response.data}

        # Order Items 데이터 매핑
        order_ids = [order["order_id"] for order in orders]
        order_items_response = supabase.table("order_items").select("*").in_("order_id", order_ids).execute()
        order_items_map = {}
        for item in order_items_response.data:
            if item["order_id"] not in order_items_map:
                order_items_map[item["order_id"]] = []
            order_items_map[item["order_id"]].append({
                "product_name": item["product_name"],
                "quantity": item["quantity"]
            })

        # 데이터 조합 (그룹화된 형태로 반환)
        grouped_orders = []
        for order in orders:
            customer_name = customers.get(order["customer_id"], "미등록")
            items = order_items_map.get(order["order_id"], [])
            grouped_orders.append({
                "order_id": order["order_id"],
                "order_date": order["order_date"],
                "total_price": order["total_price"],
                "status": order["status"],
                "customer_name": customer_name,
                "items": items,  # 항목을 배열로 반환
            })

        logger.info(f"Grouped Orders: {grouped_orders}")
        return {"success": True, "orders": grouped_orders}

    except Exception as e:
        logger.error(f"Exception in get_approved_orders: {e}")
        raise HTTPException(status_code=500, detail="승인된 주문 데이터를 불러오는 중 오류가 발생했습니다.")


# 배송 완료 처리
@router.post("/markAsCompleted", response_model=dict)
async def mark_as_completed(request: MarkAsCompletedRequest):
    try:
        # 요청 데이터에서 order_id 추출
        order_id = request.order_id

        # 1. 해당 order_id로 orders 데이터 가져오기
        order_response = supabase.table("orders").select("total_price, status").eq("order_id", order_id).single().execute()
        order_data = order_response.data

        if not order_data:
            raise HTTPException(status_code=404, detail="해당 주문을 찾을 수 없습니다.")

        if order_data["status"] != 1:
            raise HTTPException(status_code=400, detail="이미 처리된 주문입니다.")

        # 2. sales 테이블에 total_price 저장
        total_price = order_data["total_price"]
        sale_date = datetime.now().date().isoformat()  # 문자열로 변환

        sales_response = supabase.table("sales").insert({
            "sale_date": sale_date,
            "total_price": total_price
        }).execute()

        if not sales_response.data:
            raise HTTPException(status_code=500, detail="매출 데이터를 저장하는 중 오류가 발생했습니다.")

        # 3. order_items 테이블의 관련 데이터 삭제
        delete_items_response = supabase.table("order_items").delete().eq("order_id", order_id).execute()

        if not delete_items_response.data:
            raise HTTPException(status_code=500, detail="order_items 데이터를 삭제하는 중 오류가 발생했습니다.")

        # 4. orders 테이블의 해당 주문 삭제
        delete_response = supabase.table("orders").delete().eq("order_id", order_id).execute()

        if not delete_response.data:
            raise HTTPException(status_code=500, detail="orders 데이터를 삭제하는 중 오류가 발생했습니다.")

        logger.info(f"Order {order_id} marked as completed, saved to sales, and deleted from orders.")
        return {"success": True, "message": "판매 완료 및 매출 데이터 저장 완료"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Exception in mark_as_completed: {e}")
        raise HTTPException(status_code=500, detail="판매 완료 처리 중 오류가 발생했습니다.")

@router.get("/getPendingOrder")
async def get_pending_orders():
    try:
        orders_response = supabase.table("orders").select("*").eq("status", 0).execute()
        orders = orders_response.data

        if not orders:
            return {"success": True, "orders": []}

        customer_ids = {order["customer_id"] for order in orders}
        customers_response = supabase.table("customer").select("customer_id, customer_name").in_("customer_id", list(customer_ids)).execute()
        customers = {customer["customer_id"]: customer["customer_name"] for customer in customers_response.data}

        order_ids = {order["order_id"] for order in orders}
        order_items_response = supabase.table("order_items").select("order_id, product_name, quantity").in_("order_id", list(order_ids)).execute()
        order_items_map = {}
        for item in order_items_response.data:
            order_items_map.setdefault(item["order_id"], []).append({
                "product_name": item["product_name"],
                "quantity": item["quantity"]
            })

        grouped_orders = [
            {
                "order_id": order["order_id"],
                "customer_name": customers.get(order["customer_id"], "미등록"),
                "order_date": order["order_date"],
                "total_price": order["total_price"],
                "status": order["status"],
                "items": order_items_map.get(order["order_id"], [])
            }
            for order in orders
        ]

        return {"success": True, "orders": grouped_orders}
    except Exception as e:
        logger.error(f"Error fetching pending orders: {e}")
        return {"success": False, "error": "데이터를 불러오는 중 오류가 발생했습니다."}

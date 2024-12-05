from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 라우터 설정
router = APIRouter()

# Pydantic 모델 정의
class PurchaseRequest(BaseModel):
    purchase_id: int

@router.get("/getApprovedPurchases")
async def get_approved_purchases():
    try:
        response = supabase.table("purchase").select("*").eq("status", 1).execute()
        purchases = response.data

        if not purchases:
            return {"success": False, "error": "현재 배송 중인 구매 내역이 없습니다."}

        return {"success": True, "purchases": purchases}

    except Exception as e:
        return {"success": False, "error": f"오류 발생: {str(e)}"}

@router.get("/getPendingPurchases")
async def get_pending_purchases():
    try:
        response = supabase.table("purchase").select("*").eq("status", 0).execute()
        purchases = response.data

        if not purchases:
            return {"success": False, "error": "승인 대기중인 요청이 없습니다."}

        return {"success": True, "purchases": purchases}

    except Exception as e:
        return {"success": False, "error": f"오류 발생: {str(e)}"}

@router.post("/markAsCompleted")
async def mark_as_completed(request: PurchaseRequest):
    try:
        # Step 1: 요청에서 purchase_id 추출
        purchase_id = request.purchase_id

        # Step 2: purchase 테이블에서 데이터 조회
        purchase_response = supabase.table("purchase").select("*").eq("purchase_id", purchase_id).execute()
        purchase_data = purchase_response.data

        if not purchase_data:
            return {"success": False, "error": "해당 ID의 데이터를 찾을 수 없습니다."}

        # 조회된 첫 번째 데이터 가져오기
        purchase_record = purchase_data[0]

        # Step 3: item 테이블에서 동일한 이름과 타입의 아이템이 있는지 확인
        item_name = purchase_record.get('name')
        item_type = purchase_record.get('type')
        purchase_quantity = purchase_record.get('quantity')
        purchase_total_price = purchase_record.get('total_price')
        purchase_supply = purchase_record.get('supply')

        if not item_name or not item_type:
            return {"success": False, "error": "구매 항목에 이름 또는 타입이 없습니다."}

        # 단가 계산
        if purchase_quantity and purchase_quantity > 0:
            purchase_price = purchase_total_price / purchase_quantity
        else:
            return {"success": False, "error": "구매 항목의 수량이 0이거나 없습니다."}

        # Step 4: item 테이블에서 동일한 아이템 확인
        item_response = supabase.table("item").select("*").eq("name", item_name).eq("type", item_type).execute()
        existing_items = item_response.data

        if existing_items:
            # 동일한 이름과 타입의 아이템이 존재하는 경우 수량과 공급처 업데이트
            existing_item = existing_items[0]
            new_quantity = existing_item['quantity'] + purchase_quantity

            # 가격 업데이트 (선택 사항: 평균 단가 계산)
            new_price = (existing_item['price'] * existing_item['quantity'] + purchase_price * purchase_quantity) / new_quantity

            # 공급처 업데이트 (필요에 따라 처리)
            new_supply = purchase_supply  # 최신 공급처로 업데이트

            # 아이템 업데이트
            update_response = supabase.table("item").update({
                'quantity': new_quantity,
                'price': new_price,
                'supply': new_supply
            }).eq('item_id', existing_item['item_id']).execute()

            if not update_response.data:
                return {"success": False, "error": "기존 아이템 업데이트 중 오류가 발생했습니다."}
        else:
            # 동일한 이름과 타입의 아이템이 없는 경우 새로 삽입
            item_data = {
                'name': item_name,
                'type': item_type,
                'quantity': purchase_quantity,
                'price': purchase_price,
                'supply': purchase_supply
            }

            # item 테이블에 데이터 삽입
            insert_response = supabase.table("item").insert(item_data).execute()

            if not insert_response.data:
                return {"success": False, "error": "item 테이블로 데이터를 삽입하는 중 오류가 발생했습니다."}

        # Step 5: purchase 테이블에서 데이터 삭제
        delete_response = supabase.table("purchase").delete().eq("purchase_id", purchase_id).execute()

        if not delete_response.data:
            return {"success": False, "error": "purchase 테이블에서 데이터를 삭제하는 중 오류가 발생했습니다."}

        return {"success": True, "message": "데이터가 item 테이블로 성공적으로 이동되었습니다."}

    except Exception as e:
        return {"success": False, "error": f"오류 발생: {str(e)}"}

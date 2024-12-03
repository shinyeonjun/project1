from fastapi import APIRouter, HTTPException
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

@router.get("/getApprovedPurchases")
async def get_approved_purchases():
    try:
        response = supabase.table("purchase").select("*").eq("status", 0).execute()
        purchases = response.data

        if not purchases:
            return {"success": False, "error": "승인된 구매 내역이 없습니다."}

        return {"success": True, "purchases": purchases}

    except Exception as e:
        return {"success": False, "error": f"오류 발생: {str(e)}"}

@router.get("/getPendingPurchases")
async def get_pending_purchases():
    try:
        # 배송지와 전화번호를 포함하도록 select 문 수정
        response = supabase.table("purchase_request").select(
            "purchase_id, supply, name, quantity, total_price, deliveryaddress, phone_number"
        ).eq("status", 0).execute()
        purchases = response.data

        if not purchases:
            return {"success": False, "error": "승인 대기 요청이 없습니다."}

        return {"success": True, "purchases": purchases}

    except Exception as e:
        return {"success": False, "error": f"오류 발생: {str(e)}"}

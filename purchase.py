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

        # Step 3: purchase_id 및 status를 제외한 데이터 준비
        item_data = {
            key: value for key, value in purchase_record.items() if key not in ["purchase_id", "status"]
        }

        # Step 4: item 테이블에 데이터 삽입
        insert_response = supabase.table("item").insert(item_data).execute()

        # 삽입 성공 여부 확인
        if not insert_response.data:  # 데이터 삽입이 실패한 경우
            return {"success": False, "error": "item 테이블로 데이터를 삽입하는 중 오류가 발생했습니다."}

        # Step 5: purchase 테이블에서 데이터 삭제
        delete_response = supabase.table("purchase").delete().eq("purchase_id", purchase_id).execute()

        # 삭제 성공 여부 확인
        if not delete_response.data:  # 데이터 삭제가 실패한 경우
            return {"success": False, "error": "purchase 테이블에서 데이터를 삭제하는 중 오류가 발생했습니다."}

        return {"success": True, "message": "데이터가 item 테이블로 성공적으로 이동되었습니다."}

    except Exception as e:
        return {"success": False, "error": f"오류 발생: {str(e)}"}

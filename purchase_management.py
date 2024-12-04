from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI 라우터 설정
router = APIRouter()

# 데이터 모델
class ActionRequest(BaseModel):
    purchase_id: int

@router.get("/getRequests")
async def get_purchase_requests():
    """status가 0인 구매 요청 데이터 조회"""
    try:
        # purchase 테이블에서 status가 0인 데이터만 조회
        response = supabase.table("purchase").select("*").eq("status", 0).execute()
        if not response.data:
            return {"success": True, "requests": []}
        return {"success": True, "requests": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")

@router.post("/approve")
async def approve_purchase(request: ActionRequest):
    """구매 요청 승인"""
    try:
        purchase_id = request.purchase_id

        # purchase 테이블에서 해당 데이터 확인
        response = supabase.table("purchase").select("*").eq("purchase_id", purchase_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="요청 데이터를 찾을 수 없습니다.")

        # 해당 요청의 status를 1로 업데이트
        update_response = supabase.table("purchase").update({"status": 1}).eq("purchase_id", purchase_id).execute()
        if not update_response.data:
            raise HTTPException(status_code=500, detail="구매 요청 상태 업데이트 중 문제가 발생했습니다.")

        return {"success": True, "message": "구매 요청이 성공적으로 승인되었습니다."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")

@router.post("/reject")
async def reject_purchase(request: ActionRequest):
    """구매 요청 반려"""
    try:
        purchase_id = request.purchase_id

        # purchase 테이블에서 해당 데이터 삭제
        delete_response = supabase.table("purchase").delete().eq("purchase_id", purchase_id).eq("status", 0).execute()
        if not delete_response.data:
            raise HTTPException(status_code=500, detail="구매 요청 반려 중 문제가 발생했습니다.")

        return {"success": True, "message": "구매 요청이 반려되었습니다."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")

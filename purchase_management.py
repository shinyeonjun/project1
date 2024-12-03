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
    """모든 구매 요청 데이터 조회"""
    try:
        response = supabase.table("purchase_request").select("*").execute()
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

        # 요청 데이터 가져오기
        response = supabase.table("purchase_request").select("*").eq("purchase_id", purchase_id).execute()
        print("Request Data:", response.data)  # 요청 데이터 출력
        if not response.data:
            raise HTTPException(status_code=404, detail="요청 데이터를 찾을 수 없습니다.")

        purchase_request = response.data[0]

        # purchase 테이블에 데이터 삽입
        purchase_data = {
            "supply": purchase_request["supply"],
            "total_price": purchase_request["total_price"],
            "deliveryaddress": purchase_request["deliveryaddress"],
            "phone_number": purchase_request["phone_number"],
            "purchase_date": purchase_request["purchase_date"],
            "quantity": purchase_request["quantity"],
            "name": purchase_request["name"],
            "status": 0,  # 기본값: 0
        }
        print("Insert Data:", purchase_data)  # 삽입할 데이터 출력

        insert_response = supabase.table("purchase").insert(purchase_data).execute()
        print("Insert Response:", insert_response.data)  # 삽입 결과 출력
        if not insert_response.data:
            raise HTTPException(status_code=500, detail="구매 요청 데이터 저장 중 문제가 발생했습니다.")

        # purchase_request 테이블에서 데이터 삭제
        delete_response = supabase.table("purchase_request").delete().eq("purchase_id", purchase_id).execute()
        print("Delete Response:", delete_response.data)  # 삭제 결과 출력
        if not delete_response.data:
            raise HTTPException(status_code=500, detail="구매 요청 데이터 삭제 중 문제가 발생했습니다.")

        return {"success": True, "message": "구매 요청이 성공적으로 승인되었습니다."}

    except Exception as e:
        print("Error:", str(e))  # 오류 메시지 출력
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")

@router.post("/reject")
async def reject_purchase(request: ActionRequest):
    """구매 요청 반려"""
    try:
        purchase_id = request.purchase_id

        # purchase_request 테이블에서 데이터 삭제
        delete_response = supabase.table("purchase_request").delete().eq("purchase_id", purchase_id).execute()
        if not delete_response.data:
            raise HTTPException(status_code=500, detail="구매 요청 반려 중 문제가 발생했습니다.")

        return {"success": True, "message": "구매 요청이 반려되었습니다."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")

from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
from typing import List
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

# 데이터 모델 정의
class Item(BaseModel):
    name: str
    price: float
    quantity: int

class PurchaseRequest(BaseModel):
    supply: str
    total_price: float
    deliveryaddress: str
    phone_number: str
    purchase_date: str
    items: List[Item]

@router.post("/submitRequest")
async def submit_purchase_request(request: PurchaseRequest):
    try:
        # purchase_request 테이블에 저장할 데이터
        purchase_data = {
            "supply": request.supply,
            "total_price": int(request.total_price),  # float -> int 변환
            "deliveryaddress": request.deliveryaddress,
            "phone_number": request.phone_number,
            "purchase_date": request.purchase_date,  # YYYY-MM-DD 포맷
            "quantity": sum(item.quantity for item in request.items),  # 총 수량 계산
            "name": request.items[0].name,
            "status": 0  # 기본값: 0 (대기 상태)
        }

        # Supabase 테이블에 데이터 삽입
        response = supabase.table("purchase_request").insert(purchase_data).execute()
        
        # Supabase 응답 확인
        if not response.data:
            raise HTTPException(status_code=500, detail="구매 요청 데이터를 저장하는 데 실패했습니다.")

        return {"success": True, "message": "구매 요청이 성공적으로 저장되었습니다."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")
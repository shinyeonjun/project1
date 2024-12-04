from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
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
class PurchaseRequest(BaseModel):
    supply: str
    deliveryaddress: str
    phone_number: str
    purchase_date: str
    type: str  # 부품 타입 추가
    name: str
    quantity: int
    total_price: float

@router.post("/submitRequest")
async def submit_purchase_request(request: PurchaseRequest):
    try:
        # Supabase에 저장할 데이터 준비
        purchase_data = {
            "supply": request.supply,
            "deliveryaddress": request.deliveryaddress,
            "phone_number": request.phone_number,
            "purchase_date": request.purchase_date,
            "type": request.type,  # 부품 타입
            "name": request.name,
            "quantity": request.quantity,
            "total_price": int(request.total_price),
            "status": 0,  # 기본값으로 승인 대기 상태
        }

        # Supabase의 purchase 테이블에 데이터 삽입
        response = supabase.table("purchase").insert(purchase_data).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="항목 저장 실패")

        return {"success": True, "message": "항목 저장 성공"}

    except Exception as e:
        print(f"오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")

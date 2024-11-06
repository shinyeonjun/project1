from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 라우터 설정
router = APIRouter()

# JSON 파일 경로 설정
PURCHASE_REQUESTS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'purchase_requests.json')

# 데이터 모델 정의
class Item(BaseModel):
    name: str
    price: int
    quantity: int

class Purchase(BaseModel):
    supply: str
    total_price: int
    status: int
    deliveryaddress: str
    phone_number: int
    purchase_date: str
    items: List[Item]

@router.post("/purchase")
async def create_purchase(purchase: Purchase):
    # 구매 요청 데이터를 JSON 형식으로 준비
    purchase_data = {
        "supply": purchase.supply,
        "total_price": purchase.total_price,
        "status": purchase.status,
        "deliveryaddress": purchase.deliveryaddress,
        "phone_number": purchase.phone_number,
        "purchase_date": purchase.purchase_date,
        "items": [item.dict() for item in purchase.items],
        "request_date": datetime.now().isoformat()  # 요청 일시 추가
    }

    # JSON 파일 경로에 디렉터리가 없으면 생성
    os.makedirs(os.path.dirname(PURCHASE_REQUESTS_FILE), exist_ok=True)

    # 기존 데이터를 읽어와서 새로운 요청 추가
    if os.path.exists(PURCHASE_REQUESTS_FILE):
        with open(PURCHASE_REQUESTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = []

    # 새로운 구매 요청 추가
    data.append(purchase_data)

    # JSON 파일에 저장
    with open(PURCHASE_REQUESTS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    return {"success": True, "message": "구매 요청이 성공적으로 저장되었습니다."}

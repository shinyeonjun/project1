from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# .env 파일 로드
load_dotenv()

# Supabase 환경 변수 설정
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI 앱 생성
app = FastAPI()

# 데이터 모델 정의
class Item(BaseModel):
    name: str
    price: int
    quantity: int
    company: str
    notes: str

class PurchaseData(BaseModel):
    companyName: str
    transactionAmount: int
    status: str
    deliveryAddress: str
    phoneNumber: str
    orderDate: str
    items: List[Item]

@app.post("/api/purchase")
async def create_purchase(purchase_data: PurchaseData):
    # purchase 테이블에 데이터 삽입
    purchase_response = supabase.table("purchase").insert({
        "company_name": purchase_data.companyName,
        "transaction_amount": purchase_data.transactionAmount,
        "status": purchase_data.status,
        "delivery_address": purchase_data.deliveryAddress,
        "phone_number": purchase_data.phoneNumber,
        "order_date": purchase_data.orderDate
    }).execute()

    if purchase_response.error:
        raise HTTPException(status_code=500, detail="Purchase 데이터 저장 실패")

    purchase_id = purchase_response.data[0]['purchase_id']  # 삽입된 purchase ID 가져오기

    # items 테이블에 각 품목 삽입
    for item in purchase_data.items:
        item_response = supabase.table("items").insert({
            "purchase_id": purchase_id,
            "name": item.name,
            "price": item.price,
            "quantity": item.quantity,
            "company": item.company,
            "notes": item.notes
        }).execute()

        if item_response.error:
            raise HTTPException(status_code=500, detail="Item 데이터 저장 실패")

    return {"message": "데이터가 성공적으로 저장되었습니다!"}

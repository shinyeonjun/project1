import json
import os
from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# 환경 변수 파일 로드
load_dotenv()

# Supabase 클라이언트 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI 라우터 설정
router = APIRouter()

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

# JSON 파일 경로 설정
JSON_PATH = os.path.join(os.path.dirname(__file__), "data", "purchase_requests.json")

@router.post("/approve_item")
async def approve_item(purchase_index: int, item_index: int):
    try:
        print(f"Received purchase_index: {purchase_index}, item_index: {item_index}")  # 디버깅 출력
        
        # JSON 파일 존재 여부 확인
        if not os.path.exists(JSON_PATH):
            raise HTTPException(status_code=404, detail="구매 요청 파일을 찾을 수 없습니다")

        # JSON 파일에서 구매 요청 데이터 로드
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            purchases = json.load(file)

        # 인덱스 유효성 검사
        if purchase_index >= len(purchases) or item_index >= len(purchases[purchase_index]["items"]):
            raise HTTPException(status_code=400, detail="잘못된 인덱스")

        # 승인할 항목 가져오기
        item_to_approve = purchases[purchase_index]["items"].pop(item_index)

        # Supabase DB에 구매 정보 저장
        purchase_data = {
            "total_price": purchases[purchase_index]["total_price"],
            "purchase_date": purchases[purchase_index]["purchase_date"],
            "supply": purchases[purchase_index]["supply"],
            "deliveryaddress": purchases[purchase_index]["deliveryaddress"],
            "status": purchases[purchase_index]["status"],
            "phone_number": purchases[purchase_index]["phone_number"],
        }

        # purchase 테이블에 구매 정보 추가
        purchase_response = supabase.table("purchase").insert(purchase_data).execute()
        
        if not purchase_response.data:
            raise HTTPException(status_code=500, detail="구매 정보를 데이터베이스에 저장하는 데 실패했습니다")

        purchase_id = purchase_response.data[0]["purchase_id"]

        # 승인된 항목을 items 테이블에 저장
        existing_item_response = supabase.table("items").select("item_id").eq("name", item_to_approve["name"]).execute()
        
        if existing_item_response.data:
            # 이미 존재하는 부품의 경우
            item_id = existing_item_response.data[0]["item_id"]
            # 수량 업데이트
            update_response = supabase.table("items").update({
                "quantity": existing_item_response.data[0]["quantity"] + item_to_approve["quantity"]
            }).eq("item_id", item_id).execute()

            if not update_response.data:
                raise HTTPException(status_code=500, detail="항목 수량 업데이트에 실패했습니다")
        else:
            # 새 부품의 경우
            new_item_response = supabase.table("items").insert({
                "name": item_to_approve["name"],
                "price": item_to_approve["price"],
                "quantity": item_to_approve["quantity"],
                "purchase_id": purchase_id  # 연결된 purchase_id
            }).execute()

            if not new_item_response.data:
                raise HTTPException(status_code=500, detail="새 항목을 데이터베이스에 저장하는 데 실패했습니다")

        # JSON 파일 업데이트
        if not purchases[purchase_index]["items"]:  # 모든 항목이 승인된 경우
            purchases.pop(purchase_index)

        # JSON 파일을 업데이트하여 남은 요청을 기록
        with open(JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(purchases, file, ensure_ascii=False, indent=4)

        return {"success": True, "message": "항목이 승인되고 DB에 저장되었습니다"}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="구매 요청 파일을 찾을 수 없습니다")
    except IndexError:
        raise HTTPException(status_code=400, detail="잘못된 구매 또는 항목 인덱스")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류: {str(e)}")

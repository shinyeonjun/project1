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

@router.get("/getItems")
async def get_items():
    """
    item 테이블의 모든 데이터를 가져와 반환합니다.
    """
    try:
        # Supabase에서 item 테이블의 데이터를 가져오기
        response = supabase.table("item").select("*").execute()
        items = response.data

        if not items:
            return {"success": False, "error": "현재 재고 데이터가 없습니다."}

        # 성공적으로 데이터를 가져왔을 경우 반환
        return {"success": True, "items": items}

    except Exception as e:
        # 예외 처리
        return {"success": False, "error": f"오류 발생: {str(e)}"}

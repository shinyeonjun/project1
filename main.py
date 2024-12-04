from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# .env 파일 로드
load_dotenv()

# Supabase 환경 변수
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI 앱 초기화
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 특정 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 경로 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 메인 페이지 경로
@app.get("/")
async def get_main():
    return FileResponse("static/main.html")

# purchase 라우터 추가
from purchase import router as purchase_router
app.include_router(purchase_router, prefix="/api/purchase")

# purchase_request 라우터 추가
from purchase_request import router as purchase_request_router
app.include_router(purchase_request_router, prefix="/api/request")

# purchase_management 라우터 추가
from purchase_management import router as purchase_management_router
app.include_router(purchase_management_router, prefix="/api/purchase_management")

# inventory 라우터 추가
from inventory import router as inventory_router
app.include_router(inventory_router, prefix="/api/inventory")

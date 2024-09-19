from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# .env 파일 로드
load_dotenv()

# 환경 변수 설정
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정 (필요한 경우)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 특정 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 경로 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_main():
    # main.html 파일 경로로 응답
    return FileResponse("static/main.html")

@app.get("/api/dashboard")
async def get_dashboard_data():
    # 데이터베이스나 다른 소스에서 데이터를 가져오는 로직
    data = {
        "production_rate": 85,  # 예시 데이터
        "sales_count": 320,
        "inventory_count": 150
    }
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

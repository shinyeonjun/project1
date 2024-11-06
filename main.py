from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 특정 도메인으로 제한하는 것이 좋습니다.
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
app.include_router(purchase_router, prefix="/api")

# purchase_request 라우터 추가
from purchase_request import router as purchase_request_router
app.include_router(purchase_request_router, prefix="/api")

# JSON 파일 제공하는 엔드포인트 추가
@app.get("/data/purchase_requests.json")
async def get_purchase_requests():
    json_path = "data/purchase_requests.json"
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(json_path)

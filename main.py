from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List
from datetime import datetime, timedelta
import os
import calendar 

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

# order_request 라우터 추가
from order_request import router as order_request_router
app.include_router(order_request_router, prefix="/api/order_request")

# order_management 라우터 추가
from order_management import router as order_management_router
app.include_router(order_management_router, prefix="/api/order_management")

# order 라우터 추가
from order import router as order_router
app.include_router(order_router, prefix="/api/order")

# 대시보드 API 라우터 생성
dashboard_router = APIRouter()

# 구매 현황 차트 데이터 엔드포인트
@dashboard_router.get("/purchase_chart")
async def get_purchase_chart():
    try:
        # 오늘 날짜부터 과거 7일까지의 날짜 생성
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        purchase_data = []
        for date in dates:
            # purchase_date 컬럼을 사용하여 날짜별로 필터링
            response = supabase.table('purchase').select('*').eq('status', 1).gte('purchase_date', date + ' 00:00:00').lte('purchase_date', date + ' 23:59:59').execute()
            count = len(response.data)
            purchase_data.append({'date': date, 'count': count})
        return purchase_data
    except Exception as e:
        print(f"Error fetching purchase chart data: {e}")
        return []

# 재고 현황 차트 데이터 엔드포인트
@dashboard_router.get("/inventory_chart")
async def get_inventory_chart():
    try:
        # item 테이블에서 타입별 재고 수량 조회
        response = supabase.table('item').select('type', 'quantity').execute()
        data = response.data
        type_counts = {}
        for item in data:
            item_type = item['type']
            quantity = item['quantity']
            if item_type in type_counts:
                type_counts[item_type] += quantity
            else:
                type_counts[item_type] = quantity
        inventory_data = [{'type': k, 'count': v} for k, v in type_counts.items()]
        return inventory_data
    except Exception as e:
        print(f"Error fetching inventory chart data: {e}")
        return []

# 대시보드 요약 데이터 엔드포인트
@dashboard_router.get("/dashboard")
async def get_dashboard_summary():
    try:
        # 구매 완료율 계산
        purchase_total_response = supabase.table('purchase').select('*').execute()
        purchase_completed_response = supabase.table('purchase').select('*').eq('status', 2).execute()  # status가 2인 경우 완료로 가정
        total_purchases = len(purchase_total_response.data)
        completed_purchases = len(purchase_completed_response.data)
        production_rate = (completed_purchases / total_purchases) * 100 if total_purchases > 0 else 0

        # 판매 수량 계산 (orders 테이블 사용)
        sales_response = supabase.table('orders').select('*').execute()
        sales_count = len(sales_response.data)

        # 전체 재고 수량 계산
        inventory_response = supabase.table('item').select('quantity').execute()
        inventory_count = sum(item['quantity'] for item in inventory_response.data)

        return {
            'production_rate': round(production_rate, 2),
            'sales_count': sales_count,
            'inventory_count': inventory_count
        }
    except Exception as e:
        print(f"Error fetching dashboard summary data: {e}")
        return {
            'production_rate': 0,
            'sales_count': 0,
            'inventory_count': 0
        }
    

@dashboard_router.get("/sales_chart")
async def get_sales_chart():
    try:
        today = datetime.now()

        # 1. 일간 매출 (지난 7일)
        daily_sales = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            response = supabase.table("sales").select("total_price").gte("sale_date", date_str).lte("sale_date", date_str).execute()
            total_sales = sum(item["total_price"] for item in response.data)
            daily_sales.append({"date": date_str, "total_sales": total_sales})

        # 2. 월간 매출 (최근 한 달)
        start_of_month = today.replace(day=1)
        end_of_month = today
        monthly_sales = []
        for day in range((end_of_month - start_of_month).days + 1):
            date = start_of_month + timedelta(days=day)
            date_str = date.strftime('%Y-%m-%d')
            response = supabase.table("sales").select("total_price").gte("sale_date", date_str).lte("sale_date", date_str).execute()
            total_sales = sum(item["total_price"] for item in response.data)
            monthly_sales.append({"date": date_str, "total_sales": total_sales})

        # 3. 연간 매출 (최근 1년)
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today
        monthly_sales_data = []
        for month in range(1, today.month + 1):
            first_day = datetime(today.year, month, 1)
            last_day = datetime(today.year, month, calendar.monthrange(today.year, month)[1])
            response = supabase.table("sales").select("total_price").gte("sale_date", first_day.isoformat()).lte("sale_date", last_day.isoformat()).execute()
            total_sales = sum(item["total_price"] for item in response.data)
            monthly_sales_data.append({"month": f"{month}월", "total_sales": total_sales})

        return {
            "daily_sales": daily_sales,
            "monthly_sales": monthly_sales,
            "yearly_sales": monthly_sales_data
        }
    except Exception as e:
        print(f"Error fetching sales chart data: {e}")
        return {
            "daily_sales": [],
            "monthly_sales": [],
            "yearly_sales": []
        }

# 대시보드 라우터 등록
app.include_router(dashboard_router, prefix="/api")

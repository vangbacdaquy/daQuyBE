# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import health
import ai_service

# Khởi tạo App
app = FastAPI()

# 1. CẤU HÌNH CORS (Tự động)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép mọi domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ĐỊNH NGHĨA ROUTER

# Healthcheck (Sync vẫn chạy tốt trong FastAPI)
@app.get("/health")
def health_check(request: Request):
    # Gọi hàm bên file health.py
    # Lưu ý: health.py cần sửa nhẹ để không phụ thuộc request object của flask
    return health.handle_health_check(request)

# AI Process (ASYNC TOÀN TẬP)
@app.post("/process-ai")
async def process_ai(request: Request):
    # Gọi hàm async bên ai_service.py
    return await ai_service.handle_ai_request(request)
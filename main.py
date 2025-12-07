import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import health
import ai_service

# --- FIREBASE ADMIN ---
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.getenv("PROJECT_ID"),
    })

app = FastAPI()

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Hàm này chặn mọi request không có Token hợp lệ.
    """
    token = credentials.credentials
    try:
        # Firebase Admin SDK sẽ check chữ ký và hạn sử dụng của token
        decoded_token = auth.verify_id_token(token)
        return decoded_token 
        
    except Exception as e:
        # Nếu token sai, hết hạn, hoặc giả mạo -> Trả về lỗi 401
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- 3. ROUTER ---

@app.get("/health")
def health_check(request: Request):
    return health.handle_health_check(request)

@app.post("/process-ai")
async def process_ai(
    request: Request, 
    user_info: dict = Depends(verify_token) 
):
    print(f"User {user_info.get('email')} đang gọi API")
    
    return await ai_service.handle_ai_request(request)
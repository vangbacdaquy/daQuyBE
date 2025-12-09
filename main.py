import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import health
import ai_service
import report_service

# --- Init Services ---
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {'projectId': os.getenv("PROJECT_ID")})

limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Authorization Logic ---
ALLOWED_EMAILS = [
    "dhtruong0407@gmail.com",
    "suplike1191@gmail.com",
    "snmquangams@gmail.com"
]

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        email = decoded_token.get("email")

        if email not in ALLOWED_EMAILS:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Email {email} is not authorized."
            )
        return decoded_token
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- Routes ---
@app.get("/health")
def health_check(request: Request):
    return health.handle_health_check(request)

@app.post("/process-ai")
@limiter.limit("20/minute")
async def process_ai(request: Request, user_info: dict = Depends(verify_token)):
    return await ai_service.handle_ai_request(request)

@app.post("/save-report")
async def save_report(reports: list[report_service.ReportRequest], user_info: dict = Depends(verify_token)):
    return await report_service.handle_save_bulk_reports(reports, user_info.get("email"))

@app.get("/reports")
async def get_reports(
    user_email: str, 
    start_date: str, 
    end_date: str, 
    user_info: dict = Depends(verify_token)
):
    """
    Lấy danh sách báo cáo theo user_email và khoảng thời gian (start_date, end_date).
    Format date: YYYY-MM-DD
    """
    return await report_service.handle_load_reports(user_email, start_date, end_date)

import os
from google.cloud import firestore
from pydantic import BaseModel
from datetime import datetime
import pytz
from fastapi import HTTPException

# --- Init DB ---
try:
    db = firestore.Client(
        project=os.getenv("PROJECT_ID"),
        database=os.getenv("DATABASE_NAME")
    )
except Exception as e:
    print(f"Warning: DB Connection failed: {e}")
    db = None

# --- Data Models ---
class ReportRequest(BaseModel):
    image_url: str
    ai_description: str | None = ""
    ai_count: int
    manual_count: int
    notes: str | None = ""

# --- Main Logic ---

async def handle_save_report(report: ReportRequest, user_email: str):
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        vn_now = datetime.now(vn_tz)
        variance = report.manual_count - report.ai_count
        doc_data = {
            "user_email": user_email,
            "image_url": report.image_url,
            "ai_description": report.ai_description,
            "ai_count": report.ai_count,
            "manual_count": report.manual_count,
            "variance": variance,
            "notes": report.notes,
            "created_at": firestore.SERVER_TIMESTAMP,
            "date_str": vn_now.strftime("%Y-%m-%d"),
            "month_str": vn_now.strftime("%Y-%m"),
            "timestamp_iso": vn_now.isoformat()
        }
        _, doc_ref = db.collection("reports").add(doc_data)
        return {
            "status": "success", 
            "id": doc_ref.id,
            "message": "Report saved successfully"
        }
    except Exception as e:
        print(f"Save Error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def handle_save_bulk_reports(reports: list[ReportRequest], user_email: str):
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")
    batch = db.batch()
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    vn_now = datetime.now(vn_tz)
    doc_refs = []
    for report in reports:
        variance = report.manual_count - report.ai_count
        doc_ref = db.collection("reports").document()
        doc_data = {
            "user_email": user_email,
            "image_url": report.image_url,
            "ai_count": report.ai_count,
            "manual_count": report.manual_count,
            "variance": variance,
            "notes": report.notes,
            "created_at": firestore.SERVER_TIMESTAMP,
            "date_str": vn_now.strftime("%Y-%m-%d"),
            "month_str": vn_now.strftime("%Y-%m"),
            "timestamp_iso": vn_now.isoformat()
        }
        batch.set(doc_ref, doc_data)
        doc_refs.append(doc_ref)
    try:
        batch.commit()
        results = [{
            "status": "success",
            "id": doc_ref.id,
            "message": "Report saved successfully"
        } for doc_ref in doc_refs]
        return {"results": results}
    except Exception as e:
        print(f"Batch Save Error: {e}")
        return {"results": [{
            "status": "error",
            "message": f"Database error: {str(e)}"
        }]}

async def handle_load_reports(user_email: str, start_date: str, end_date: str):
    """
    Hàm load reports từ Firestore dựa trên user_email và khoảng thời gian.
    Query fields: user_email, date_str (YYYY-MM-DD)
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        # Tạo query cơ bản: filter theo user_email
        reports_ref = db.collection("reports")
        if(user_email != "" and user_email is not None):
            query = reports_ref.where(filter=firestore.FieldFilter("user_email", "==", user_email))

        # Filter theo date range (dựa trên field date_str)
        if start_date:
            query = query.where(filter=firestore.FieldFilter("date_str", ">=", start_date))
        if end_date:
            query = query.where(filter=firestore.FieldFilter("date_str", "<=", end_date))

        # Thực hiện query (stream() trả về generator các document snapshot)
        # Lưu ý: stream() là hàm sync, trong môi trường async thực tế nên chạy trong threadpool hoặc dùng AsyncClient
        docs = query.stream()

        reports = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            # Xử lý datetime object nếu có (để return JSON không lỗi)
            if "created_at" in data and data["created_at"]:
                # Firestore Timestamp -> string
                data["created_at"] = data["created_at"].isoformat() if hasattr(data["created_at"], "isoformat") else str(data["created_at"])
            
            reports.append(data)

        return {"reports": reports}

    except Exception as e:
        print(f"Load Reports Error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
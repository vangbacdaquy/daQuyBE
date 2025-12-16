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
            "ai_description": report.ai_description,
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

async def handle_load_reports(user_email: str, start_date: str, end_date: str, last_created_at: str, last_image_url: str):
    """
    Hàm load reports từ Firestore dựa trên user_email và khoảng thời gian.
    Query fields: user_email, date_str (YYYY-MM-DD)
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        # Tạo query cơ bản: filter theo user_email
        query = db.collection("reports")
        if user_email:
            query = query.where(filter=firestore.FieldFilter("user_email", "==", user_email))

        # Filter theo date range (dựa trên field date_str)
        is_range_query = False
        if start_date == end_date:
            query = query.where(filter=firestore.FieldFilter("date_str", "==", start_date))
        else:
            query = query.where(filter=firestore.FieldFilter("date_str", ">=", start_date))
            query = query.where(filter=firestore.FieldFilter("date_str", "<=", end_date))
            is_range_query = True

        # Sorting
        # Nếu có range filter trên date_str, bắt buộc phải sort theo date_str đầu tiên
        if is_range_query:
            query = query.order_by('date_str', direction=firestore.Query.DESCENDING)
        
        query = query.order_by('created_at',direction=firestore.Query.DESCENDING).order_by('image_url')

        if (last_created_at and last_image_url):
            # Convert ISO string to datetime for cursor
            try:
                # Handle 'Z' for UTC if present (Python < 3.11 compat)
                iso_str = last_created_at.replace('Z', '+00:00')
                last_created_dt = datetime.fromisoformat(iso_str)
            except Exception:
                last_created_dt = last_created_at

            cursor_values = []
            if is_range_query:
                # Derive date_str from created_at
                if isinstance(last_created_dt, datetime):
                    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                    if last_created_dt.tzinfo is None:
                        last_created_dt = last_created_dt.replace(tzinfo=pytz.utc)
                    last_date_str = last_created_dt.astimezone(vn_tz).strftime("%Y-%m-%d")
                    cursor_values.append(last_date_str)
                else:
                    cursor_values.append(start_date or end_date)

            cursor_values.append(last_created_dt)
            cursor_values.append(last_image_url)
            
            query = query.start_after(*cursor_values)

        docs = query.limit(20).stream()

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
    
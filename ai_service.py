from google.genai import Client, types
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prompt import SYSTEM_INSTRUCTION
import os
import asyncio
import time
import json

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
MODEL_ID = "gemini-3-pro-preview"

class InventoryItem(BaseModel):
    layout_type: str = Field(..., description="Dạng Lưới / Dạng Treo / Dạng Trải Ngang")
    item_type: str = Field(..., description="Nhẫn / Bông tai / Dây chuyền / Lắc tay")
    counting_logic: str = Field(..., description="Mô tả ngắn gọn quá trình soi và đếm")
    count: int = Field(..., description="Số lượng món đồ đếm được")

async def process_single_file(aclient, uri: str, prompt: str):
    """Xử lý từng file để đảm bảo map đúng imageID"""
    image_id = uri.split('/')[-1] # Lấy tên file làm ID
    try:
        mime_type = "video/mp4" if uri.endswith(".mp4") else "image/jpeg"
        
        # Gọi model với schema
        response = await aclient.models.generate_content(
            model=MODEL_ID,
            contents=[
                types.Part.from_uri(file_uri=uri, mime_type=mime_type),
                types.Part.from_text(text=prompt)
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0,
                top_k=None,
                top_p=None,
                response_mime_type="application/json",
                response_schema=InventoryItem,
                thinking_config=types.ThinkingConfig(thinking_level="low")
            ),
        )
        
        # Parse kết quả
        data = json.loads(response.text)
        return {
            "imageID": image_id,
            "layout_type": data.get("layout_type", ""),
            "item_type": data.get("item_type", ""),
            "count": data.get("count", 0),
            "counting_logic": data.get("counting_logic", "")
        }
    except Exception as e:
        print(f"Err {image_id}: {e}")
        return {
            "imageID": image_id,
            "layout_type": "Error",
            "item_type": "Error",
            "count": 0,
            "counting_logic": f"Lỗi: {str(e)}"
        }

async def handle_ai_request(request):
    start_ts = time.time()
    
    # Init Client
    aclient = Client(vertexai=True, project=PROJECT_ID, location=LOCATION).aio

    try:
        # Parse Body
        try:
            req_json = await request.json()
        except:
            req_json = {}

        file_uris = req_json.get('file_uris', [])
        prompt = req_json.get('prompt', "Đếm số lượng trang sức.")

        if not file_uris:
            return JSONResponse(
                status_code=400,
                content={
                    "data": None,
                    "error": {"code": "INVALID_INPUT", "message": "Thiếu file_uris"}
                }
            )

        # Xử lý song song tất cả các ảnh
        tasks = [process_single_file(aclient, uri, prompt) for uri in file_uris]
        results = await asyncio.gather(*tasks)

        # Tính thời gian xử lý
        duration = int((time.time() - start_ts) * 1000)

        # Trả về kết quả thành công
        return JSONResponse(
            status_code=200,
            content={
                "data": {"items": results},
                "message": "Xử lý thành công.",
                "metadata": {"processingTimeMs": duration}
            }
        )

    except Exception as e:
        # Trả về lỗi hệ thống
        return JSONResponse(
            status_code=500,
            content={
                "data": None,
                "error": {"code": "PROCESSING_ERROR", "message": str(e)}
            }
        )
    
    finally:
        await aclient.aclose()
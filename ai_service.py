from google.genai import Client, types
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from prompt import SYSTEM_INSTRUCTION
import os

load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
MODEL_ID = "gemini-3-pro-preview"

async def handle_ai_request(request):
    """Hàm xử lý request từ Frontend."""
    # Khởi tạo Client
    aclient = Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION).aio

    # Lấy dữ liệu JSON
    try:
        request_json = await request.json()
    except Exception:
        request_json = None
    
    if not request_json:
        return JSONResponse(content={"error": "Invalid JSON"}, status_code=400)

    file_uris = request_json.get('file_uris', [])
    prompt_text = request_json.get('prompt')

    # Kiểm tra đầu vào: phải có ít nhất file hoặc prompt
    if not file_uris and not prompt_text:
        return JSONResponse(content={"error": "Cần cung cấp file_uris hoặc prompt"}, status_code=400)

    # Nếu không có prompt nhưng có file, dùng prompt mặc định
    if not prompt_text:
        prompt_text = "Mô tả chi tiết nội dung trong các hình ảnh/video này."

    try:
        contents = []
        
        # Xử lý file nếu có
        for uri in file_uris:
            mime_type = "video/mp4" if uri.endswith(".mp4") else "image/jpeg"
            contents.append(types.Part.from_uri(file_uri=uri, mime_type=mime_type))

        # Thêm prompt text
        contents.append(types.Part.from_text(text=prompt_text))

        # Gọi Gemini API
        response = await aclient.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0,
                top_p=None,
                top_k=None,
        ),
        )

        # Trả về kết quả
        # Lưu ý: response.usage_metadata có thể cần convert sang dict nếu nó là object
        usage_data = response.usage_metadata
        if hasattr(usage_data, "model_dump"):
            usage_data = usage_data.model_dump()
        elif hasattr(usage_data, "to_dict"):
            usage_data = usage_data.to_dict()

        return JSONResponse(content={
            "status": "success",
            "data": response.text,
            "usage": usage_data
        }, status_code=200)

    except Exception as e:
        print(f"Lỗi: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
    finally:
        await aclient.aclose()
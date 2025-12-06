from google.genai import Client, types
from dotenv import load_dotenv
import functions_framework
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
MODEL_ID = "gemini-2.5-flash"


@functions_framework.http
async def handle_ai_request(request):
    """Hàm xử lý request từ Frontend."""
    # Khởi tạo Client
    aclient = Client(api_key=GEMINI_API_KEY).aio

    # Lấy dữ liệu JSON
    request_json = await request.get_json(silent=True)
    
    if not request_json:
        return {"error": "Invalid JSON"}, 400

    file_uris = request_json.get('file_uris', [])
    prompt_text = request_json.get('prompt')

    # Kiểm tra đầu vào: phải có ít nhất file hoặc prompt
    if not file_uris and not prompt_text:
        return {"error": "Cần cung cấp file_uris hoặc prompt"}, 400

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
        )

        # Trả về kết quả
        return {
            "status": "success",
            "data": response.text,
            "usage": response.usage_metadata
        }, 200

    except Exception as e:
        print(f"Lỗi: {e}")
        return {"error": str(e)}, 500
    
    finally:
        await aclient.aclose()
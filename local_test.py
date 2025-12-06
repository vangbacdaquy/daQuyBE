import asyncio
import os
from main import entry_point

# Mock class để giả lập Request object
class MockRequest:
    def __init__(self, json_data=None, path="/"):
        self._json_data = json_data
        self.path = path

    async def get_json(self, silent=True):
        return self._json_data

async def run_test():
    print("--- Bắt đầu test local ---")
    
    # 0. Test Health Check
    print("\n0. Test Health Check (/health):")
    mock_req_health = MockRequest(path="/health")
    try:
        result, status = await entry_point(mock_req_health)
        print(f"Status: {status}")
        print(f"Response: {result}")
    except Exception as e:
        print(f"Lỗi khi test health: {e}")

    # 1. Test trường hợp chỉ có Prompt
    print("\n1. Test với Prompt text (/process-ai):")
    mock_req_text = MockRequest({
        "prompt": "Chào Gemini, hãy giới thiệu về bản thân ngắn gọn."
    }, path="/process-ai")
    
    try:
        # Gọi hàm entry_point
        result, status = await entry_point(mock_req_text)
        print(f"Status: {status}")
        print(f"Response: {result}")
    except Exception as e:
        print(f"Lỗi khi test text: {e}")


    # 2. Test trường hợp có File (Giả lập URI, cần URI thật nếu muốn Gemini đọc được)
    # Nếu không có file thật trên GCS, Gemini sẽ báo lỗi không tìm thấy file hoặc quyền truy cập.
    # Ở đây ta chỉ test logic code chạy qua được không.
    print("\n2. Test với File URI (Giả lập):")
    mock_req_file = MockRequest({
        "file_uris": ["gs://cloud-samples-data/video/animals.mp4"], # File mẫu công khai của Google
        "prompt": "Video này có con gì?"
    }, path="/process-ai")

    try:
        result, status = await entry_point(mock_req_file)
        print(f"Status: {status}")
        print(f"Response: {result}")
    except Exception as e:
        print(f"Lỗi khi test file: {e}")

if __name__ == "__main__":
    # Kiểm tra biến môi trường trước
    # main.py đã gọi load_dotenv() ở top level, nên khi import main, nó đã chạy rồi.
    if not os.getenv("GEMINI_API_KEY"):
        print("CẢNH BÁO: Chưa thấy GEMINI_API_KEY trong biến môi trường. Code có thể sẽ lỗi Authentication.")
    
    asyncio.run(run_test())

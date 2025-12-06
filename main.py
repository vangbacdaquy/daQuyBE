# main.py
import functions_framework
import health
import ai_service

@functions_framework.http
async def entry_point(request):
    path = request.path # Lấy cái đuôi phía sau domain
    
    # URL 1: .../health
    if path == "/health":
        return health.handle_health_check(request)
    
    # URL 2: .../process-ai
    elif path == "/process-ai":
        return await ai_service.handle_ai_request(request)
        
    # URL lạ -> Báo lỗi 404
    else:
        return {"error": "Đường dẫn không tồn tại"}, 404
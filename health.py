def handle_health_check(request):
    """
    Hàm kiểm tra trạng thái hoạt động của Service (Health Check).
    Chỉ cần trả về 200 OK và một thông báo đơn giản.
    """
    return {
        "status": "ok",
        "message": "App is running correctly",
        "version": "1.0.0"
    }, 200

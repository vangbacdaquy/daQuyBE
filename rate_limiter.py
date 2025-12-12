from fastapi import HTTPException, status
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        # Lưu timestamp của các request
        self.minute_requests = defaultdict(list)
        self.daily_requests = defaultdict(list)
        
        # Danh sách user không bị giới hạn
        self.unlimited_users = {
            "dhtruong0407@gmail.com", 
            "snmquangams@gmail.com"
        }
        
    def check_rate_limit(self, email: str):
        """
        Kiểm tra giới hạn rate limit cho user.
        - Max 10 requests / 1 phút
        - Max 60 requests / 24 giờ
        - User trong unlimited_users được miễn phí.
        """
        if email in self.unlimited_users:
            return
        
        now = time.time()
        
        # 1. Kiểm tra giới hạn 1 phút (60 giây)
        # Lọc bỏ các timestamp cũ hơn 60s
        self.minute_requests[email] = [t for t in self.minute_requests[email] if now - t < 60]
        
        if len(self.minute_requests[email]) >= 10:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Bạn đã hết lượt thử trong 1 phút (Max 10 req/min). Vui lòng đợi."
            )
            
        # 2. Kiểm tra giới hạn 24 giờ (86400 giây)
        # Lọc bỏ các timestamp cũ hơn 24h
        self.daily_requests[email] = [t for t in self.daily_requests[email] if now - t < 86400]
        
        if len(self.daily_requests[email]) >= 60:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Bạn đã hết lượt thử trong 24 giờ (Max 60 req/day). Vui lòng quay lại sau."
            )
        
        # Ghi nhận request mới
        self.minute_requests[email].append(now)
        self.daily_requests[email].append(now)

# Global instance
limiter_service = RateLimiter()

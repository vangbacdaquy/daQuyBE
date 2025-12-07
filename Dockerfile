# Khuyên dùng bản -slim để nhẹ hơn (nhanh hơn khi deploy)
FROM python:3.13-slim

# Cấu hình Python
ENV PYTHONUNBUFFERED=True
ENV APP_HOME=/app
WORKDIR $APP_HOME

# --- BƯỚC 1: CHỈ COPY FILE THƯ VIỆN TRƯỚC ---
# Đây là bí quyết! Docker sẽ kiểm tra xem file này có thay đổi không.
# Nếu file này không đổi, nó sẽ dùng Cache của lần build trước và BỎ QUA bước pip install.
COPY requirements.txt .

# --- BƯỚC 2: CÀI THƯ VIỆN ---
# Dùng --no-cache-dir để giảm dung lượng ảnh (vì ta đã có Docker Layer Cache rồi)
RUN pip install --no-cache-dir -r requirements.txt

# --- BƯỚC 3: COPY CODE CỦA BẠN SAU ---
# Bây giờ mới copy code. Nếu bạn sửa code, Docker chỉ chạy lại từ dòng này trở đi.
COPY . ./

# Chạy server
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
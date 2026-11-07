FROM python:3.12-slim

# Cài đặt ffmpeg và các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cài đặt dependencies trước để tận dụng Docker layer cache
COPY requirements.txt requirements-server.txt ./
RUN pip install --no-cache-dir -r requirements-server.txt

# Sao chép toàn bộ mã nguồn
COPY . .

# Lưu thời điểm build theo giờ Việt Nam (UTC+7) dạng ddmmyyhh
RUN date -u -d '+7 hours' +%d%m%y%H > BUILD_STAMP

# Biến môi trường mặc định
ENV PORT=8765 \
    WORKSPACE_DIR=/app/workspace \
    PYTHONUNBUFFERED=1 \
    MAX_PARALLEL_RENDERS=1

# Tạo sẵn workspace
RUN mkdir -p /app/workspace

EXPOSE 8765

# Chạy gunicorn với 1 worker, 8 threads (vì job queue lưu trong bộ nhớ)
CMD ["sh", "-c", "gunicorn wsgi:app --bind 0.0.0.0:${PORT:-8765} --workers 1 --threads 8 --timeout 900"]

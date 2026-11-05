#!/usr/bin/env bash
# Script khởi động 1 chạm cho TAIO Cover Studio trên macOS và Linux

set -e

echo "============================================================"
echo "          Khởi động TAIO Cover Studio...                   "
echo "============================================================"

# Kiểm tra python3
if ! command -v python3 &> /dev/null; then
    echo "Lỗi: Không tìm thấy python3. Vui lòng cài đặt Python 3.10 trở lên."
    exit 1
fi

# Chạy web server
python3 studio_web.py

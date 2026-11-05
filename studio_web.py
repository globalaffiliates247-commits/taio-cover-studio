#!/usr/bin/env python3
"""
studio_web.py - Điểm khởi chạy giao diện Web cục bộ trên máy tính (macOS, Windows, Linux).
Mặc định truy cập: http://127.0.0.1:8765
"""

import os
import sys
import webbrowser
from pathlib import Path

# Đảm bảo đường dẫn gốc dự án có trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from web.server import app

def main():
    host = os.getenv("HOST", "127.0.0.1").strip()
    port = int(os.getenv("PORT", "8765").strip())

    url = f"http://{host}:{port}"
    print("=" * 60)
    print("  TAIO Cover Studio (v1.0 MVP) — Giao diện Web")
    print(f"  Đang chạy tại: {url}")
    print("  Nhấn Ctrl+C để dừng máy chủ.")
    print("=" * 60)

    # Tự động mở trình duyệt nếu không tắt cờ BROWSER=none
    if os.getenv("NO_BROWSER", "").lower() not in ("1", "true"):
        def _open_browser():
            import time
            time.sleep(1.0)
            webbrowser.open(url)
        import threading
        threading.Thread(target=_open_browser, daemon=True).start()

    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    main()

"""
web/cleanup.py - Tự động dọn dẹp các tệp tải lên và tệp xuất đã cũ theo FILE_TTL_HOURS.
"""

import os
import time
from pathlib import Path
from core.paths import UPLOADS_DIR, OUTPUTS_DIR, PREVIEWS_DIR


def cleanup_old_files():
    """Xoá các file trong uploads, outputs, previews cũ hơn FILE_TTL_HOURS."""
    ttl_hours_str = os.getenv("FILE_TTL_HOURS", "6").strip()
    try:
        ttl_hours = float(ttl_hours_str)
    except ValueError:
        ttl_hours = 6.0

    if ttl_hours <= 0:
        return  # Đã tắt tự động xoá

    ttl_seconds = ttl_hours * 3600.0
    now = time.time()

    target_dirs = [UPLOADS_DIR, OUTPUTS_DIR, PREVIEWS_DIR]

    for d in target_dirs:
        if not d.exists():
            continue
        for item in d.iterdir():
            if item.is_file() and not item.name.startswith("."):
                try:
                    file_mtime = item.stat().st_mtime
                    if now - file_mtime > ttl_seconds:
                        item.unlink()
                except Exception:
                    pass

"""
core/version.py - Quản lý thông tin phiên bản và dấu thời gian build cho TAIO.CLUB.
Định dạng nhãn: v<phiên_bản> · <ddmmyyhh> (theo giờ Việt Nam UTC+7).
"""

from datetime import datetime, timezone, timedelta
import os
from pathlib import Path
import subprocess
from typing import Dict, Optional
from core.paths import BASE_DIR

_CACHED_VERSION_INFO: Optional[Dict[str, str]] = None

VN_TZ = timezone(timedelta(hours=7))


def get_version_info() -> Dict[str, str]:
    """
    Trả về thông tin phiên bản dạng:
    {"version": "1.3.0", "build": "07112621", "label": "v1.3.0 · 07112621"}
    Tính toán một lần lúc khởi động và lưu bộ nhớ đệm.
    """
    global _CACHED_VERSION_INFO
    if _CACHED_VERSION_INFO is not None:
        return _CACHED_VERSION_INFO

    # 1. Đọc số phiên bản từ file VERSION (nguồn duy nhất)
    version_file = BASE_DIR / "VERSION"
    version_str = "1.3.0"
    if version_file.exists():
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                v = f.read().strip()
                if v:
                    version_str = v
        except Exception:
            pass

    # 2. Xác định build stamp ddmmyyhh theo UTC+7
    build_stamp = ""

    # a. File BUILD_STAMP (sinh lúc docker build trên Render/VPS)
    build_file = BASE_DIR / "BUILD_STAMP"
    if build_file.exists():
        try:
            with open(build_file, "r", encoding="utf-8") as f:
                b = f.read().strip()
                if b:
                    build_stamp = b
        except Exception:
            pass

    # b. Nếu không có BUILD_STAMP, lấy thời gian commit git cuối cùng
    if not build_stamp:
        try:
            res = subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0 and res.stdout.strip():
                ts = int(res.stdout.strip())
                dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(VN_TZ)
                build_stamp = dt.strftime("%d%m%y%H")
        except Exception:
            pass

    # c. Nếu không có git, dùng mtime của file VERSION
    if not build_stamp:
        try:
            if version_file.exists():
                mtime = os.path.getmtime(version_file)
                dt = datetime.fromtimestamp(mtime, tz=timezone.utc).astimezone(VN_TZ)
                build_stamp = dt.strftime("%d%m%y%H")
            else:
                dt = datetime.now(VN_TZ)
                build_stamp = dt.strftime("%d%m%y%H")
        except Exception:
            dt = datetime.now(VN_TZ)
            build_stamp = dt.strftime("%d%m%y%H")

    label = f"v{version_str} · {build_stamp}"
    _CACHED_VERSION_INFO = {
        "version": version_str,
        "build": build_stamp,
        "label": label,
    }
    return _CACHED_VERSION_INFO

"""
core/paths.py - Quản lý đường dẫn trong toàn bộ ứng dụng TAIO Cover Studio.
"""

import os
import shutil
from pathlib import Path

# Thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# Các thư mục thành phần
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
TEMPLATES_DIR = BASE_DIR / "templates"
BRAND_DIR = BASE_DIR / "brand"
CONFIG_DIR = BASE_DIR / "config"

# Thư mục workspace (lấy từ biến môi trường hoặc mặc định ./workspace)
_env_workspace = os.getenv("WORKSPACE_DIR", "").strip()
if _env_workspace:
    WORKSPACE_DIR = Path(_env_workspace).resolve()
else:
    WORKSPACE_DIR = (BASE_DIR / "workspace").resolve()

# Đảm bảo workspace tồn tại
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR = WORKSPACE_DIR / "uploads"
OUTPUTS_DIR = WORKSPACE_DIR / "outputs"
PREVIEWS_DIR = WORKSPACE_DIR / "previews"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

# Tìm nhị phân ffmpeg và ffprobe
CANDIDATE_BIN_DIRS = [
    Path.home() / "bin",
    Path("/opt/homebrew/bin"),
    Path("/usr/local/bin"),
    Path("/usr/bin"),
]


def get_ffmpeg_path() -> str:
    """Trả về đường dẫn tới ffmpeg nhị phân khả dụng."""
    env_bin = os.getenv("FFMPEG_BINARY")
    if env_bin and os.path.exists(env_bin):
        return env_bin

    which_bin = shutil.which("ffmpeg")
    if which_bin:
        return which_bin

    for bin_dir in CANDIDATE_BIN_DIRS:
        cand = bin_dir / "ffmpeg"
        if cand.exists() and os.access(cand, os.X_OK):
            return str(cand)

    return "ffmpeg"


def get_ffprobe_path() -> str:
    """Trả về đường dẫn tới ffprobe nhị phân khả dụng."""
    env_bin = os.getenv("FFPROBE_BINARY")
    if env_bin and os.path.exists(env_bin):
        return env_bin

    which_bin = shutil.which("ffprobe")
    if which_bin:
        return which_bin

    for bin_dir in CANDIDATE_BIN_DIRS:
        cand = bin_dir / "ffprobe"
        if cand.exists() and os.access(cand, os.X_OK):
            return str(cand)

    return "ffprobe"

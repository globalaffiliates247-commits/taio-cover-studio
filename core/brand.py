"""
core/brand.py - Quản lý Brand Kit và giải quyết biến thay thế ($name, $primary,...)
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from core.paths import BRAND_DIR


def load_brand_kit(brand_file: Optional[Path] = None) -> Dict[str, Any]:
    """Tải cấu hình thương hiệu từ brand.json."""
    if brand_file is None:
        brand_file = BRAND_DIR / "brand.json"

    if not brand_file.exists():
        return {
            "name": "TAIO",
            "handle": "taio.club",
            "tagline": "",
            "logo": "logo.png",
            "colors": {
                "primary": "#1A56DB",
                "primary_dark": "#0E2B6C",
                "accent": "#FFD34D",
                "text": "#FFFFFF",
                "pill": "#FFFFFF26",
                "pill_stroke": "#FFFFFF55",
            },
            "voice": "Chuyên nghiệp, súc tích, mang tính hành động.",
        }

    try:
        with open(brand_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Cảnh báo: Không thể đọc {brand_file}: {e}")
        return {}


def get_brand_replacements(brand_data: Dict[str, Any]) -> Dict[str, str]:
    """Tạo bảng tra cứu biến thay thế $... từ dữ liệu brand."""
    replacements: Dict[str, str] = {}

    # Thuộc tính cơ bản
    replacements["$name"] = str(brand_data.get("name", "TAIO"))
    replacements["$handle"] = str(brand_data.get("handle", "taio.club"))
    replacements["$tagline"] = str(brand_data.get("tagline", ""))

    # Bảng màu
    colors = brand_data.get("colors", {})
    for key, val in colors.items():
        replacements[f"${key}"] = str(val)

    return replacements


def resolve_variables(obj: Any, brand_data: Dict[str, Any]) -> Any:
    """Đệ quy thay thế các biến $... trong chuỗi, dict, list."""
    replacements = get_brand_replacements(brand_data)

    def _replace_str(s: str) -> str:
        # Nếu chuỗi khớp chính xác một biến, trả về giá trị biến đó
        if s in replacements:
            return replacements[s]
        # Nếu chuỗi chứa biến (ví dụ: "@$handle")
        res = s
        for k, v in replacements.items():
            if k in res:
                res = res.replace(k, v)
        return res

    if isinstance(obj, str):
        return _replace_str(obj)
    elif isinstance(obj, list):
        return [resolve_variables(item, brand_data) for item in obj]
    elif isinstance(obj, dict):
        return {k: resolve_variables(v, brand_data) for k, v in obj.items()}
    return obj


def get_default_logo_path(brand_data: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """Lấy đường dẫn file logo mặc định của brand."""
    if brand_data is None:
        brand_data = load_brand_kit()

    logo_filename = brand_data.get("logo", "logo.png")
    logo_path = BRAND_DIR / logo_filename
    if logo_path.exists():
        return logo_path
    return None

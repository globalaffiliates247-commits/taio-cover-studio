"""
core/templates.py - Nạp, xác thực và thay thế biến thương hiệu trong các mẫu lớp phủ.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.paths import TEMPLATES_DIR
from core.brand import load_brand_kit, resolve_variables

logger = logging.getLogger("taio.templates")


def load_raw_template(template_path: Path) -> Optional[Dict[str, Any]]:
    """Đọc file json của một template, bỏ qua nếu lỗi cú pháp."""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                logger.warning(f"Bỏ qua template không hợp lệ (không phải dict): {template_path.name}")
                return None
            if "id" not in data or "layers" not in data:
                logger.warning(f"Bỏ qua template thiếu id hoặc layers: {template_path.name}")
                return None
            return data
    except Exception as e:
        logger.warning(f"Cảnh báo: Không thể phân tích template {template_path.name}: {e}")
        return None


def list_templates(templates_dir: Optional[Path] = None, brand_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Liệt kê toàn bộ các template hợp lệ, đã thay thế biến thương hiệu."""
    if templates_dir is None:
        templates_dir = TEMPLATES_DIR
    if brand_data is None:
        brand_data = load_brand_kit()

    templates: List[Dict[str, Any]] = []
    if not templates_dir.exists():
        return templates

    for json_file in sorted(templates_dir.glob("*.json")):
        raw = load_raw_template(json_file)
        if raw is not None:
            resolved = resolve_variables(raw, brand_data)
            templates.append(resolved)

    return templates


def get_template(template_id: str, templates_dir: Optional[Path] = None, brand_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Tìm một template theo id."""
    all_tpls = list_templates(templates_dir=templates_dir, brand_data=brand_data)
    for tpl in all_tpls:
        if tpl.get("id") == template_id:
            return tpl
    return None

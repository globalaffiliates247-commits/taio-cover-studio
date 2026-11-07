"""
core/overrides.py - Xử lý mô hình ghi đè (overrides) động lên template mà không sửa file mẫu.
Hỗ trợ sticker logo (vị trí tâm, xoay, phóng to/thu nhỏ, opacity) và caption style nâng cao.
"""

import copy
from typing import Any, Dict, Optional
from core.colors import parse_hex_color


def clamp(val: float, min_val: float, max_val: float) -> float:
    """Kẹp giá trị trong khoảng [min_val, max_val]."""
    return max(min_val, min(max_val, val))


def apply_overrides(
    template: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Tạo bản sao sâu (deep copy) của template và áp dụng các cấu hình overrides hợp lệ.
    Nếu overrides rỗng hoặc không hợp lệ, trả về bản sao nguyên bản (tương thích ngược 100%).
    """
    tpl_copy = copy.deepcopy(template)
    if not overrides or not isinstance(overrides, dict):
        return tpl_copy

    layer_overrides = overrides.get("layers")
    if not isinstance(layer_overrides, dict):
        return tpl_copy

    layers = tpl_copy.get("layers", [])
    for layer in layers:
        layer_id = layer.get("id") or layer.get("type")
        if not layer_id or layer_id not in layer_overrides:
            continue

        ov = layer_overrides[layer_id]
        if not isinstance(ov, dict):
            continue

        # Đánh dấu layer có override
        layer["has_override"] = True

        # 1. Ẩn/hiện (visible)
        if "visible" in ov:
            layer["visible"] = bool(ov["visible"])

        # 2. Toạ độ TÂM sticker và kích thước tỉ lệ theo khung
        if "x" in ov:
            try:
                layer["x"] = clamp(float(ov["x"]), -0.5, 1.5)
                layer["is_sticker"] = True
            except (ValueError, TypeError):
                pass

        if "y" in ov:
            try:
                layer["y"] = clamp(float(ov["y"]), -0.5, 1.5)
                layer["is_sticker"] = True
            except (ValueError, TypeError):
                pass

        if "w" in ov:
            try:
                layer["w"] = clamp(float(ov["w"]), 0.02, 1.5)
                layer["is_sticker"] = True
            except (ValueError, TypeError):
                pass

        # 3. Góc xoay (độ, -180 đến 180)
        if "rotation" in ov:
            try:
                rot = float(ov["rotation"]) % 360.0
                if rot > 180.0:
                    rot -= 360.0
                layer["rotation"] = rot
                layer["is_sticker"] = True
            except (ValueError, TypeError):
                pass

        # 4. Độ mờ (opacity, 0.0 đến 1.0)
        if "opacity" in ov:
            try:
                layer["opacity"] = clamp(float(ov["opacity"]), 0.0, 1.0)
            except (ValueError, TypeError):
                pass

        # 5. Khung viên thuốc (pill: boolean hoặc dict)
        if "pill" in ov:
            pill_val = ov["pill"]
            if isinstance(pill_val, bool):
                layer["pill_enabled"] = pill_val
            elif isinstance(pill_val, dict):
                layer["pill_enabled"] = True
                layer["pill"] = pill_val

        # 6. Style tuỳ chỉnh cho text / caption
        if "style" in ov and isinstance(ov["style"], dict):
            layer["style_override"] = ov["style"]
        if layer.get("type") == "caption":
            if "color" in ov:
                layer["color"] = ov["color"]
            if "accent" in ov:
                layer["accent"] = ov["accent"]

        # 7. Màu tuỳ chỉnh cho rect / gradient (color: hex string hoặc None)
        if "color" in ov:
            new_col = ov["color"]
            if new_col and isinstance(new_col, str) and new_col.strip():
                try:
                    c_rgb = parse_hex_color(new_col.strip())
                    nr, ng, nb = c_rgb[0], c_rgb[1], c_rgb[2]
                    darken_k = float(ov.get("gradient_darken", layer.get("gradient_darken", 0)))
                    if "fill" in layer and layer["fill"]:
                        old_fill = parse_hex_color(layer["fill"])
                        layer["fill"] = f"#{nr:02X}{ng:02X}{nb:02X}{old_fill[3]:02X}"
                    if "fill_to" in layer and layer["fill_to"]:
                        old_fill_to = parse_hex_color(layer["fill_to"])
                        if darken_k > 0:
                            mult = max(0.0, 1.0 - darken_k)
                            dr = max(0, min(255, int(round(nr * mult))))
                            dg = max(0, min(255, int(round(ng * mult))))
                            db = max(0, min(255, int(round(nb * mult))))
                            layer["fill_to"] = f"#{dr:02X}{dg:02X}{db:02X}{old_fill_to[3]:02X}"
                        else:
                            layer["fill_to"] = f"#{nr:02X}{ng:02X}{nb:02X}{old_fill_to[3]:02X}"
                except Exception:
                    pass

    return tpl_copy

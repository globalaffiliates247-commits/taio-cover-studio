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
        layer_overrides = {}

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

        # 8. Chiều cao & vị trí y cho dải nền (h, y)
        if "h" in ov:
            try:
                h_val = clamp(float(ov["h"]), 0.10, 0.90)
                layer["h"] = h_val
                if "y" in ov:
                    layer["y"] = clamp(float(ov["y"]), -0.5, 1.5)
                else:
                    layer["y"] = 1.0 - h_val
            except (ValueError, TypeError):
                pass

    # 9. Xử lý cơ chế parent: layer con tự động co giãn và di chuyển tương đối trong khung cha
    orig_layers_map = {l.get("id"): l for l in template.get("layers", []) if l.get("id")}
    for layer in layers:
        parent_id = layer.get("parent")
        if not parent_id or parent_id not in orig_layers_map:
            continue
        orig_parent = orig_layers_map[parent_id]
        cur_parent = next((l for l in layers if l.get("id") == parent_id), None)
        if not cur_parent:
            continue

        p_orig_y = float(orig_parent.get("y", 0))
        p_orig_h = float(orig_parent.get("h", 1))
        p_cur_y = float(cur_parent.get("y", p_orig_y))
        p_cur_h = float(cur_parent.get("h", p_orig_h))

        p_orig_x = float(orig_parent.get("x", 0))
        p_orig_w = float(orig_parent.get("w", 1))
        p_cur_x = float(cur_parent.get("x", p_orig_x))
        p_cur_w = float(cur_parent.get("w", p_orig_w))

        if p_orig_h > 0 and (p_cur_h != p_orig_h or p_cur_y != p_orig_y or p_cur_x != p_orig_x or p_cur_w != p_orig_w):
            if "box" in layer and isinstance(layer["box"], dict):
                orig_box = orig_layers_map[layer.get("id", "")].get("box", layer["box"])
                rel_y = (float(orig_box.get("y", 0)) - p_orig_y) / p_orig_h
                rel_h = float(orig_box.get("h", 0)) / p_orig_h
                rel_x = (float(orig_box.get("x", 0)) - p_orig_x) / (p_orig_w if p_orig_w > 0 else 1)
                rel_w = float(orig_box.get("w", 0)) / (p_orig_w if p_orig_w > 0 else 1)

                layer["box"] = copy.deepcopy(layer["box"])
                layer["box"]["y"] = p_cur_y + rel_y * p_cur_h
                layer["box"]["h"] = rel_h * p_cur_h
                layer["box"]["x"] = p_cur_x + rel_x * p_cur_w
                layer["box"]["w"] = rel_w * p_cur_w

    # 10. Xử lý scene objects (v1.4.0)
    scene_objects = overrides.get("objects")
    if scene_objects and isinstance(scene_objects, list):
        from core.scene import validate_scene
        is_valid, err_msg = validate_scene(scene_objects)
        if is_valid:
            tpl_copy["objects"] = scene_objects

    return tpl_copy

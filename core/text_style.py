"""
core/text_style.py - Chuẩn hoá, kiểm tra và áp dụng Text Styles cho layer Caption.
Hỗ trợ font, cỡ chữ (tự co / cố định), kiểu in hoa, màu chữ, 2 màu nhấn, viền, bóng, canh lề và vị trí dọc.
"""

from typing import Any, Dict, Optional, Tuple


def clamp_val(val: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(max_v, val))


def normalize_text_style(raw_style: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Chuẩn hoá và gán giá trị an toàn cho một dictionary style tuỳ chỉnh.
    """
    if not raw_style or not isinstance(raw_style, dict):
        return {}

    clean: Dict[str, Any] = {}

    # 1. Font & Trọng số
    if "font_family" in raw_style:
        clean["font_family"] = str(raw_style["font_family"]).strip()
    if "weight" in raw_style:
        clean["weight"] = str(raw_style["weight"]).strip()

    # 2. Cỡ chữ & chế độ cỡ (auto / fixed)
    if "size_mode" in raw_style:
        clean["size_mode"] = "fixed" if str(raw_style["size_mode"]).lower() == "fixed" else "auto"
    raw_s = raw_style.get("size_px")
    if raw_s is None:
        raw_s = raw_style.get("size")
    if raw_s is not None:
        try:
            val_s = float(raw_s)
            if val_s < 1.0:
                val_s = val_s * 1080.0
            clean["size_px"] = max(10, min(160, int(round(val_s))))
            clean["size"] = clean["size_px"]
        except (ValueError, TypeError):
            pass

    # 3. Kiểu chữ hoa (preserve / uppercase / title)
    if "case_mode" in raw_style:
        cm = str(raw_style["case_mode"]).lower()
        if cm in ("preserve", "uppercase", "title"):
            clean["case_mode"] = cm

    # 4. Màu sắc
    if "color" in raw_style and isinstance(raw_style["color"], str):
        clean["color"] = raw_style["color"].strip()
    if "accent_color" in raw_style and isinstance(raw_style["accent_color"], str):
        clean["accent_color"] = raw_style["accent_color"].strip()
    if "accent2_color" in raw_style and isinstance(raw_style["accent2_color"], str):
        clean["accent2_color"] = raw_style["accent2_color"].strip()
    if "accent_style" in raw_style:
        clean["accent_style"] = str(raw_style["accent_style"]).strip().lower()

    # 5. Viền chữ (stroke)
    if "stroke_width" in raw_style:
        try:
            clean["stroke_width"] = max(0, min(30, int(raw_style["stroke_width"])))
        except (ValueError, TypeError):
            pass
    if "stroke_color" in raw_style and isinstance(raw_style["stroke_color"], str):
        clean["stroke_color"] = raw_style["stroke_color"].strip()

    # 6. Đổ bóng (shadow)
    if "shadow_dx" in raw_style:
        try:
            clean["shadow_dx"] = clamp_val(float(raw_style["shadow_dx"]), -50.0, 50.0)
        except (ValueError, TypeError):
            pass
    if "shadow_dy" in raw_style:
        try:
            clean["shadow_dy"] = clamp_val(float(raw_style["shadow_dy"]), -50.0, 50.0)
        except (ValueError, TypeError):
            pass
    if "shadow_color" in raw_style and isinstance(raw_style["shadow_color"], str):
        clean["shadow_color"] = raw_style["shadow_color"].strip()
    if "shadow_blur" in raw_style:
        try:
            clean["shadow_blur"] = max(0, min(30, int(raw_style["shadow_blur"])))
        except (ValueError, TypeError):
            pass
    if "shadow_opacity" in raw_style:
        try:
            clean["shadow_opacity"] = clamp_val(float(raw_style["shadow_opacity"]), 0.0, 1.0)
        except (ValueError, TypeError):
            pass

    # 7. Canh lề & vị trí
    if "align" in raw_style:
        al = str(raw_style["align"]).lower()
        if al in ("left", "center", "right"):
            clean["align"] = al
    if "valign" in raw_style:
        val = str(raw_style["valign"]).lower()
        if val in ("top", "middle", "bottom"):
            clean["valign"] = val
    if "y_offset_ratio" in raw_style:
        try:
            clean["y_offset_ratio"] = clamp_val(float(raw_style["y_offset_ratio"]), -0.4, 0.4)
        except (ValueError, TypeError):
            pass

    # 8. Khoảng cách (letter spacing, line spacing) & ngắt dòng (wrap)
    if "wrap" in raw_style:
        clean["wrap"] = bool(raw_style["wrap"])
    if "letter_spacing" in raw_style:
        try:
            clean["letter_spacing"] = clamp_val(float(raw_style["letter_spacing"]), 0.0, 0.5)
        except (ValueError, TypeError):
            pass
    if "line_spacing" in raw_style:
        try:
            clean["line_spacing"] = clamp_val(float(raw_style["line_spacing"]), 0.8, 2.5)
        except (ValueError, TypeError):
            pass

    # 9. Nền chữ (bg_style: none, lines, block)
    if "bg_style" in raw_style:
        bgs = str(raw_style["bg_style"]).lower()
        if bgs in ("none", "lines", "block"):
            clean["bg_style"] = bgs
    if "bg_color" in raw_style and isinstance(raw_style["bg_color"], str):
        clean["bg_color"] = raw_style["bg_color"].strip()
    if "bg_opacity" in raw_style:
        try:
            clean["bg_opacity"] = clamp_val(float(raw_style["bg_opacity"]), 0.0, 1.0)
        except (ValueError, TypeError):
            pass
    if "bg_radius" in raw_style:
        try:
            clean["bg_radius"] = max(0, min(40, int(raw_style["bg_radius"])))
        except (ValueError, TypeError):
            pass
    if "bg_padding" in raw_style:
        try:
            clean["bg_padding"] = max(0, min(50, int(raw_style["bg_padding"])))
        except (ValueError, TypeError):
            pass

    return clean


def apply_text_style_to_layer(layer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hợp nhất style_override vào layer caption.
    """
    style_ov = layer.get("style_override")
    if not style_ov:
        return layer

    norm_style = normalize_text_style(style_ov)
    if not norm_style:
        return layer

    # Font & weight
    if "weight" in norm_style:
        layer["weight"] = norm_style["weight"]
    if "font_family" in norm_style:
        layer["font_family"] = norm_style["font_family"]

    # Cỡ chữ (FIX v1.6.0 FIX-5)
    if "size_mode" in norm_style:
        layer["size_mode"] = norm_style["size_mode"]
    if "wrap" in norm_style:
        layer["wrap"] = norm_style["wrap"]
    if "size_px" in norm_style:
        layer["fixed_size"] = norm_style["size_px"]
        layer["size_px"] = norm_style["size_px"]
    elif "size" in norm_style:
        s = norm_style["size"]
        sz = int(round(float(s) * 1080)) if float(s) < 1.0 else int(s)
        layer["fixed_size"] = sz
        layer["size_px"] = sz

    # In hoa / Kiểu chữ hoa
    if "case_mode" in norm_style:
        layer["case_mode"] = norm_style["case_mode"]
        if norm_style["case_mode"] == "uppercase":
            layer["uppercase"] = True
        elif norm_style["case_mode"] == "preserve":
            layer["uppercase"] = False
        elif norm_style["case_mode"] == "title":
            layer["uppercase"] = False

    # Màu chính và màu nhấn
    if "color" in norm_style:
        layer["color"] = norm_style["color"]
    if "accent_color" in norm_style:
        layer["accent"] = norm_style["accent_color"]
    if "accent2_color" in norm_style:
        layer["accent2"] = norm_style["accent2_color"]
    if "accent_style" in norm_style:
        layer["accent_style"] = norm_style["accent_style"]

    # Viền chữ
    if "stroke_width" in norm_style or "stroke_color" in norm_style:
        current_stroke = layer.get("stroke") or {}
        layer["stroke"] = {
            "width": norm_style.get("stroke_width", current_stroke.get("width", 0)),
            "color": norm_style.get("stroke_color", current_stroke.get("color", "#000000")),
            "is_ratio": False,  # Giá trị pixel trực tiếp từ override
        }

    # Đổ bóng
    if any(k in norm_style for k in ("shadow_dx", "shadow_dy", "shadow_color", "shadow_blur", "shadow_opacity")):
        current_shadow = layer.get("shadow") or {}
        layer["shadow"] = {
            "dx": norm_style.get("shadow_dx", current_shadow.get("dx", 0)),
            "dy": norm_style.get("shadow_dy", current_shadow.get("dy", 2)),
            "color": norm_style.get("shadow_color", current_shadow.get("color", "#000000")),
            "blur": norm_style.get("shadow_blur", 0),
            "opacity": norm_style.get("shadow_opacity", 0.8),
            "is_ratio": False,
        }

    # Canh lề và vị trí
    if "align" in norm_style:
        layer["align"] = norm_style["align"]
    if "valign" in norm_style:
        layer["valign"] = norm_style["valign"]
    if "y_offset_ratio" in norm_style:
        layer["y_offset_ratio"] = norm_style["y_offset_ratio"]

    # Khoảng cách
    if "letter_spacing" in norm_style:
        layer["letter_spacing"] = norm_style["letter_spacing"]
    if "line_spacing" in norm_style:
        layer["line_spacing"] = norm_style["line_spacing"]

    # Nền chữ (P5)
    if "bg_style" in norm_style:
        layer["bg_style"] = norm_style["bg_style"]
    if "bg_color" in norm_style:
        layer["bg_color"] = norm_style["bg_color"]
    if "bg_opacity" in norm_style:
        layer["bg_opacity"] = norm_style["bg_opacity"]
    if "bg_radius" in norm_style:
        layer["bg_radius"] = norm_style["bg_radius"]
    if "bg_padding" in norm_style:
        layer["bg_padding"] = norm_style["bg_padding"]

    return layer

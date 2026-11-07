"""
core/auto_contrast.py - Tự động điều chỉnh tương phản chữ caption trên nền sáng (v1.3.0).
Dựa trên tiêu chuẩn WCAG 2.1 (Contrast Minimum 3:1).
"""

import copy
import json
from typing import Any, Dict, Optional, Tuple
from core.colors import contrast_ratio, darken, parse_hex_color
from core.paths import CONFIG_DIR


def _load_palette_names() -> Dict[str, str]:
    """Tải bảng tên màu tiếng Việt từ palettes.json."""
    palettes_path = CONFIG_DIR / "palettes.json"
    names = {
        "#E53935": "Đỏ",
        "#FB8C00": "Cam",
        "#FDD835": "Vàng",
        "#43A047": "Xanh lá",
        "#1E88E5": "Xanh dương",
        "#8E24AA": "Tím",
    }
    if palettes_path.exists():
        try:
            with open(palettes_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for plist in data.values():
                    if isinstance(plist, list):
                        for item in plist:
                            if "hex" in item and "name" in item:
                                names[item["hex"].upper()] = item["name"]
        except Exception:
            pass
    return names


def get_color_name(hex_code: str) -> str:
    """Trả về tên tiếng Việt của mã màu hex hoặc fallback."""
    if not hex_code:
        return "mới"
    clean = hex_code.strip().upper()
    if len(clean) == 7:
        pass
    elif len(clean) == 9:
        clean = clean[:7]
    names = _load_palette_names()
    return names.get(clean, "mới")


def adjust_caption_contrast(
    template: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None,
    brand_data: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Kiểm tra độ tương phản giữa caption/accent và nền.
    Nếu contrast_ratio < 3:1 và người dùng chưa đặt màu chữ trong bảng Aa:
      - Tự đổi màu chữ sang #111111 hoặc #FFFFFF (chọn màu có độ tương phản cao hơn).
      - Tự đổi màu nhấn sang màu đạt >= 3:1 (thứ tự ưu tiên: #FFFFFF, #111111, $primary).
      - Trả về (overrides_đã_cập_nhật, thông_báo).
    """
    ov_copy = copy.deepcopy(overrides) if overrides else {}
    if "layers" not in ov_copy or not isinstance(ov_copy["layers"], dict):
        ov_copy["layers"] = {}
    layer_ovs = ov_copy["layers"]

    layers = template.get("layers", [])
    caption_layer = None
    bg_layer = None

    tpl_id = template.get("id", "")
    target_bg_id = {
        "lower_third_fade": "bg_fade",
        "footer_band": "bg_band",
        "top_bottom_bars": "top_bar",
        "vertical_9x16_footer": "bg_band",
    }.get(tpl_id)

    for l in layers:
        lid = l.get("id") or l.get("type")
        if lid == "caption" or l.get("type") == "caption":
            caption_layer = l
        elif target_bg_id and lid == target_bg_id:
            bg_layer = l
        elif not bg_layer and l.get("type") == "rect":
            bg_layer = l

    if not caption_layer or not bg_layer:
        return ov_copy, None

    # Xác định màu nền ở mép dưới của dải (nơi đậm nhất)
    bg_id = bg_layer.get("id") or bg_layer.get("type")
    bg_ov = layer_ovs.get(bg_id, {})
    bg_color_override = bg_ov.get("color")

    brand_colors = (brand_data or {}).get("colors", {})
    primary_hex = brand_colors.get("primary", "#1A56DB")

    color_name = "mới"
    if bg_color_override and isinstance(bg_color_override, str) and bg_color_override.strip():
        base_hex = bg_color_override.strip()
        color_name = get_color_name(base_hex)
        darken_k = float(bg_ov.get("gradient_darken", bg_layer.get("gradient_darken", 0)))
        if darken_k > 0:
            eff_bg = darken(base_hex, darken_k)
        else:
            eff_bg = base_hex
    else:
        # Màu gốc của template
        fill_val = bg_layer.get("fill_to") or bg_layer.get("fill") or "#000000"
        if isinstance(fill_val, str) and fill_val.startswith("$"):
            tok = fill_val[1:]
            eff_bg = brand_colors.get(tok, "#000000")
        else:
            eff_bg = fill_val

    # Kiểm tra xem người dùng đã tự đặt màu chữ hay chưa
    caption_ov = layer_ovs.get("caption", {})
    style_ov = caption_ov.get("style", {})
    user_set_color = bool(style_ov.get("color") or caption_ov.get("color"))
    user_set_accent = bool(style_ov.get("accent_color") or caption_ov.get("accent"))

    # Lấy màu chữ hiện tại
    current_text_col = style_ov.get("color") or caption_ov.get("color") or caption_layer.get("color", "#FFFFFF")
    if isinstance(current_text_col, str) and current_text_col.startswith("$"):
        current_text_col = brand_colors.get(current_text_col[1:], "#FFFFFF")

    # Lấy màu nhấn hiện tại
    current_accent_col = style_ov.get("accent_color") or caption_ov.get("accent") or caption_layer.get("accent", "$accent")
    if isinstance(current_accent_col, str) and current_accent_col.startswith("$"):
        current_accent_col = brand_colors.get(current_accent_col[1:], "#FFD34D")

    notice_msg = None
    adjusted = False

    # 1. Điều chỉnh màu chữ
    text_ratio = contrast_ratio(current_text_col, eff_bg)
    chosen_text_col = current_text_col

    if text_ratio < 3.0 and not user_set_color:
        ratio_dark = contrast_ratio("#111111", eff_bg)
        ratio_light = contrast_ratio("#FFFFFF", eff_bg)
        chosen_text_col = "#111111" if ratio_dark >= ratio_light else "#FFFFFF"

        if "caption" not in layer_ovs:
            layer_ovs["caption"] = {}
        layer_ovs["caption"]["color"] = chosen_text_col
        if "style" not in layer_ovs["caption"] or not isinstance(layer_ovs["caption"]["style"], dict):
            layer_ovs["caption"]["style"] = {}
        layer_ovs["caption"]["style"]["color"] = chosen_text_col

        adjusted = True
        notice_msg = f"Đã tự đổi màu chữ để dễ đọc trên nền {color_name}"

    # 2. Điều chỉnh màu nhấn
    accent_ratio = contrast_ratio(current_accent_col, eff_bg)
    if accent_ratio < 3.0 and not user_set_accent:
        # Thứ tự ưu tiên: #FFFFFF, #111111, $primary
        candidates = ["#FFFFFF", "#111111", primary_hex]
        chosen_accent = None

        # Ưu tiên ứng viên có tương phản >= 3:1 và khác màu chữ chính
        for cand in candidates:
            if contrast_ratio(cand, eff_bg) >= 3.0 and cand.upper() != chosen_text_col.upper():
                chosen_accent = cand
                break

        # Nếu không có ứng viên nào khác màu chữ, chọn ứng viên đầu tiên đạt >= 3:1
        if not chosen_accent:
            for cand in candidates:
                if contrast_ratio(cand, eff_bg) >= 3.0:
                    chosen_accent = cand
                    break

        if chosen_accent:
            if "caption" not in layer_ovs:
                layer_ovs["caption"] = {}
            layer_ovs["caption"]["accent"] = chosen_accent
            if "style" not in layer_ovs["caption"] or not isinstance(layer_ovs["caption"]["style"], dict):
                layer_ovs["caption"]["style"] = {}
            layer_ovs["caption"]["style"]["accent_color"] = chosen_accent

            adjusted = True
            if not notice_msg:
                notice_msg = f"Đã tự đổi màu chữ để dễ đọc trên nền {color_name}"

    return ov_copy, notice_msg

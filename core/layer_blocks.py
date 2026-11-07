"""
core/layer_blocks.py - Kết xuất các khối đồ hoạ độc lập (như logo block) thành ảnh RGBA.
Được sử dụng cho cả overlay_renderer lẫn endpoint /api/layer-image phục vụ kéo thả sticker.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from PIL import Image, ImageDraw

from core.brand import get_default_logo_path, load_brand_kit
from core.colors import parse_hex_color
from core.text_layout import get_font, prepare_caption_text


def render_logo_block(
    layer: Dict[str, Any],
    logo_path: Optional[str] = None,
    scale_px: Optional[int] = None,
    pill_override: Optional[bool] = None,
    base_h: int = 140,
) -> Image.Image:
    """
    Vẽ độc lập khối logo (gồm ảnh logo + nhãn tên thương hiệu + khung viên thuốc pill tuỳ chọn).
    Trả về PIL Image RGBA có nền trong suốt, vừa khít nội dung.
    """
    # 1. Xác định file logo
    if not logo_path or not os.path.exists(logo_path):
        default_logo = get_default_logo_path()
        if default_logo and default_logo.exists():
            logo_path = str(default_logo)

    lh = max(base_h, 32)
    logo_img = None
    if logo_path and os.path.exists(logo_path):
        try:
            raw_img = Image.open(logo_path).convert("RGBA")
            scale = lh / float(raw_img.height)
            target_lw = max(int(round(raw_img.width * scale)), 1)
            logo_img = raw_img.resize((target_lw, lh), Image.Resampling.LANCZOS)
        except Exception:
            pass

    # 2. Xử lý nhãn chữ
    label = layer.get("label", "").strip()
    # Nếu layer không ghi nhãn và không có logo_img, lấy tên brand mặc định
    if not label and not logo_img:
        bkit = load_brand_kit()
        label = bkit.get("name", "TAIO.CLUB")

    weight = layer.get("weight", "Bold")
    font_size = max(int(round(lh * 0.52)), 14)
    font = get_font(weight, font_size)

    label_w = 0.0
    label_h = 0.0
    norm_label = ""
    if label:
        norm_label = prepare_caption_text(label, uppercase=False)
        l_bbox = font.getbbox(norm_label)
        if l_bbox:
            label_w = float(l_bbox[2] - l_bbox[0])
            label_h = float(l_bbox[3] - l_bbox[1])

    gap = int(round(lh * 0.22)) if (logo_img and norm_label) else 0

    content_w = 0.0
    if logo_img:
        content_w += logo_img.width
    if gap > 0:
        content_w += gap
    if norm_label:
        content_w += label_w

    # 3. Cấu hình Pill
    has_pill = False
    if pill_override is True:
        has_pill = True
    elif pill_override is False:
        has_pill = False
    else:
        has_pill = bool(layer.get("pill") or layer.get("pill_enabled", False))

    pill_cfg = layer.get("pill") or {}
    pad = int(round(lh * 0.22)) if has_pill else 0

    total_w = int(round(content_w + pad * 2))
    total_h = int(round(lh + pad * 2))

    block_img = Image.new("RGBA", (max(total_w, 10), max(total_h, 10)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(block_img)

    # 4. Vẽ Pill nếu được kích hoạt
    if has_pill:
        pill_fill_hex = pill_cfg.get("fill") if isinstance(pill_cfg, dict) else None
        pill_stroke_hex = pill_cfg.get("stroke") if isinstance(pill_cfg, dict) else None
        pill_stroke_w = int(round(lh * 0.04)) if isinstance(pill_cfg, dict) else 2

        c_pill_fill = parse_hex_color(pill_fill_hex or "#00000080")
        c_pill_stroke = parse_hex_color(pill_stroke_hex or "#FFFFFF40")

        p_radius = total_h // 2
        pill_bbox = [0, 0, total_w, total_h]
        draw.rounded_rectangle(pill_bbox, radius=p_radius, fill=c_pill_fill)
        if pill_stroke_w > 0 and c_pill_stroke:
            draw.rounded_rectangle(pill_bbox, radius=p_radius, outline=c_pill_stroke, width=pill_stroke_w)

    # 5. Dán Logo
    curr_x = float(pad)
    curr_y = float(pad)
    if logo_img:
        block_img.paste(logo_img, (int(round(curr_x)), int(round(curr_y))), logo_img)
        curr_x += logo_img.width + gap

    # 6. Vẽ chữ nhãn
    if norm_label:
        color_hex = layer.get("color", "#FFFFFF")
        font_color = parse_hex_color(color_hex)
        # Canh dọc giữa nhãn với lh
        text_y = curr_y + (lh - label_h) / 2.0
        # Bù độ lệch font baseline
        l_bbox = font.getbbox(norm_label)
        if l_bbox:
            text_y -= float(l_bbox[1])
        draw.text((int(round(curr_x)), int(round(text_y))), norm_label, font=font, fill=font_color)

    # 7. Phóng to / thu nhỏ nếu có scale_px
    if scale_px and scale_px > 0:
        max_edge = max(block_img.width, block_img.height)
        if max_edge > 0 and max_edge != scale_px:
            ratio = scale_px / float(max_edge)
            new_w = max(int(round(block_img.width * ratio)), 1)
            new_h = max(int(round(block_img.height * ratio)), 1)
            block_img = block_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return block_img

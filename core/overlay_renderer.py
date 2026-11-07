"""
core/overlay_renderer.py - Vẽ toàn bộ các layer của template lên ảnh RGBA trong suốt.
Mỗi loại layer được thực thi bởi một hàm riêng và đăng ký trong LAYER_DRAWERS.
"""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from core.colors import parse_hex_color
from core.canvas import CanvasLayout
from core.text_layout import (
    compute_text_layout,
    get_font,
    prepare_caption_text,
    TextSpan,
)


def _draw_gradient_rect(
    img: Image.Image,
    bbox: Tuple[int, int, int, int],
    c1: Tuple[int, int, int, int],
    c2: Tuple[int, int, int, int],
    direction: str = "vertical",
    radius: int = 0,
):
    """Vẽ hình chữ nhật dải màu gradient (dọc hoặc ngang), hỗ trợ bo góc."""
    x1, y1, x2, y2 = bbox
    w = max(x2 - x1, 1)
    h = max(y2 - y1, 1)

    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)

    if direction == "horizontal":
        for i in range(w):
            factor = i / max(w - 1, 1)
            r = int(c1[0] + (c2[0] - c1[0]) * factor)
            g = int(c1[1] + (c2[1] - c1[1]) * factor)
            b = int(c1[2] + (c2[2] - c1[2]) * factor)
            a = int(c1[3] + (c2[3] - c1[3]) * factor)
            grad_draw.line([(i, 0), (i, h)], fill=(r, g, b, a))
    else:  # vertical
        for j in range(h):
            factor = j / max(h - 1, 1)
            r = int(c1[0] + (c2[0] - c1[0]) * factor)
            g = int(c1[1] + (c2[1] - c1[1]) * factor)
            b = int(c1[2] + (c2[2] - c1[2]) * factor)
            a = int(c1[3] + (c2[3] - c1[3]) * factor)
            grad_draw.line([(0, j), (w, j)], fill=(r, g, b, a))

    if radius > 0:
        mask = Image.new("L", (w, h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
        img.paste(grad, (x1, y1), mask)
    else:
        img.paste(grad, (x1, y1), grad)


def _draw_rect(
    overlay: Image.Image,
    layer: Dict[str, Any],
    layout: CanvasLayout,
    context: Dict[str, Any],
    warnings: List[str],
):
    """Vẽ layer hình chữ nhật / dải màu."""
    w, h = layout.out_w, layout.out_h
    unit = layout.unit

    lx = int(round(layer.get("x", 0) * w))
    ly = int(round(layer.get("y", 0) * h))
    lw = int(round(layer.get("w", 1) * w))
    lh = int(round(layer.get("h", 0.1) * h))

    radius_ratio = layer.get("radius", 0)
    radius = int(round(radius_ratio * unit)) if radius_ratio else 0

    fill_hex = layer.get("fill")
    fill_to_hex = layer.get("fill_to")

    stroke_hex = layer.get("stroke")
    stroke_w_ratio = layer.get("stroke_width", 0)
    stroke_w = int(round(stroke_w_ratio * unit)) if stroke_w_ratio else 0

    c_fill = parse_hex_color(fill_hex) if fill_hex else None
    c_stroke = parse_hex_color(stroke_hex) if stroke_hex else None

    if fill_to_hex and c_fill:
        # Gradient
        c_fill_to = parse_hex_color(fill_to_hex)
        direction = layer.get("direction", "vertical")
        _draw_gradient_rect(overlay, (lx, ly, lx + lw, ly + lh), c_fill, c_fill_to, direction=direction, radius=radius)
    elif c_fill:
        draw = ImageDraw.Draw(overlay)
        bbox = [lx, ly, lx + lw, ly + lh]
        if radius > 0:
            draw.rounded_rectangle(bbox, radius=radius, fill=c_fill)
        else:
            draw.rectangle(bbox, fill=c_fill)

    # Stroke nếu có
    if c_stroke and stroke_w > 0:
        draw = ImageDraw.Draw(overlay)
        bbox = [lx, ly, lx + lw, ly + lh]
        if radius > 0:
            draw.rounded_rectangle(bbox, radius=radius, outline=c_stroke, width=stroke_w)
        else:
            draw.rectangle(bbox, outline=c_stroke, width=stroke_w)


def _draw_caption(
    overlay: Image.Image,
    layer: Dict[str, Any],
    layout: CanvasLayout,
    context: Dict[str, Any],
    warnings: List[str],
):
    """Vẽ caption với tự co cỡ chữ, tô màu từ nhấn **...**, đổ bóng và viền chữ."""
    caption_text = context.get("caption", "").strip()
    if not caption_text:
        return

    w, h = layout.out_w, layout.out_h
    unit = layout.unit
    box = layer.get("box", {"x": 0.05, "y": 0.7, "w": 0.9, "h": 0.25})

    bx = int(round(box.get("x", 0) * w))
    by = int(round(box.get("y", 0) * h))
    bw = int(round(box.get("w", 1) * w))
    bh = int(round(box.get("h", 0.2) * h))

    weight = layer.get("weight", "Black")
    uppercase = layer.get("uppercase", True)
    max_size = layer.get("max_size", 0.075)
    min_size = layer.get("min_size", 0.032)
    line_spacing = layer.get("line_spacing", 1.18)
    max_lines = layer.get("max_lines", 4)

    align = layer.get("align", "center")
    valign = layer.get("valign", "middle")

    # Màu sắc
    main_color = parse_hex_color(layer.get("color", "#FFFFFF"))
    raw_accent = layer.get("accent")
    if raw_accent and not str(raw_accent).startswith("$"):
        accent_color = parse_hex_color(raw_accent)
    else:
        accent_color = (255, 211, 77, 255)  # Luôn đảm bảo màu vàng #FFD34D chuẩn xác

    # Đổ bóng & Viền
    shadow_cfg = layer.get("shadow")
    stroke_cfg = layer.get("stroke")

    shadow_color = parse_hex_color(shadow_cfg.get("color")) if shadow_cfg else None
    shadow_dx = int(round(shadow_cfg.get("dx", 0) * unit)) if shadow_cfg else 0
    shadow_dy = int(round(shadow_cfg.get("dy", 0) * unit)) if shadow_cfg else 0

    stroke_color = parse_hex_color(stroke_cfg.get("color")) if stroke_cfg else None
    stroke_w = int(round(stroke_cfg.get("width", 0) * unit)) if stroke_cfg else 0

    # Tính toán layout
    result = compute_text_layout(
        raw_text=caption_text,
        box_w=bw,
        box_h=bh,
        unit=unit,
        weight=weight,
        uppercase=uppercase,
        max_size_ratio=max_size,
        min_size_ratio=min_size,
        line_spacing=line_spacing,
        max_lines=max_lines,
    )

    if result.warning:
        warnings.append(result.warning)

    draw = ImageDraw.Draw(overlay)

    # Tính toạ độ dọc bắt đầu (valign)
    if valign == "top":
        start_y = by
    elif valign == "bottom":
        start_y = by + (bh - result.total_h)
    else:  # middle
        start_y = by + (bh - result.total_h) / 2.0

    current_y = start_y
    font = result.font

    for line in result.lines:
        # Tính toạ độ ngang bắt đầu (align)
        if align == "left":
            current_x = float(bx)
        elif align == "right":
            current_x = float(bx + (bw - line.width))
        else:  # center
            current_x = float(bx + (bw - line.width) / 2.0)

        for span in line.spans:
            if not span.text:
                continue

            text_color = accent_color if span.is_accent else main_color

            # 1. Vẽ bóng (shadow) nếu có
            if shadow_color:
                draw.text(
                    (current_x + shadow_dx, current_y + shadow_dy),
                    span.text,
                    font=font,
                    fill=shadow_color,
                )

            # 2. Vẽ viền (stroke) nếu có
            if stroke_color and stroke_w > 0:
                draw.text(
                    (current_x, current_y),
                    span.text,
                    font=font,
                    fill=text_color,
                    stroke_width=stroke_w,
                    stroke_fill=stroke_color,
                )
            else:
                draw.text(
                    (current_x, current_y),
                    span.text,
                    font=font,
                    fill=text_color,
                )

            # Tăng current_x bằng getlength chính xác
            try:
                span_w = float(font.getlength(span.text))
            except Exception:
                span_bbox = font.getbbox(span.text)
                span_w = float(span_bbox[2] - span_bbox[0]) if span_bbox else 0.0
            current_x += span_w

        current_y += result.line_height


def _draw_logo(
    overlay: Image.Image,
    layer: Dict[str, Any],
    layout: CanvasLayout,
    context: Dict[str, Any],
    warnings: List[str],
):
    """Vẽ logo thương hiệu (ảnh + tên thương hiệu trong khung viên thuốc pill tuỳ chọn)."""
    w, h = layout.out_w, layout.out_h
    unit = layout.unit

    lh = max(int(round(layer.get("h", 0.07) * h)), 16)
    lx = int(round(layer.get("x", 0.05) * w))
    ly = int(round(layer.get("y", 0.05) * h))

    anchor = layer.get("anchor", "left")
    label = layer.get("label", "").strip()
    color_hex = layer.get("color", "#FFFFFF")
    font_color = parse_hex_color(color_hex)
    weight = layer.get("weight", "Bold")

    gap = int(round(layer.get("gap", 0.012) * unit))
    pill_cfg = layer.get("pill")

    # Lấy đường dẫn file logo
    logo_path = context.get("logo_path")
    logo_img = None
    if logo_path and os.path.exists(logo_path):
        try:
            raw_img = Image.open(logo_path).convert("RGBA")
            # Scale logo sao cho chiều cao khớp lh
            scale = lh / float(raw_img.height)
            target_lw = max(int(round(raw_img.width * scale)), 1)
            logo_img = raw_img.resize((target_lw, lh), Image.Resampling.LANCZOS)
        except Exception as e:
            warnings.append(f"Không thể đọc ảnh logo: {e}")

    # Chuẩn bị font cho label
    font_size = max(int(round(lh * 0.55)), 12)
    font = get_font(weight, font_size)

    label_w = 0.0
    label_h = 0.0
    if label:
        norm_label = prepare_caption_text(label, uppercase=False)
        l_bbox = font.getbbox(norm_label)
        if l_bbox:
            label_w = float(l_bbox[2] - l_bbox[0])
            label_h = float(l_bbox[3] - l_bbox[1])
    else:
        norm_label = ""

    # Tổng kích thước khối nội dung (content width)
    content_w = 0.0
    if logo_img:
        content_w += logo_img.width
    if logo_img and norm_label:
        content_w += gap
    if norm_label:
        content_w += label_w

    pad = int(round(pill_cfg.get("pad", 0.012) * unit)) if pill_cfg else 0
    pill_w = int(round(content_w + pad * 2))
    pill_h = int(round(lh + pad * 2))

    # Căn chỉnh vị trí theo anchor
    if anchor == "right":
        target_x = lx - pill_w
    elif anchor == "center":
        target_x = int(lx - pill_w / 2.0)
    else:  # left
        target_x = lx

    target_y = ly

    # 1. Vẽ Pill nếu có
    if pill_cfg:
        pill_fill_hex = pill_cfg.get("fill")
        pill_stroke_hex = pill_cfg.get("stroke")
        pill_stroke_w = int(round(pill_cfg.get("stroke_width", 0.003) * unit))

        c_pill_fill = parse_hex_color(pill_fill_hex) if pill_fill_hex else None
        c_pill_stroke = parse_hex_color(pill_stroke_hex) if pill_stroke_hex else None

        radius_str = pill_cfg.get("radius", "full")
        if radius_str == "full":
            p_radius = pill_h // 2
        else:
            try:
                p_radius = int(round(float(radius_str) * unit))
            except Exception:
                p_radius = pill_h // 2

        draw = ImageDraw.Draw(overlay)
        pill_bbox = [target_x, target_y, target_x + pill_w, target_y + pill_h]
        if c_pill_fill:
            draw.rounded_rectangle(pill_bbox, radius=p_radius, fill=c_pill_fill)
        if c_pill_stroke and pill_stroke_w > 0:
            draw.rounded_rectangle(pill_bbox, radius=p_radius, outline=c_pill_stroke, width=pill_stroke_w)

        inner_x = target_x + pad
        inner_y = target_y + pad
    else:
        inner_x = target_x
        inner_y = target_y

    # 2. Vẽ Logo icon
    if logo_img:
        overlay.paste(logo_img, (int(round(inner_x)), int(round(inner_y))), logo_img)
        inner_x += logo_img.width + gap

    # 3. Vẽ Label chữ
    if norm_label:
        draw = ImageDraw.Draw(overlay)
        # Căn giữa dọc theo lh
        text_y = inner_y + (lh - label_h) / 2.0 - 1
        draw.text((inner_x, text_y), norm_label, font=font, fill=font_color)


def _draw_text(
    overlay: Image.Image,
    layer: Dict[str, Any],
    layout: CanvasLayout,
    context: Dict[str, Any],
    warnings: List[str],
):
    """Vẽ layer chữ phụ (ví dụ @handle, tagline...)."""
    w, h = layout.out_w, layout.out_h
    unit = layout.unit

    raw_text = layer.get("text", "").strip()
    if not raw_text:
        return

    box = layer.get("box")
    if box:
        bx = int(round(box.get("x", 0) * w))
        by = int(round(box.get("y", 0) * h))
        bw = int(round(box.get("w", 1) * w))
        bh = int(round(box.get("h", 0.05) * h))
    else:
        bx = int(round(layer.get("x", 0) * w))
        by = int(round(layer.get("y", 0) * h))
        bw = int(round(layer.get("w", 0.5) * w))
        bh = int(round(layer.get("h", 0.05) * h))

    size_ratio = layer.get("size", 0.035)
    font_size = max(int(round(size_ratio * unit)), 10)
    weight = layer.get("weight", "Bold")
    font = get_font(weight, font_size)

    color_hex = layer.get("color", "#FFFFFF")
    text_color = parse_hex_color(color_hex)
    align = layer.get("align", "left")
    valign = layer.get("valign", "middle")

    norm_text = prepare_caption_text(raw_text, uppercase=layer.get("uppercase", False))
    bbox = font.getbbox(norm_text)
    tw = float(bbox[2] - bbox[0]) if bbox else 0.0
    th = float(bbox[3] - bbox[1]) if bbox else float(font_size)

    if align == "right":
        tx = bx + (bw - tw)
    elif align == "center":
        tx = bx + (bw - tw) / 2.0
    else:
        tx = bx

    if valign == "bottom":
        ty = by + (bh - th)
    elif valign == "top":
        ty = by
    else:  # middle
        ty = by + (bh - th) / 2.0

    draw = ImageDraw.Draw(overlay)
    draw.text((tx, ty), norm_text, font=font, fill=text_color)


def _draw_image(
    overlay: Image.Image,
    layer: Dict[str, Any],
    layout: CanvasLayout,
    context: Dict[str, Any],
    warnings: List[str],
):
    """Vẽ layer ảnh tĩnh bổ sung."""
    src = layer.get("src")
    if not src or not os.path.exists(src):
        warnings.append(f"Không tìm thấy ảnh: {src}")
        return

    try:
        img = Image.open(src).convert("RGBA")
        w, h = layout.out_w, layout.out_h

        lx = int(round(layer.get("x", 0) * w))
        ly = int(round(layer.get("y", 0) * h))
        lw = int(round(layer.get("w", 0.2) * w))
        lh = int(round(layer.get("h", 0.1) * h))

        resized = img.resize((lw, lh), Image.Resampling.LANCZOS)
        opacity = float(layer.get("opacity", 1.0))
        if opacity < 1.0:
            alpha = resized.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            resized.putalpha(alpha)

        overlay.paste(resized, (lx, ly), resized)
    except Exception as e:
        warnings.append(f"Lỗi khi vẽ layer image: {e}")


# Bảng tra cứu ánh xạ từng loại layer với hàm vẽ tương ứng
LAYER_DRAWERS: Dict[str, Callable] = {
    "rect": _draw_rect,
    "caption": _draw_caption,
    "logo": _draw_logo,
    "text": _draw_text,
    "image": _draw_image,
}


def render_overlay(
    template: Dict[str, Any],
    layout: CanvasLayout,
    caption: str,
    logo_path: Optional[str] = None,
) -> Tuple[Image.Image, List[str]]:
    """
    Vẽ toàn bộ các layer của template lên một ảnh RGBA trong suốt có kích thước (out_w, out_h).
    Trả về (overlay_image, warnings_list).
    """
    overlay = Image.new("RGBA", (layout.out_w, layout.out_h), (0, 0, 0, 0))
    warnings: List[str] = []

    context = {
        "caption": caption,
        "logo_path": logo_path,
    }

    layers = template.get("layers", [])
    for layer in layers:
        if layer.get("hidden", False):
            continue

        l_type = layer.get("type")
        drawer = LAYER_DRAWERS.get(l_type)

        if drawer is None:
            warnings.append(f"Bỏ qua layer không hỗ trợ: '{l_type}'")
            continue

        try:
            drawer(overlay, layer, layout, context, warnings)
        except Exception as e:
            warnings.append(f"Lỗi khi vẽ layer {l_type}: {e}")

    return overlay, warnings

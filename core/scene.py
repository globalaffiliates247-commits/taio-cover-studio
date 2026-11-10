"""
core/scene.py - Quản lý mô hình Scene đối tượng đồ hoạ động (v1.4.0).
Bao gồm:
- validate_scene: kiểm tra tính hợp lệ và giới hạn số lượng đối tượng (tối đa 10 chữ, 3 ảnh).
- render_objects: kết xuất các đối tượng theo thứ tự z-index lên overlay RGBA.
- render_single_object_image: kết xuất một đối tượng độc lập thành ảnh PNG (cho POST /api/object-image).
"""

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from core.brand import get_default_logo_path, load_brand_kit
from core.canvas import CanvasLayout
from core.colors import parse_hex_color
from core.paths import FONTS_DIR
from core.text_layout import get_font, prepare_caption_text

# Giới hạn tối đa của Scene để bảo toàn RAM Render Free
MAX_TEXT_OBJECTS = 10
MAX_IMAGE_OBJECTS = 3

# LRU Cache cho object-image (tối đa 50 ảnh PNG)
_OBJECT_IMAGE_CACHE: Dict[str, bytes] = {}
_OBJECT_CACHE_KEYS: List[str] = []
MAX_OBJECT_CACHE_SIZE = 50


def clear_object_image_cache():
    """Xoá sạch bộ nhớ đệm object-image."""
    global _OBJECT_IMAGE_CACHE, _OBJECT_CACHE_KEYS
    _OBJECT_IMAGE_CACHE.clear()
    _OBJECT_CACHE_KEYS.clear()


def count_scene_objects(objects: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Đếm tổng số đối tượng text và image trong scene (kể cả phần tử con trong group)."""
    text_count = 0
    image_count = 0

    for obj in objects:
        if not isinstance(obj, dict):
            continue
        obj_type = obj.get("type")
        if obj_type == "text":
            text_count += 1
        elif obj_type == "image":
            image_count += 1
        elif obj_type == "group":
            for child in obj.get("children", []):
                if not isinstance(child, dict):
                    continue
                c_type = child.get("type")
                if c_type == "text":
                    text_count += 1
                elif c_type == "image":
                    image_count += 1

    return text_count, image_count


def validate_scene(objects: Any) -> Tuple[bool, Optional[str]]:
    """
    Kiểm tra tính hợp lệ của cấu trúc scene.
    Giới hạn: tối đa 10 đối tượng chữ, 3 đối tượng ảnh.
    """
    if not isinstance(objects, list):
        return False, "Cấu trúc scene phải là một mảng các đối tượng (list)"

    text_count, image_count = count_scene_objects(objects)
    if text_count > MAX_TEXT_OBJECTS:
        return False, f"Vượt quá giới hạn tối đa {MAX_TEXT_OBJECTS} đối tượng chữ (hiện có {text_count})"
    if image_count > MAX_IMAGE_OBJECTS:
        return False, f"Vượt quá giới hạn tối đa {MAX_IMAGE_OBJECTS} đối tượng ảnh (hiện có {image_count})"

    valid_types = {"group", "text", "image"}
    for idx, obj in enumerate(objects):
        if not isinstance(obj, dict):
            return False, f"Đối tượng tại vị trí {idx} không hợp lệ (phải là object)"
        obj_type = obj.get("type")
        if obj_type not in valid_types:
            return False, f"Loại đối tượng '{obj_type}' không được hỗ trợ (chỉ hỗ trợ: {', '.join(valid_types)})"
        if "id" not in obj or not str(obj["id"]).strip():
            return False, f"Đối tượng tại vị trí {idx} thiếu trường 'id'"

    return True, None


def _resolve_image_source(src: str, ctx: Optional[Dict[str, Any]] = None) -> Optional[Image.Image]:
    """Giải quyết nguồn ảnh từ file hoặc từ brand kit logo."""
    if not src:
        # Mặc định lấy logo brand
        ctx_logo = ctx.get("logo_path") if ctx else None
        if ctx_logo and os.path.exists(ctx_logo):
            return Image.open(ctx_logo).convert("RGBA")
        def_logo = get_default_logo_path()
        if def_logo and def_logo.exists():
            return Image.open(str(def_logo)).convert("RGBA")
        return None

    if src.startswith("brand|") or src == "brand":
        ctx_logo = ctx.get("logo_path") if ctx else None
        if ctx_logo and os.path.exists(ctx_logo):
            return Image.open(ctx_logo).convert("RGBA")
        def_logo = get_default_logo_path()
        if def_logo and def_logo.exists():
            return Image.open(str(def_logo)).convert("RGBA")
        return None

    if os.path.exists(src):
        try:
            return Image.open(src).convert("RGBA")
        except Exception:
            return None

    # Thử tìm trong workspace hoặc brand
    cand_path = Path(src)
    if cand_path.exists():
        try:
            return Image.open(str(cand_path)).convert("RGBA")
        except Exception:
            return None

    return None


def _parse_text_spans(text: str, default_color: str, accent_color: str) -> List[Tuple[str, str]]:
    """Phân tách chuỗi text thành các span (chữ thường hoặc nhấn **từ khóa**)."""
    spans: List[Tuple[str, str]] = []
    parts = text.split("**")
    is_accent = False
    for part in parts:
        if part:
            color = accent_color if is_accent else default_color
            spans.append((part, color))
        is_accent = not is_accent
    return spans


def render_text_to_image(
    text: str,
    style: Dict[str, Any],
    max_w: int = 1080,
    accent_color: str = "#FFD34D",
) -> Image.Image:
    """
    Vẽ chữ định dạng (hỗ trợ xuống dòng, **nhấn**, font, cỡ, viền, bóng, nền) thành PIL Image RGBA.
    """
    family = style.get("font") or "BeVietnamPro"
    weight = style.get("weight") or "Bold"
    font_size = max(int(round(float(style.get("size", 0.04)) * max_w)), 12)
    color_hex = style.get("color") or "#FFFFFF"
    accent_hex = style.get("accent") or accent_color
    align = style.get("align", "center")  # 'left' | 'center' | 'right'

    font = get_font(weight=weight, size=font_size, family=family)

    # Viền chữ (stroke)
    stroke_w = int(round(float(style.get("stroke_width", 0)) * (font_size / 32.0)))
    stroke_col_hex = style.get("stroke_color") or "#000000"
    c_stroke = parse_hex_color(stroke_col_hex) if stroke_w > 0 else None

    # Bóng đổ (shadow)
    shadow_dy = int(round(float(style.get("shadow_dy", 0)) * (font_size / 32.0)))
    shadow_col_hex = style.get("shadow_color") or "#00000088"
    c_shadow = parse_hex_color(shadow_col_hex) if shadow_dy > 0 else None

    lines = text.split("\n") if text else [""]
    line_spacing = float(style.get("line_spacing", 1.2))

    # Tính toán bounding box của từng dòng
    line_layouts = []
    total_w = 0
    total_h = 0
    ascent, descent = font.getmetrics()
    line_h = int(round((ascent + descent) * line_spacing))

    for line_str in lines:
        spans = _parse_text_spans(line_str, color_hex, accent_hex)
        line_w = 0
        span_data = []
        for span_text, span_col in spans:
            bbox = font.getbbox(span_text)
            sw = bbox[2] - bbox[0] if bbox else 0
            span_data.append((span_text, span_col, sw))
            line_w += sw
        line_layouts.append((line_w, span_data))
        total_w = max(total_w, line_w)

    total_h = max(len(lines) * line_h, font_size)
    pad = max(stroke_w + shadow_dy + 12, 10)

    img_w = max(int(total_w + pad * 2), 24)
    img_h = max(int(total_h + pad * 2), 24)

    txt_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_img)

    # Nền chữ (bg_mode: 'none' | 'block')
    bg_mode = style.get("bg_mode", "none")
    if bg_mode in ("block", "pill"):
        bg_color_hex = style.get("bg_color") or "#000000B3"
        c_bg = parse_hex_color(bg_color_hex)
        bg_radius = int(round(float(style.get("bg_radius", 0.01)) * max_w))
        if bg_mode == "pill":
            bg_radius = img_h // 2
        draw.rounded_rectangle([2, 2, img_w - 3, img_h - 3], radius=bg_radius, fill=c_bg)

    cur_y = pad
    for line_w, span_data in line_layouts:
        if align == "center":
            start_x = pad + (total_w - line_w) // 2
        elif align == "right":
            start_x = pad + (total_w - line_w)
        else:
            start_x = pad

        cur_x = start_x
        for span_text, span_col, sw in span_data:
            c_text = parse_hex_color(span_col)

            # Vẽ bóng đổ
            if c_shadow and shadow_dy > 0:
                draw.text(
                    (cur_x, cur_y + shadow_dy),
                    span_text,
                    font=font,
                    fill=c_shadow,
                )

            # Vẽ viền
            if c_stroke and stroke_w > 0:
                draw.text(
                    (cur_x, cur_y),
                    span_text,
                    font=font,
                    fill=c_text,
                    stroke_width=stroke_w,
                    stroke_fill=c_stroke,
                )
            else:
                draw.text(
                    (cur_x, cur_y),
                    span_text,
                    font=font,
                    fill=c_text,
                )

            cur_x += sw
        cur_y += line_h

    # Độ mờ opacity của đối tượng chữ
    opacity = float(style.get("opacity", 1.0))
    if opacity < 1.0:
        alpha = txt_img.split()[3]
        alpha = alpha.point(lambda p: int(p * max(0.0, min(1.0, opacity))))
        txt_img.putalpha(alpha)

    return txt_img


def render_group_object(
    obj: Dict[str, Any],
    layout: CanvasLayout,
    ctx: Optional[Dict[str, Any]] = None,
) -> Tuple[Image.Image, int, int]:
    """
    Kết xuất nhóm đối tượng (gồm pill nền nếu có + các đối tượng con image và text).
    Trả về (group_img, center_x_px, center_y_px).
    """
    out_w, out_h = layout.out_w, layout.out_h
    gx = float(obj.get("x", 0.5)) * out_w
    gy = float(obj.get("y", 0.5)) * out_h
    rot = float(obj.get("rotation", 0))

    children = obj.get("children", [])
    rendered_children = []

    # Cấu hình Pill (FIX v1.6.0 FIX-4: none | translucent | solid)
    pill_cfg = obj.get("pill", {})
    has_pill = False
    pill_mode = "translucent"  # Logo mới mặc định ở chế độ Trong mờ
    pill_color = None
    pill_opacity = 0.50

    bkit = load_brand_kit()
    brand_colors = bkit.get("colors", {})

    default_stroke_col = "#FFFFFF"
    default_stroke_alpha = int(round(0.25 * 255))

    if isinstance(pill_cfg, dict):
        mode = pill_cfg.get("mode")
        if mode in ("none", "translucent", "solid"):
            pill_mode = mode
            has_pill = mode != "none"
        else:
            has_pill = bool(pill_cfg.get("enabled", True))
            pill_mode = "translucent" if has_pill else "none"

        translucent_cfg = pill_cfg.get("translucent", {})
        solid_cfg = pill_cfg.get("solid", {})

        if pill_mode == "translucent":
            # Mặc định của Trong mờ giống bản <= v1.4: nền #000000 độ đậm 50%, viền #FFFFFF độ đậm 25%.
            # Chế độ này KHÔNG dùng màu thương hiệu.
            raw_op = translucent_cfg.get("opacity") if isinstance(translucent_cfg, dict) else None
            if raw_op is None and pill_cfg.get("mode") == "translucent":
                raw_op = pill_cfg.get("opacity")
            if raw_op is not None:
                pill_opacity = float(raw_op) / 100.0 if float(raw_op) > 1.0 else float(raw_op)
            else:
                pill_opacity = 0.50
            pill_color = "#000000"
            default_stroke_col = "#FFFFFF"
            default_stroke_alpha = int(round(0.25 * 255))
        elif pill_mode == "solid":
            raw_op = solid_cfg.get("opacity") if isinstance(solid_cfg, dict) else None
            if raw_op is None and pill_cfg.get("mode") == "solid":
                raw_op = pill_cfg.get("opacity")
            if raw_op is not None:
                pill_opacity = float(raw_op) / 100.0 if float(raw_op) > 1.0 else float(raw_op)
            else:
                pill_opacity = 1.0

            pill_color = solid_cfg.get("color") if isinstance(solid_cfg, dict) else None
            if not pill_color and pill_cfg.get("mode") == "solid":
                pill_color = pill_cfg.get("color")
            if not pill_color:
                pill_color = brand_colors.get("primary", "#1A56DB")
            default_stroke_col = brand_colors.get("pill_stroke", "#334155")
            default_stroke_alpha = int(round(max(0.0, min(1.0, pill_opacity)) * 255))
        else:
            has_pill = False
    elif isinstance(pill_cfg, bool):
        has_pill = pill_cfg
        pill_mode = "translucent" if has_pill else "none"
        pill_opacity = 0.50
        pill_color = "#000000"
        default_stroke_col = "#FFFFFF"
        default_stroke_alpha = int(round(0.25 * 255))
    else:
        has_pill = True
        pill_mode = "translucent"
        pill_opacity = 0.50
        pill_color = "#000000"
        default_stroke_col = "#FFFFFF"
        default_stroke_alpha = int(round(0.25 * 255))

    for child in children:
        if not child.get("visible", True):
            continue
        c_type = child.get("type")
        dx = float(child.get("dx", 0)) * out_w
        dy = float(child.get("dy", 0)) * out_h

        if c_type == "image":
            img = _resolve_image_source(child.get("src", ""), ctx)
            if img:
                w_ratio = float(child.get("w", 0.08))
                cw = max(int(round(w_ratio * out_w)), 16)
                scale = cw / float(img.width)
                ch = max(int(round(img.height * scale)), 16)
                resized = img.resize((cw, ch), Image.Resampling.LANCZOS)
                rendered_children.append((resized, dx, dy, cw, ch))
        elif c_type == "text":
            c_style = dict(child.get("style", {}))
            c_text = child.get("text", "")
            if c_text:
                # Tự động tương phản chữ logo khi nền màu sáng (WCAG >= 3:1)
                if has_pill and (pill_mode == "solid" or pill_opacity >= 0.7):
                    from core.colors import contrast_ratio
                    current_txt_col = c_style.get("color", "#FFFFFF")
                    if isinstance(current_txt_col, str) and current_txt_col.startswith("$"):
                        current_txt_col = brand_colors.get(current_txt_col[1:], "#FFFFFF")
                    eff_bg = pill_color
                    if contrast_ratio(current_txt_col, eff_bg) < 3.0:
                        ratio_dark = contrast_ratio("#111111", eff_bg)
                        ratio_light = contrast_ratio("#FFFFFF", eff_bg)
                        c_style["color"] = "#111111" if ratio_dark >= ratio_light else "#FFFFFF"
                txt_img = render_text_to_image(c_text, c_style, max_w=out_w)
                rendered_children.append((txt_img, dx, dy, txt_img.width, txt_img.height))

    if not rendered_children:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), int(round(gx)), int(round(gy))

    # Tính bounding box bao quanh các con
    min_x = min(dx - w / 2 for _, dx, dy, w, h in rendered_children)
    max_x = max(dx + w / 2 for _, dx, dy, w, h in rendered_children)
    min_y = min(dy - h / 2 for _, dx, dy, w, h in rendered_children)
    max_y = max(dy + h / 2 for _, dx, dy, w, h in rendered_children)

    pad_x = 24
    pad_y = 16

    box_w = int(round(max_x - min_x + pad_x * 2))
    box_h = int(round(max_y - min_y + pad_y * 2))
    center_offset_x = (min_x + max_x) / 2
    center_offset_y = (min_y + max_y) / 2

    group_canvas = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(group_canvas)

    if has_pill:
        alpha_val = int(round(max(0.0, min(1.0, pill_opacity)) * 255))
        c_fill_raw = parse_hex_color(pill_color)
        c_fill = (c_fill_raw[0], c_fill_raw[1], c_fill_raw[2], alpha_val)

        stroke_cfg = pill_cfg.get("stroke") if isinstance(pill_cfg, dict) else None
        has_stroke = True
        stroke_col_hex = default_stroke_col
        stroke_alpha = default_stroke_alpha
        if isinstance(stroke_cfg, dict):
            has_stroke = bool(stroke_cfg.get("enabled", True))
            if "color" in stroke_cfg:
                stroke_col_hex = stroke_cfg["color"]
            if "alpha" in stroke_cfg:
                stroke_alpha = int(round(float(stroke_cfg["alpha"])))
        elif isinstance(stroke_cfg, bool):
            has_stroke = stroke_cfg

        c_stroke_raw = parse_hex_color(stroke_col_hex)
        c_stroke = (c_stroke_raw[0], c_stroke_raw[1], c_stroke_raw[2], stroke_alpha)

        stroke_w = max(int(round(0.003 * out_w)), 1) if has_stroke else 0

        radius_cfg = pill_cfg.get("radius", "full") if isinstance(pill_cfg, dict) else "full"
        if radius_cfg == "full" or not isinstance(radius_cfg, (int, float)):
            radius = box_h // 2
        else:
            radius = int(round(float(radius_cfg)))

        draw.rounded_rectangle(
            [stroke_w, stroke_w, box_w - stroke_w - 1, box_h - stroke_w - 1],
            radius=radius,
            fill=c_fill,
            outline=c_stroke if has_stroke else None,
            width=stroke_w,
        )

    # Dán từng phần tử con vào group canvas
    half_bw = box_w / 2.0
    half_bh = box_h / 2.0
    for c_img, dx, dy, cw, ch in rendered_children:
        target_x = int(round(half_bw + (dx - center_offset_x) - cw / 2.0))
        target_y = int(round(half_bh + (dy - center_offset_y) - ch / 2.0))
        group_canvas.paste(c_img, (target_x, target_y), c_img)

    # Xoay nhóm nếu có
    if abs(rot) > 0.01:
        rotated = group_canvas.rotate(-rot, expand=True, resample=Image.Resampling.BICUBIC)
    else:
        rotated = group_canvas

    return rotated, int(round(gx + center_offset_x)), int(round(gy + center_offset_y))


def render_objects(
    overlay: Image.Image,
    objects: List[Dict[str, Any]],
    layout: CanvasLayout,
    ctx: Dict[str, Any],
    warnings: Optional[List[str]] = None,
) -> Image.Image:
    """
    Vẽ toàn bộ danh sách đối tượng trong scene lên overlay RGBA, sắp xếp theo z-index.
    """
    if not objects:
        return overlay

    sorted_objects = sorted(objects, key=lambda o: float(o.get("z", 10)))
    out_w, out_h = layout.out_w, layout.out_h

    for obj in sorted_objects:
        if not obj.get("visible", True):
            continue

        obj_type = obj.get("type")
        rot = float(obj.get("rotation", 0))

        if obj_type == "group":
            group_img, cx, cy = render_group_object(obj, layout, ctx)
            paste_x = cx - group_img.width // 2
            paste_y = cy - group_img.height // 2
            overlay.paste(group_img, (paste_x, paste_y), group_img)

        elif obj_type == "text":
            text_str = obj.get("text", "")
            if not text_str:
                continue
            style = obj.get("style", {})
            txt_img = render_text_to_image(text_str, style, max_w=out_w)
            if abs(rot) > 0.01:
                txt_img = txt_img.rotate(-rot, expand=True, resample=Image.Resampling.BICUBIC)
            cx = int(round(float(obj.get("x", 0.5)) * out_w))
            cy = int(round(float(obj.get("y", 0.5)) * out_h))
            paste_x = cx - txt_img.width // 2
            paste_y = cy - txt_img.height // 2
            overlay.paste(txt_img, (paste_x, paste_y), txt_img)

        elif obj_type == "image":
            img = _resolve_image_source(obj.get("src", ""), ctx)
            if not img:
                continue
            w_ratio = float(obj.get("w", 0.2))
            cw = max(int(round(w_ratio * out_w)), 16)
            scale = cw / float(img.width)
            ch = max(int(round(img.height * scale)), 16)
            resized = img.resize((cw, ch), Image.Resampling.LANCZOS)
            opacity = float(obj.get("opacity", 1.0))
            if opacity < 1.0:
                alpha = resized.split()[3]
                alpha = alpha.point(lambda p: int(p * max(0.0, min(1.0, opacity))))
                resized.putalpha(alpha)
            if abs(rot) > 0.01:
                resized = resized.rotate(-rot, expand=True, resample=Image.Resampling.BICUBIC)
            cx = int(round(float(obj.get("x", 0.5)) * out_w))
            cy = int(round(float(obj.get("y", 0.5)) * out_h))
            paste_x = cx - resized.width // 2
            paste_y = cy - resized.height // 2
            overlay.paste(resized, (paste_x, paste_y), resized)

    return overlay


def render_single_object_image(
    obj: Dict[str, Any],
    max_edge: int = 1024,
    ctx: Optional[Dict[str, Any]] = None,
) -> Tuple[Image.Image, str]:
    """
    Kết xuất một đối tượng duy nhất thành ảnh PNG RGBA không viền/nền thừa (phục vụ POST /api/object-image).
    Trả về (image, content_hash).
    """
    # Tính hash JSON để cache
    obj_clean = copy.deepcopy(obj)
    # Loại bỏ các thuộc tính toạ độ tuyệt đối màn hình nếu có để tái sử dụng cache khi chỉ kéo di chuyển
    obj_clean.pop("x", None)
    obj_clean.pop("y", None)
    hash_str = hashlib.sha256(json.dumps(obj_clean, sort_keys=True).encode("utf-8")).hexdigest()

    obj_type = obj.get("type", "group")
    # Giả định khung 1080x1920 để tính tỉ lệ chữ và kích thước
    layout = CanvasLayout(
        out_w=1080,
        out_h=1920,
        video_w=1080,
        video_h=1920,
        video_target_w=1080,
        video_target_h=1920,
        video_x=0,
        video_y=0,
        is_custom=False,
        fill_mode="source",
        fill_color="#000000",
        unit=1080,
    )

    if obj_type == "group":
        rendered, _, _ = render_group_object(obj, layout, ctx)
    elif obj_type == "text":
        rendered = render_text_to_image(obj.get("text", ""), obj.get("style", {}), max_w=1080)
    elif obj_type == "image":
        img = _resolve_image_source(obj.get("src", ""), ctx)
        if img:
            w_ratio = float(obj.get("w", 0.2))
            cw = max(int(round(w_ratio * 1080)), 16)
            scale = cw / float(img.width)
            ch = max(int(round(img.height * scale)), 16)
            rendered = img.resize((cw, ch), Image.Resampling.LANCZOS)
        else:
            rendered = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    else:
        rendered = Image.new("RGBA", (32, 32), (0, 0, 0, 0))

    # Kẹp kích thước cạnh dài không quá max_edge (1024px)
    if max(rendered.width, rendered.height) > max_edge:
        scale = max_edge / float(max(rendered.width, rendered.height))
        nw = max(int(round(rendered.width * scale)), 1)
        nh = max(int(round(rendered.height * scale)), 1)
        rendered = rendered.resize((nw, nh), Image.Resampling.LANCZOS)

    return rendered, hash_str

"""
core/compositor.py - Kết hợp khung hình và lớp phủ cho Preview (Pillow) và Xuất Video (ffmpeg).
Dùng chung bố cục từ core.canvas để đảm bảo xem trước khớp 100% với video xuất.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter

from core.brand import get_default_logo_path, load_brand_kit
from core.canvas import calculate_canvas_layout
from core.frames import extract_frame_at
from core.overrides import apply_overrides
from core.auto_contrast import adjust_caption_contrast
from core.encode_profiles import get_encode_args
from core.overlay_renderer import render_overlay
from core.paths import get_ffmpeg_path, OUTPUTS_DIR, get_ffmpeg_threads
from core.video_probe import probe_video


def build_preview(
    video_path: str,
    template: Dict[str, Any],
    caption: str,
    time_sec: float = 1.0,
    logo_path: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
    exclude_layers: Optional[List[str]] = None,
    exclude_objects: bool = False,
) -> Tuple[Image.Image, List[str]]:
    """
    Tạo 1 ảnh xem trước tại thời điểm time_sec, khớp 100% với khung hình xuất của video.
    """
    if exclude_objects:
        if exclude_layers is None:
            exclude_layers = ["__objects__"]
        elif "__objects__" not in exclude_layers:
            exclude_layers = list(exclude_layers) + ["__objects__"]

    brand_data = load_brand_kit()
    effective_overrides, auto_notice = adjust_caption_contrast(template, overrides, brand_data)
    tpl = apply_overrides(template, effective_overrides)
    info = probe_video(video_path)
    # Giới hạn time_sec trong phạm vi video
    clamped_t = min(max(time_sec, 0.0), max(info.duration - 0.1, 0.0))

    layout = calculate_canvas_layout(info.width, info.height, tpl.get("canvas"))
    raw_frame = extract_frame_at(video_path, clamped_t)

    # Nếu chưa truyền logo_path, dùng logo mặc định của brand
    if not logo_path:
        default_logo = get_default_logo_path()
        if default_logo:
            logo_path = str(default_logo)

    # 1. Tạo nền canvas
    if layout.is_custom:
        canvas_img = Image.new("RGBA", (layout.out_w, layout.out_h), (0, 0, 0, 255))
        if layout.fill_mode == "blur":
            # Tạo nền mờ phủ kín canvas
            # Scale phủ kín
            scale = max(layout.out_w / float(raw_frame.width), layout.out_h / float(raw_frame.height))
            bg_w = int(round(raw_frame.width * scale))
            bg_h = int(round(raw_frame.height * scale))
            bg_resized = raw_frame.resize((bg_w, bg_h), Image.Resampling.BILINEAR)

            # Crop chính giữa
            crop_x = (bg_w - layout.out_w) // 2
            crop_y = (bg_h - layout.out_h) // 2
            bg_cropped = bg_resized.crop((crop_x, crop_y, crop_x + layout.out_w, crop_y + layout.out_h))

            # Box blur / Gaussian blur và giảm sáng nhẹ
            bg_blurred = bg_cropped.filter(ImageFilter.BoxBlur(20))
            enhancer = ImageEnhance.Brightness(bg_blurred)
            bg_final = enhancer.enhance(0.7).convert("RGBA")
            canvas_img.paste(bg_final, (0, 0))
        elif layout.fill_mode == "color":
            from core.colors import parse_hex_color
            c_fill = parse_hex_color(layout.fill_color)
            color_bg = Image.new("RGBA", (layout.out_w, layout.out_h), c_fill)
            canvas_img.paste(color_bg, (0, 0))

        # Dán video frame vào vị trí định sẵn
        v_resized = raw_frame.resize((layout.video_target_w, layout.video_target_h), Image.Resampling.BILINEAR).convert("RGBA")
        canvas_img.paste(v_resized, (layout.video_x, layout.video_y))
    else:
        # Giữ khung gốc
        if raw_frame.size != (layout.out_w, layout.out_h):
            canvas_img = raw_frame.resize((layout.out_w, layout.out_h), Image.Resampling.BILINEAR).convert("RGBA")
        else:
            canvas_img = raw_frame.convert("RGBA")

    # 2. Vẽ lớp phủ overlay
    overlay_img, warnings = render_overlay(
        tpl,
        layout,
        caption,
        logo_path=logo_path,
        exclude_layers=exclude_layers,
    )
    if auto_notice and auto_notice not in warnings:
        warnings.insert(0, auto_notice)

    # 3. Ghép alpha
    final_img = Image.alpha_composite(canvas_img, overlay_img).convert("RGB")
    return final_img, warnings


def render_video(
    video_path: str,
    template: Dict[str, Any],
    caption: str,
    output_path: Optional[str] = None,
    logo_path: Optional[str] = None,
    on_progress: Optional[Callable[[float], None]] = None,
    overrides: Optional[Dict[str, Any]] = None,
    quality: str = "balanced",
) -> Dict[str, Any]:
    """
    Xuất video MP4 bằng ffmpeg với lớp phủ PNG RGBA, theo dõi tiến độ qua pipe:1.
    """
    brand_data = load_brand_kit()
    effective_overrides, _ = adjust_caption_contrast(template, overrides, brand_data)
    tpl = apply_overrides(template, effective_overrides)
    info = probe_video(video_path)
    layout = calculate_canvas_layout(info.width, info.height, tpl.get("canvas"))

    if not logo_path:
        default_logo = get_default_logo_path()
        if default_logo:
            logo_path = str(default_logo)

    # Vẽ lớp phủ overlay PNG
    overlay_img, warnings = render_overlay(tpl, layout, caption, logo_path=logo_path)

    # Lưu overlay ra file tạm
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_overlay:
        overlay_tmp_path = tmp_overlay.name
        overlay_img.save(overlay_tmp_path, format="PNG")

    # Xác định đường dẫn file xuất
    if not output_path:
        src_stem = Path(video_path).stem
        output_path = str(OUTPUTS_DIR / f"{src_stem}_taio.mp4")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    preset = os.getenv("FFMPEG_PRESET", "veryfast").strip()
    ffmpeg_bin = get_ffmpeg_path()

    # Xây dựng video filter graph của ffmpeg
    if layout.is_custom:
        if layout.fill_mode == "blur":
            filter_complex = (
                f"[0:v]scale={layout.out_w}:{layout.out_h}:force_original_aspect_ratio=increase,"
                f"crop={layout.out_w}:{layout.out_h},boxblur=20:5,"
                f"colorchannelmixer=aa=1:rr=0.7:gg=0.7:bb=0.7[bg];"
                f"[0:v]scale={layout.video_target_w}:{layout.video_target_h}[fg];"
                f"[bg][fg]overlay={layout.video_x}:{layout.video_y}[comp];"
                f"[comp][1:v]overlay=0:0[outv]"
            )
        else:
            filter_complex = (
                f"color=c={layout.fill_color}:s={layout.out_w}x{layout.out_h}[bg];"
                f"[0:v]scale={layout.video_target_w}:{layout.video_target_h}[fg];"
                f"[bg][fg]overlay={layout.video_x}:{layout.video_y}[comp];"
                f"[comp][1:v]overlay=0:0[outv]"
            )
    else:
        if (layout.out_w, layout.out_h) != (info.width, info.height):
            filter_complex = f"[0:v]scale={layout.out_w}:{layout.out_h}[v0];[v0][1:v]overlay=0:0[outv]"
        else:
            filter_complex = "[0:v][1:v]overlay=0:0[outv]"

    threads_str = str(get_ffmpeg_threads())
    encode_args = get_encode_args(quality=quality, video_info=info, preset=preset)

    cmd = [
        ffmpeg_bin,
        "-y",
        "-nostats",
        "-loglevel", "error",
        "-threads", threads_str,
        "-i", str(video_path),
        "-i", overlay_tmp_path,
        "-filter_complex_threads", "1",
        "-filter_complex", filter_complex,
        "-threads", threads_str,
        "-map", "[outv]",
        "-map", "0:a?",
        *encode_args,
        "-c:a", "copy",
        "-progress", "pipe:1",
        str(output_path),
    ]

    try:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="ignore") as stderr_file:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=stderr_file,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            duration_us = max(info.duration * 1_000_000.0, 1.0)

            for line in proc.stdout:
                line = line.strip()
                if line.startswith("out_time_us="):
                    try:
                        val_str = line.split("=")[1].strip()
                        val_us = float(val_str)
                        prog = min(max(val_us / duration_us, 0.0), 1.0)
                        if on_progress:
                            on_progress(prog)
                    except Exception:
                        pass
                elif line.startswith("progress=end"):
                    if on_progress:
                        on_progress(1.0)

            proc.wait()

            if proc.stdout:
                proc.stdout.close()

            if proc.returncode != 0:
                stderr_file.seek(0)
                err_content = stderr_file.read()
                err_lines = [l.strip() for l in err_content.strip().splitlines() if l.strip()]
                last_err = "\n".join(err_lines[-2:]) if err_lines else "Lỗi không xác định"

                if proc.returncode in (-9, 137):
                    raise RuntimeError("ffmpeg bị hệ thống dừng (có thể do thiếu RAM)")
                else:
                    raise RuntimeError(f"ffmpeg thất bại (mã thoát {proc.returncode}): {last_err}")

    finally:
        if os.path.exists(overlay_tmp_path):
            try:
                os.remove(overlay_tmp_path)
            except Exception:
                pass

    return {
        "output": output_path,
        "width": layout.out_w,
        "height": layout.out_h,
        "warnings": warnings,
    }

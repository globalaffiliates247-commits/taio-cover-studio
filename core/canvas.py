"""
core/canvas.py - Tính toán khung hình xuất, bố cục video và kích thước đồng nhất cho preview & render.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class CanvasLayout:
    out_w: int
    out_h: int
    video_w: int
    video_h: int
    # Vị trí thực tế của video trên canvas (x, y, w, h) tính theo pixel
    video_x: int
    video_y: int
    video_target_w: int
    video_target_h: int
    is_custom: bool
    fill_mode: str  # "none", "blur", "color"
    fill_color: str
    unit: int  # min(out_w, out_h) theo đặc tả


def _round_to_even(val: float, multiple_of: int = 2) -> int:
    """Làm tròn về bội số nguyên gần nhất (mặc định số chẵn)."""
    res = int(round(val / multiple_of)) * multiple_of
    return max(res, multiple_of)


def calculate_canvas_layout(
    video_w: int,
    video_h: int,
    canvas_cfg: Any,
    output_max_res: Optional[int] = None,
) -> CanvasLayout:
    """
    Tính toán khung hình xuất, đảm bảo các quy tắc:
    - Không phóng to video quá kích thước gốc trừ khi upscale=True.
    - Chiều rộng làm tròn về bội số của 8. Chiều cao làm tròn về số chẵn (hoặc bội số 8).
    - Biến OUTPUT_MAX_RES giới hạn cạnh ngắn (min(W, H)).
    - Dùng chung cho cả preview và render để khớp tuyệt đối.
    """
    # Đọc OUTPUT_MAX_RES từ môi trường nếu không truyền trực tiếp
    if output_max_res is None:
        env_max = os.getenv("OUTPUT_MAX_RES", "").strip()
        if env_max.isdigit():
            output_max_res = int(env_max)

    # 1. Trường hợp giữ khung gốc ("source" hoặc None)
    if not canvas_cfg or canvas_cfg == "source":
        cur_w = float(video_w)
        cur_h = float(video_h)

        # Giới hạn cạnh ngắn theo OUTPUT_MAX_RES nếu cần
        short_edge = min(cur_w, cur_h)
        if output_max_res and short_edge > output_max_res:
            scale = output_max_res / short_edge
            cur_w = cur_w * scale
            cur_h = cur_h * scale

        out_w = _round_to_even(cur_w, 8)
        out_h = _round_to_even(cur_h, 2)
        unit = min(out_w, out_h)

        return CanvasLayout(
            out_w=out_w,
            out_h=out_h,
            video_w=video_w,
            video_h=video_h,
            video_x=0,
            video_y=0,
            video_target_w=out_w,
            video_target_h=out_h,
            is_custom=False,
            fill_mode="none",
            fill_color="#000000",
            unit=unit,
        )

    # 2. Trường hợp canvas tuỳ chỉnh (ví dụ 9:16)
    if isinstance(canvas_cfg, dict):
        aspect_str = canvas_cfg.get("aspect", "9:16")
        if aspect_str == "9:16":
            aspect_w, aspect_h = 9, 16
        elif ":" in aspect_str:
            parts = aspect_str.split(":")
            aspect_w, aspect_h = float(parts[0]), float(parts[1])
        else:
            aspect_w, aspect_h = 9, 16

        target_ratio = aspect_w / aspect_h
        cfg_target_w = canvas_cfg.get("width", 1080)
        upscale = canvas_cfg.get("upscale", False)

        # Tính target width/height
        # Nếu không cho phép upscale: cạnh ngắn không vượt quá cạnh ngắn của video gốc
        # hoặc width không vượt quá min(video_w, cfg_target_w)
        if not upscale:
            # Ví dụ: video 720x720, 9:16 -> target_w = min(720, 1080) = 720
            # video 1080x1080 -> target_w = min(1080, 1080) = 1080
            # video 1920x1080 -> min edge video là 1080 -> target_w = 1080 (hoặc nếu output_max_res)
            target_w = min(float(cfg_target_w), float(min(video_w, video_h)))
        else:
            target_w = float(cfg_target_w)

        # Giới hạn cạnh ngắn bởi output_max_res nếu có
        if output_max_res and target_w > output_max_res:
            target_w = float(output_max_res)

        target_h = target_w / target_ratio

        out_w = _round_to_even(target_w, 8)
        out_h = _round_to_even(target_h, 8)
        unit = min(out_w, out_h)

        # Tính vị trí video_area
        area_cfg = canvas_cfg.get("video_area", {"x": 0, "y": 0, "w": 1, "h": 1, "fit": "contain", "valign": "center"})
        area_x = area_cfg.get("x", 0) * out_w
        area_y = area_cfg.get("y", 0) * out_h
        area_w = area_cfg.get("w", 1) * out_w
        area_h = area_cfg.get("h", 1) * out_h
        fit = area_cfg.get("fit", "contain")
        valign = area_cfg.get("valign", "center")

        video_ratio = video_w / video_h
        area_ratio = area_w / area_h

        if fit == "cover":
            if video_ratio > area_ratio:
                # Video bè hơn area -> scale theo height
                v_target_h = area_h
                v_target_w = v_target_h * video_ratio
            else:
                v_target_w = area_w
                v_target_h = v_target_w / video_ratio
        else:  # contain
            if video_ratio > area_ratio:
                # Scale theo width
                v_target_w = area_w
                v_target_h = v_target_w / video_ratio
            else:
                v_target_h = area_h
                v_target_w = v_target_h * video_ratio

        # Căn lề ngang luôn ở giữa area
        vx = area_x + (area_w - v_target_w) / 2.0

        # Căn lề dọc
        if valign == "top":
            vy = area_y
        elif valign == "bottom":
            vy = area_y + (area_h - v_target_h)
        else:  # center
            vy = area_y + (area_h - v_target_h) / 2.0

        fill_mode = canvas_cfg.get("fill", "blur")
        fill_color = canvas_cfg.get("fill_color", "#000000")

        return CanvasLayout(
            out_w=out_w,
            out_h=out_h,
            video_w=video_w,
            video_h=video_h,
            video_x=int(round(vx)),
            video_y=int(round(vy)),
            video_target_w=int(round(v_target_w)),
            video_target_h=int(round(v_target_h)),
            is_custom=True,
            fill_mode=fill_mode,
            fill_color=fill_color,
            unit=unit,
        )

    # Fallback về source
    out_w = _round_to_even(video_w, 8)
    out_h = _round_to_even(video_h, 2)
    return CanvasLayout(
        out_w=out_w,
        out_h=out_h,
        video_w=video_w,
        video_h=video_h,
        video_x=0,
        video_y=0,
        video_target_w=out_w,
        video_target_h=out_h,
        is_custom=False,
        fill_mode="none",
        fill_color="#000000",
        unit=min(out_w, out_h),
    )

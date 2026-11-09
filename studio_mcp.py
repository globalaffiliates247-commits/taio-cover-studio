#!/usr/bin/env python3
"""
studio_mcp.py - MCP (Model Context Protocol) Server cho TAIO Cover Studio.
Cho phép các trợ lý AI (Claude, Antigravity, Cursor,...) điều khiển studio qua stdio.
"""

import io
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Đảm bảo đường dẫn gốc dự án có trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP, Image

from core.compositor import build_preview, render_video
from core.frames import extract_ai_frames
from core.templates import get_template, list_templates as core_list_templates
from core.version import get_version_info
from core.video_probe import probe_video

v_info = get_version_info()

# Khởi tạo MCP Server
mcp = FastMCP("TAIO Cover Studio")


@mcp.tool()
def list_templates() -> List[Dict[str, str]]:
    """
    Liệt kê tất cả các mẫu lớp phủ (templates) thương hiệu khả dụng kèm phiên bản.
    Trả về danh sách các đối tượng {id, name, description, version}.
    """
    tpls = core_list_templates()
    result = []
    for t in tpls:
        result.append({
            "id": str(t.get("id", "")),
            "name": str(t.get("name", "")),
            "description": str(t.get("description", "")),
            "version": v_info["label"],
        })
    return result


@mcp.tool()
def inspect_video(video_path: str, n_frames: int = 3):
    """
    Đọc thông tin kỹ thuật của video và trích xuất n khung hình (mặc định 3 ảnh).
    Giúp chính trợ lý AI quan sát nội dung và tự viết caption mà không cần API key ngoài.
    """
    if not os.path.exists(video_path):
        return [f"Lỗi: Không tìm thấy file video tại '{video_path}'"]

    try:
        info = probe_video(video_path)
    except Exception as e:
        return [f"Lỗi khi đọc video: {e}"]

    # Trích xuất khung hình
    frames = extract_ai_frames(video_path, duration=info.duration, n_frames=n_frames, max_edge=768)

    summary_text = (
        f"Thông tin video: {info.summary}\n"
        f"- Độ phân giải: {info.width}x{info.height}\n"
        f"- Thời lượng: {info.formatted_duration} ({info.duration:.2f}s)\n"
        f"- Tốc độ khung hình: {info.fps:.2f} fps\n"
        f"- Âm thanh: {'Có âm thanh' if info.has_audio else 'Không có âm thanh'}\n"
        f"- Số khung hình trích xuất đính kèm: {len(frames)}"
    )

    outputs = [summary_text]
    for fr in frames:
        buf = io.BytesIO()
        fr.save(buf, format="JPEG", quality=85)
        outputs.append(Image(data=buf.getvalue(), format="jpeg"))

    return outputs


@mcp.tool()
def suggest_captions(
    video_path: str,
    context: str = "",
    style: str = "tin_tuc",
    provider: Optional[str] = None,
    n: int = 5,
) -> Dict[str, Any]:
    """
    Gợi ý 5 caption hấp dẫn dựa trên 3 khung hình của video và ngữ cảnh người dùng.
    Phong cách (style): 'tin_tuc', 'giao_duc', 'ban_hang', 'giai_tri'.
    """
    if not os.path.exists(video_path):
        return {"error": f"Không tìm thấy file video: {video_path}"}

    try:
        from ai.suggest import get_caption_suggestions
        return get_caption_suggestions(
            video_path=video_path,
            context=context,
            style=style,
            provider=provider,
            n=n,
        )
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def preview_overlay(
    video_path: str,
    template_id: str = "lower_third_fade",
    caption: str = "",
    time_sec: float = 1.0,
    logo_path: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
):
    """
    Tạo 1 ảnh xem trước lớp phủ tại thời điểm time_sec (khớp 100% với video xuất).
    Hỗ trợ tham số overrides để tuỳ chỉnh sticker logo và kiểu chữ.
    """
    if not os.path.exists(video_path):
        return [f"Lỗi: Không tìm thấy file video: {video_path}"]

    tpl = get_template(template_id)
    if not tpl:
        return [f"Lỗi: Không tìm thấy template '{template_id}'"]

    try:
        img, warnings = build_preview(
            video_path=video_path,
            template=tpl,
            caption=caption,
            time_sec=time_sec,
            logo_path=logo_path,
            overrides=overrides,
            quality=quality,
        )

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        img_item = Image(data=buf.getvalue(), format="jpeg")

        warn_msg = f"Cảnh báo: {' | '.join(warnings)}" if warnings else "Xem trước hợp lệ, không có cảnh báo."
        return [img_item, warn_msg]
    except Exception as e:
        return [f"Lỗi tạo preview: {e}"]


@mcp.tool()
def render_overlay_video(
    video_path: str,
    template_id: str = "lower_third_fade",
    caption: str = "",
    output_path: Optional[str] = None,
    logo_path: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
    quality: str = "balanced",
) -> Dict[str, Any]:
    """
    Xuất video MP4 với lớp phủ thương hiệu và caption.
    Hỗ trợ tham số overrides để tuỳ biến sticker logo và kiểu chữ, và quality: light | balanced | high.
    """
    if not os.path.exists(video_path):
        return {"error": f"Không tìm thấy file video: {video_path}"}

    tpl = get_template(template_id)
    if not tpl:
        return {"error": f"Không tìm thấy template '{template_id}'"}

    if not output_path:
        p = Path(video_path)
        output_path = str(p.parent / f"{p.stem}_taio.mp4")

    try:
        res = render_video(
            video_path=video_path,
            template=tpl,
            caption=caption,
            output_path=output_path,
            logo_path=logo_path,
            overrides=overrides,
            quality=quality,
        )
        return {
            "output": res["output"],
            "width": res["width"],
            "height": res["height"],
            "warnings": res.get("warnings", []),
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()

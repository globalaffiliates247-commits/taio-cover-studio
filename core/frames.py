"""
core/frames.py - Trích xuất khung hình từ video phục vụ preview và AI.
"""

import io
import os
import subprocess
from typing import List, Optional
from PIL import Image
from core.paths import get_ffmpeg_path


def extract_frame_at(
    video_path: str,
    time_sec: float,
    max_edge: Optional[int] = None,
) -> Image.Image:
    """
    Trích xuất 1 khung hình tại thời điểm time_sec bằng ffmpeg và trả về ảnh PIL Image (RGB).
    """
    ffmpeg_bin = get_ffmpeg_path()
    scale_filter = []
    if max_edge and max_edge > 0:
        # Thu cạnh dài về max_edge, giữ tỷ lệ
        scale_filter = ["-vf", f"scale='if(gt(iw,ih),{max_edge},-2)':'if(gt(iw,ih),-2,{max_edge})'"]

    cmd = [
        ffmpeg_bin,
        "-threads", "1",
        "-ss", f"{time_sec:.3f}",
        "-i", str(video_path),
        *scale_filter,
        "-vframes", "1",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "pipe:1"
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or not res.stdout:
        raise ValueError(f"Không thể trích xuất khung hình tại giây {time_sec:.2f}: {res.stderr.decode('utf-8', errors='ignore')}")

    img = Image.open(io.BytesIO(res.stdout)).convert("RGB")
    return img


def extract_ai_frames(
    video_path: str,
    duration: float,
    n_frames: int = 3,
    max_edge: int = 768,
) -> List[Image.Image]:
    """
    Trích xuất n_frames rải đều (bỏ 5% đầu và cuối), thu về cạnh dài max_edge (mặc định 768px) theo đặc tả F7.
    """
    if duration <= 1.0:
        timestamps = [duration / 2.0]
    else:
        start_t = 0.05 * duration
        end_t = 0.95 * duration
        if n_frames <= 1:
            timestamps = [(start_t + end_t) / 2.0]
        else:
            step = (end_t - start_t) / float(n_frames + 1)
            timestamps = [start_t + step * (i + 1) for i in range(n_frames)]

    frames: List[Image.Image] = []
    for t in timestamps:
        try:
            fr = extract_frame_at(video_path, t, max_edge=max_edge)
            frames.append(fr)
        except Exception as e:
            print(f"Cảnh báo: Lỗi trích khung hình tại t={t:.2f}: {e}")

    return frames

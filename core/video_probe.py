"""
core/video_probe.py - Đọc thông tin chi tiết của video bằng ffprobe.
"""

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Optional
from core.paths import get_ffprobe_path


@dataclass
class VideoInfo:
    width: int
    height: int
    duration: float
    fps: float
    has_audio: bool
    rotation: int
    codec: str
    bit_rate: int = 0
    audio_bit_rate: int = 0

    @property
    def formatted_duration(self) -> str:
        """Định dạng thời lượng mm:ss hoặc hh:mm:ss."""
        total_sec = int(round(self.duration))
        hrs = total_sec // 3600
        mins = (total_sec % 3600) // 60
        secs = total_sec % 60
        if hrs > 0:
            return f"{hrs}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"

    @property
    def summary(self) -> str:
        """Chuỗi tóm tắt hiển thị trên giao diện theo đặc tả."""
        audio_str = "có âm thanh" if self.has_audio else "không có âm thanh"
        fps_str = f"{self.fps:.2f}".rstrip("0").rstrip(".")
        return f"{self.width}×{self.height} · {self.formatted_duration} · {fps_str} fps · {audio_str}"


def probe_video(video_path: str) -> VideoInfo:
    """
    Phân tích file video bằng ffprobe.
    Ném ngoại lệ ValueError bằng tiếng Việt nếu không phải file video hoặc không đọc được.
    """
    if not os.path.exists(video_path):
        raise ValueError(f"Không tìm thấy file video: {video_path}")

    ffprobe_bin = get_ffprobe_path()
    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-show_entries", "stream:format",
        "-of", "json",
        str(video_path)
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
    except FileNotFoundError:
        raise ValueError("Chưa cài đặt ffprobe hoặc không tìm thấy lệnh ffprobe trong PATH.")
    except subprocess.TimeoutExpired:
        raise ValueError("Quá thời gian khi đọc thông tin video.")

    if res.returncode != 0:
        raise ValueError("File tải lên không phải là định dạng video hợp lệ hoặc file bị lỗi.")

    try:
        data = json.loads(res.stdout)
    except Exception:
        raise ValueError("Không thể phân tích dữ liệu từ ffprobe.")

    streams = data.get("streams", [])
    format_info = data.get("format", {})

    video_stream = None
    audio_stream = None

    for s in streams:
        c_type = s.get("codec_type")
        if c_type == "video" and video_stream is None:
            video_stream = s
        elif c_type == "audio" and audio_stream is None:
            audio_stream = s

    if not video_stream:
        raise ValueError("File này không chứa luồng hình ảnh (video) nào.")

    # Đọc chiều rộng, chiều cao
    raw_w = int(video_stream.get("width", 0))
    raw_h = int(video_stream.get("height", 0))
    if raw_w <= 0 or raw_h <= 0:
        raise ValueError("Kích thước video không hợp lệ.")

    # Đọc góc xoay (rotation) từ tags hoặc side_data
    rotation = 0
    tags = video_stream.get("tags", {})
    if "rotate" in tags:
        try:
            rotation = int(tags["rotate"])
        except Exception:
            pass

    side_data_list = video_stream.get("side_data_list", [])
    for sd in side_data_list:
        if "rotation" in sd:
            try:
                rotation = int(sd["rotation"])
            except Exception:
                pass

    # Nếu xoay dọc 90 hoặc 270 (hoặc -90, -270) -> hoán đổi rộng và cao
    norm_rot = abs(rotation) % 360
    if norm_rot in (90, 270):
        width, height = raw_h, raw_w
    else:
        width, height = raw_w, raw_h

    # Thời lượng (duration)
    duration = 0.0
    if "duration" in video_stream:
        try:
            duration = float(video_stream["duration"])
        except Exception:
            pass
    if duration <= 0 and "duration" in format_info:
        try:
            duration = float(format_info["duration"])
        except Exception:
            pass

    # FPS
    fps = 30.0
    r_frame_rate = video_stream.get("r_frame_rate", "")
    if "/" in r_frame_rate:
        num, den = r_frame_rate.split("/")
        try:
            den_f = float(den)
            if den_f > 0:
                fps = float(num) / den_f
        except Exception:
            pass
    elif "avg_frame_rate" in video_stream and "/" in video_stream["avg_frame_rate"]:
        num, den = video_stream["avg_frame_rate"].split("/")
        try:
            den_f = float(den)
            if den_f > 0:
                fps = float(num) / den_f
        except Exception:
            pass

    codec = video_stream.get("codec_name", "h264")
    has_audio = audio_stream is not None

    # Bitrate (bps) của luồng video và âm thanh
    bit_rate = 0
    if "bit_rate" in video_stream:
        try:
            bit_rate = int(video_stream["bit_rate"])
        except Exception:
            pass

    audio_bit_rate = 0
    if audio_stream and "bit_rate" in audio_stream:
        try:
            audio_bit_rate = int(audio_stream["bit_rate"])
        except Exception:
            pass

    # Nếu luồng video không ghi bit_rate, lấy từ format.bit_rate trừ audio
    if bit_rate <= 0 and "bit_rate" in format_info:
        try:
            fmt_br = int(format_info["bit_rate"])
            if audio_bit_rate > 0:
                bit_rate = max(0, fmt_br - audio_bit_rate)
            else:
                bit_rate = int(fmt_br * 0.88)
        except Exception:
            pass

    return VideoInfo(
        width=width,
        height=height,
        duration=duration,
        fps=fps,
        has_audio=has_audio,
        rotation=rotation,
        codec=codec,
        bit_rate=bit_rate,
        audio_bit_rate=audio_bit_rate,
    )

"""
core/encode_profiles.py - Định nghĩa và quản lý các hồ sơ mã hoá video (v1.5.0).
Bao gồm:
- 3 mức nén: Nhẹ (light), Cân bằng (balanced), Chất lượng cao (high).
- Tính toán bitrate sàn và giới hạn -maxrate / -bufsize theo bitrate gốc.
- Ước tính dung lượng đầu ra ngay trên máy chủ và trình duyệt.
"""

from typing import Any, Dict, List, Optional
from core.video_probe import VideoInfo

# Sàn bitrate video tối thiểu (bps) để tránh vỡ hình ở các cảnh chuyển động
FLOOR_BITRATE_720P = 600_000     # 600 kbps cho 720p trở xuống
FLOOR_BITRATE_1080P = 1_200_000  # 1200 kbps cho 1080p trở lên

# Hồ sơ cấu hình CRF và hệ số nhân bitrate gốc
ENCODE_PROFILES: Dict[str, Dict[str, Any]] = {
    "light": {
        "id": "light",
        "name": "Nhẹ",
        "description": "Gửi Telegram, Zalo, xem nhanh",
        "crf": 26,
        "multiplier": 1.0,
    },
    "balanced": {
        "id": "balanced",
        "name": "Cân bằng",
        "description": "Đăng TikTok, Reels, Facebook",
        "crf": 23,
        "multiplier": 1.5,
    },
    "high": {
        "id": "high",
        "name": "Chất lượng cao",
        "description": "Lưu trữ, đăng YouTube",
        "crf": 20,
        "multiplier": 3.0,
    },
}


def get_floor_bitrate(width: int, height: int) -> int:
    """Xác định mức sàn bitrate tối thiểu dựa trên độ phân giải video."""
    min_dim = min(width, height) if width > 0 and height > 0 else 720
    if min_dim <= 720:
        return FLOOR_BITRATE_720P
    return FLOOR_BITRATE_1080P


def get_encode_args(
    quality: str = "balanced",
    video_info: Optional[VideoInfo] = None,
    preset: str = "veryfast",
) -> List[str]:
    """
    Sinh các đối số mã hoá ffmpeg cho luồng video dựa trên hồ sơ chất lượng.
    Giữ -preset veryfast cho cả 3 mức.
    """
    profile = ENCODE_PROFILES.get(quality, ENCODE_PROFILES["balanced"])
    crf = profile["crf"]
    multiplier = profile["multiplier"]

    args = [
        "-c:v", "libx264",
        "-x264-params", "rc-lookahead=10",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]

    # Nếu có thông tin bitrate nguồn thì áp dụng -maxrate và -bufsize (2×)
    if video_info and video_info.bit_rate > 0:
        floor_br = get_floor_bitrate(video_info.width, video_info.height)
        max_rate_bps = max(int(video_info.bit_rate * multiplier), floor_br)
        max_rate_k = max(1, max_rate_bps // 1000)
        buf_size_k = max_rate_k * 2

        args.extend([
            "-maxrate", f"{max_rate_k}k",
            "-bufsize", f"{buf_size_k}k",
        ])

    return args


def estimate_file_size(
    quality: str = "balanced",
    duration: float = 0.0,
    video_info: Optional[VideoInfo] = None,
) -> int:
    """
    Ước tính dung lượng file kết quả (bytes).
    Dung lượng = (bitrate video dự kiến + bitrate âm thanh) × thời lượng (giây) / 8.
    """
    if duration <= 0:
        duration = video_info.duration if video_info else 0.0
    if duration <= 0:
        return 0

    profile = ENCODE_PROFILES.get(quality, ENCODE_PROFILES["balanced"])
    multiplier = profile["multiplier"]

    # Ước tính bitrate video
    if video_info and video_info.bit_rate > 0:
        floor_br = get_floor_bitrate(video_info.width, video_info.height)
        est_video_br = max(int(video_info.bit_rate * multiplier), floor_br)
    else:
        # Giả định mặc định theo CRF
        crf = profile["crf"]
        if crf <= 20:
            est_video_br = 2_000_000
        elif crf <= 23:
            est_video_br = 1_200_000
        else:
            est_video_br = 700_000

    audio_br = video_info.audio_bit_rate if video_info and video_info.audio_bit_rate > 0 else 128_000
    if video_info and not video_info.has_audio:
        audio_br = 0

    total_bitrate = est_video_br + audio_br
    return int((total_bitrate * duration) / 8)

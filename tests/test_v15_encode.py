"""
tests/test_v15_encode.py - Kiểm thử 3 mức nén video: Nhẹ, Cân bằng, Chất lượng cao (v1.5 P2).
"""

import unittest
from core.encode_profiles import (
    ENCODE_PROFILES,
    FLOOR_BITRATE_720P,
    FLOOR_BITRATE_1080P,
    get_floor_bitrate,
    get_encode_args,
    estimate_file_size,
)
from core.video_probe import VideoInfo


class TestV15EncodeProfiles(unittest.TestCase):
    """Kiểm tra logic tính toán tham số ffmpeg theo 3 mức nén."""

    def test_profile_definitions(self):
        """Kiểm tra định nghĩa 3 mức nén: light (CRF 26), balanced (CRF 23), high (CRF 20)."""
        self.assertIn("light", ENCODE_PROFILES)
        self.assertIn("balanced", ENCODE_PROFILES)
        self.assertIn("high", ENCODE_PROFILES)

        self.assertEqual(ENCODE_PROFILES["light"]["crf"], 26)
        self.assertEqual(ENCODE_PROFILES["balanced"]["crf"], 23)
        self.assertEqual(ENCODE_PROFILES["high"]["crf"], 20)

    def test_floor_bitrate_resolution(self):
        """Kiểm tra sàn bitrate theo độ phân giải."""
        # 720p hoặc nhỏ hơn -> 600 kbps
        self.assertEqual(get_floor_bitrate(720, 1280), FLOOR_BITRATE_720P)
        self.assertEqual(get_floor_bitrate(480, 854), FLOOR_BITRATE_720P)
        # 1080p -> 1200 kbps
        self.assertEqual(get_floor_bitrate(1080, 1920), FLOOR_BITRATE_1080P)

    def test_encode_args_with_low_bitrate_source(self):
        """Kiểm tra video nguồn bitrate thấp (0.4 Mbps) trên 720p bị chặn bởi mức sàn."""
        info = VideoInfo(
            width=720,
            height=1280,
            duration=30.0,
            fps=30.0,
            has_audio=True,
            rotation=0,
            codec="h264",
            bit_rate=400_000,       # 400 kbps
            audio_bit_rate=64_000,
        )

        # Mức Nhẹ (1.0 × 400k = 400k < sàn 600k -> chọn sàn 600k)
        args_light = get_encode_args("light", video_info=info)
        self.assertIn("-crf", args_light)
        self.assertEqual(args_light[args_light.index("-crf") + 1], "26")
        self.assertIn("-maxrate", args_light)
        self.assertEqual(args_light[args_light.index("-maxrate") + 1], "600k")
        self.assertEqual(args_light[args_light.index("-bufsize") + 1], "1200k")

        # Mức Cân bằng (1.5 × 400k = 600k -> chọn sàn 600k)
        args_bal = get_encode_args("balanced", video_info=info)
        self.assertEqual(args_bal[args_bal.index("-crf") + 1], "23")
        self.assertEqual(args_bal[args_bal.index("-maxrate") + 1], "600k")

        # Mức Chất lượng cao (3.0 × 400k = 1200k > sàn 600k -> chọn 1200k)
        args_high = get_encode_args("high", video_info=info)
        self.assertEqual(args_high[args_high.index("-crf") + 1], "20")
        self.assertEqual(args_high[args_high.index("-maxrate") + 1], "1200k")

    def test_encode_args_without_bitrate(self):
        """Khi video nguồn không đọc được bitrate thì không áp -maxrate."""
        info = VideoInfo(
            width=720,
            height=1280,
            duration=10.0,
            fps=30.0,
            has_audio=True,
            rotation=0,
            codec="h264",
            bit_rate=0,
        )
        args = get_encode_args("balanced", video_info=info)
        self.assertIn("-crf", args)
        self.assertEqual(args[args.index("-crf") + 1], "23")
        self.assertNotIn("-maxrate", args)

    def test_estimate_file_size(self):
        """Kiểm tra hàm ước tính dung lượng file."""
        info = VideoInfo(
            width=720,
            height=1280,
            duration=60.0,          # 1 phút
            fps=30.0,
            has_audio=True,
            rotation=0,
            codec="h264",
            bit_rate=800_000,
            audio_bit_rate=128_000,
        )
        size_light = estimate_file_size("light", duration=60.0, video_info=info)
        size_bal = estimate_file_size("balanced", duration=60.0, video_info=info)
        size_high = estimate_file_size("high", duration=60.0, video_info=info)

        self.assertGreater(size_bal, size_light)
        self.assertGreater(size_high, size_bal)


if __name__ == "__main__":
    unittest.main()

"""
tests/test_stage1_core.py - Kiểm thử Giai đoạn 1: Lõi (Core), T1, T2, T4
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

# Đảm bảo đường dẫn gốc dự án có trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import BASE_DIR, get_ffmpeg_path
from core.video_probe import probe_video
from core.templates import list_templates, get_template
from core.compositor import build_preview, render_video
from core.canvas import calculate_canvas_layout


class TestStage1Core(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = BASE_DIR / "workspace" / "test_stage1"
        cls.test_dir.mkdir(parents=True, exist_ok=True)

        ffmpeg_bin = get_ffmpeg_path()

        # 1. Tạo video test 720x720 có âm thanh (dài 3 giây)
        cls.v720_path = str(cls.test_dir / "sample_720.mp4")
        if not os.path.exists(cls.v720_path):
            cmd = [
                ffmpeg_bin, "-y",
                "-f", "lavfi", "-i", "testsrc=size=720x720:rate=30",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
                "-t", "3",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                cls.v720_path,
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 2. Tạo video test 1080x1920 (dọc)
        cls.v1080_vertical = str(cls.test_dir / "sample_1080_vert.mp4")
        if not os.path.exists(cls.v1080_vertical):
            cmd = [
                ffmpeg_bin, "-y",
                "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30",
                "-t", "2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                cls.v1080_vertical,
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 3. Tạo video test 1920x1080 (ngang)
        cls.v1920_horizontal = str(cls.test_dir / "sample_1920_horiz.mp4")
        if not os.path.exists(cls.v1920_horizontal):
            cmd = [
                ffmpeg_bin, "-y",
                "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=30",
                "-t", "2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                cls.v1920_horizontal,
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def test_templates_loading(self):
        """Kiểm tra 4 templates mặc định đã sẵn sàng."""
        tpls = list_templates()
        tpl_ids = [t["id"] for t in tpls]
        expected_ids = ["footer_band", "top_bottom_bars", "lower_third_fade", "vertical_9x16_footer"]
        for eid in expected_ids:
            self.assertIn(eid, tpl_ids, f"Thiếu template {eid}")

    def test_t1_preview_all_templates(self):
        """T1: Preview cả 4 mẫu với caption có dấu và 2 cụm nhấn."""
        caption = 'Biến tướng từ hoạt động **"đi chùa online"** để kêu gọi, **trục lợi**'
        tpls = ["footer_band", "top_bottom_bars", "lower_third_fade", "vertical_9x16_footer"]

        for tid in tpls:
            tpl = get_template(tid)
            self.assertIsNotNone(tpl)
            img, warnings = build_preview(self.v720_path, tpl, caption=caption, time_sec=1.0)
            self.assertEqual(len(warnings), 0, f"Template {tid} sinh cảnh báo ngoài mong muốn: {warnings}")
            self.assertGreater(img.width, 0)
            self.assertGreater(img.height, 0)

            # Lưu ảnh preview kiểm tra
            out_preview = self.test_dir / f"preview_{tid}.jpg"
            img.save(str(out_preview), "JPEG")

    def test_t2_render_all_templates(self):
        """T2: Xuất cả 4 mẫu, giữ âm thanh và kiểm tra kích thước."""
        caption = 'Biến tướng từ hoạt động **"đi chùa online"** để kêu gọi, **trục lợi**'
        tpls = ["footer_band", "top_bottom_bars", "lower_third_fade", "vertical_9x16_footer"]

        # Test với video 720x720
        for tid in tpls:
            tpl = get_template(tid)
            out_video = str(self.test_dir / f"out_720_{tid}.mp4")
            progress_values = []

            res = render_video(
                self.v720_path,
                tpl,
                caption=caption,
                output_path=out_video,
                on_progress=lambda p: progress_values.append(p),
            )

            self.assertTrue(os.path.exists(out_video))
            probe_out = probe_video(out_video)
            self.assertTrue(probe_out.has_audio, f"{tid} bị mất audio")
            self.assertAlmostEqual(probe_out.duration, 3.0, delta=0.2)

            if tid == "vertical_9x16_footer":
                # 9:16 với gốc 720 -> 720x1280
                self.assertEqual(probe_out.width, 720)
                self.assertEqual(probe_out.height, 1280)
            else:
                # Giữ khung gốc 720x720
                self.assertEqual(probe_out.width, 720)
                self.assertEqual(probe_out.height, 720)

            self.assertGreater(len(progress_values), 0, "Không nhận được progress update")

        # 9:16 với gốc 1080 -> 1080x1920
        tpl_vert = get_template("vertical_9x16_footer")
        out_vert = str(self.test_dir / "out_1080_vert.mp4")
        res_v = render_video(self.v1080_vertical, tpl_vert, caption=caption, output_path=out_vert)
        probe_v = probe_video(out_vert)
        self.assertEqual(probe_v.width, 1080)
        self.assertEqual(probe_v.height, 1920)

    def test_t4_caption_overflow_warning(self):
        """T4: Caption 200 ký tự co tới min_size và có cảnh báo, không lỗi."""
        long_caption = "Đây là một đoạn caption thử nghiệm rất dài dài dài " * 5  # > 200 ký tự
        tpl = get_template("footer_band")
        img, warnings = build_preview(self.v720_path, tpl, caption=long_caption, time_sec=1.0)
        self.assertIn("Caption dài quá khung — nên rút gọn.", warnings)
        self.assertIsNotNone(img)


if __name__ == "__main__":
    unittest.main()

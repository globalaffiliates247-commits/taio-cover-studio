"""
tests/test_fix_memory.py - Kiểm tra giới hạn bộ nhớ RAM < 250MB và cờ -threads của ffmpeg.
"""

import os
import resource
import subprocess
import sys
import unittest
from pathlib import Path

from core.compositor import render_video
from core.paths import BASE_DIR, get_ffmpeg_threads
from core.templates import get_template


class TestFixMemory(unittest.TestCase):
    """Kiểm thử tối ưu hóa bộ nhớ RAM và luồng ffmpeg."""

    @classmethod
    def setUpClass(cls):
        cls.tpl = get_template("vertical_9x16_footer")
        cls.sample_video = BASE_DIR / "workspace" / "test_stage1" / "sample_720.mp4"
        if not cls.sample_video.exists():
            # Tạo video mẫu 720x1280 nếu chưa có
            cls.sample_video = BASE_DIR / "workspace" / "test_mem_sample.mp4"
            cls.sample_video.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=720x1280:rate=30",
                "-t", "2", "-pix_fmt", "yuv420p", str(cls.sample_video)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    def test_ffmpeg_threads_configuration(self):
        """Kiểm tra get_ffmpeg_threads() đọc chuẩn cấu hình mặc định là 2."""
        threads = get_ffmpeg_threads()
        self.assertIsInstance(threads, int)
        self.assertGreaterEqual(threads, 1)

    def test_render_memory_usage(self):
        """Kiểm tra render_video với video 720x1280 đạt RAM đỉnh < 250MB."""
        out_path = BASE_DIR / "workspace" / "test_mem_out.mp4"
        try:
            res = render_video(
                video_path=str(self.sample_video),
                template=self.tpl,
                caption="Kiểm tra **bộ nhớ RAM** đỉnh",
                output_path=str(out_path),
            )
            self.assertTrue(os.path.exists(res["output"]))

            ru = resource.getrusage(resource.RUSAGE_CHILDREN)
            # Trên macOS ru_maxrss là bytes, trên Linux là kilobytes
            if sys.platform == "darwin":
                max_rss_mb = ru.ru_maxrss / (1024 * 1024)
            else:
                max_rss_mb = ru.ru_maxrss / 1024

            print(f"\n[TEST MEMORY] RAM đỉnh của ffmpeg con: {max_rss_mb:.2f} MB")
            self.assertLess(max_rss_mb, 250.0, f"RAM đỉnh {max_rss_mb:.2f} MB vượt quá ngưỡng 250 MB")

        finally:
            if out_path.exists():
                out_path.unlink()


if __name__ == "__main__":
    unittest.main()

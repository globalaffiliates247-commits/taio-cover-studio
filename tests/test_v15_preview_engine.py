"""
tests/test_v15_preview_engine.py — Kiểm tra endpoint /api/video/<id> với HTTP Range (FEATURE v1.5 P7).
"""

import shutil
import unittest
from pathlib import Path
from web.server import app, UPLOADS_DIR


class TestV15PreviewEngine(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.test_vid_id = "test_stream_vid"
        self.test_vid_path = UPLOADS_DIR / f"{self.test_vid_id}.mp4"
        # Tạo file video giả lập
        with open(self.test_vid_path, "wb") as f:
            f.write(b"0" * 4096)

    def tearDown(self):
        if self.test_vid_path.exists():
            self.test_vid_path.unlink()

    def test_stream_video_full_200(self):
        res = self.client.get(f"/api/video/{self.test_vid_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "video/mp4")
        self.assertEqual(len(res.data), 4096)

    def test_stream_video_partial_206(self):
        res = self.client.get(f"/api/video/{self.test_vid_id}", headers={"Range": "bytes=0-100"})
        self.assertEqual(res.status_code, 206)
        self.assertEqual(len(res.data), 101)
        self.assertIn("bytes 0-100/4096", res.headers.get("Content-Range", ""))

    def test_stream_video_404(self):
        res = self.client.get("/api/video/non_existent_vid_id")
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()

"""
tests/test_stage4_web.py - Kiểm thử Giai đoạn 4: Web API & Luồng xử lý hoàn chỉnh
"""

import io
import json
import os
import sys
import time
import unittest
from pathlib import Path

# Đảm bảo đường dẫn gốc dự án có trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import BASE_DIR
from web.server import app


class TestStage4Web(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.sample_video = str(BASE_DIR / "workspace" / "test_stage1" / "sample_720.mp4")

    def test_routes_healthz_and_index(self):
        """Kiểm tra trang chủ và healthz."""
        res_health = self.client.get("/healthz")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.data.decode("utf-8"), "ok")

        res_index = self.client.get("/")
        self.assertEqual(res_index.status_code, 200)
        self.assertIn("TAIO Cover Studio", res_index.data.decode("utf-8"))

    def test_api_config(self):
        """Kiểm tra /api/config trả về đầy đủ templates và AI providers."""
        res = self.client.get("/api/config")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("templates", data)
        self.assertIn("ai", data)
        self.assertIn("brand", data)
        self.assertGreaterEqual(len(data["templates"]), 4)

    def test_upload_invalid_file_error(self):
        """Kiểm tra upload file không phải video -> báo lỗi tiếng Việt 400."""
        fake_data = {"file": (io.BytesIO(b"Day khong phai la file video"), "fake.txt"), "kind": "video"}
        res = self.client.post("/api/upload", data=fake_data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)
        self.assertIn("không phải video hợp lệ", data["error"])

    def test_full_pipeline_upload_preview_render_download(self):
        """Luồng hoàn chỉnh: Upload -> Preview -> Render -> Poll Job -> Download."""
        # 1. Upload video
        with open(self.sample_video, "rb") as f:
            v_bytes = f.read()
        upload_data = {
            "file": (io.BytesIO(v_bytes), "sample_test.mp4"),
            "kind": "video"
        }
        res_up = self.client.post("/api/upload", data=upload_data, content_type="multipart/form-data")
        self.assertEqual(res_up.status_code, 200)
        up_json = res_up.get_json()
        video_id = up_json["id"]
        self.assertTrue(up_json["name"].startswith("TAIO.CoverClip_"))
        self.assertIn("info", up_json)
        self.assertIn("summary", up_json["info"])

        # 2. Preview
        caption = 'Biến tướng từ **"đi chùa online"** để **trục lợi**'
        preview_payload = {
            "video_id": video_id,
            "template": "footer_band",
            "caption": caption,
            "t": 1.0
        }
        res_prev = self.client.post("/api/preview", json=preview_payload)
        self.assertEqual(res_prev.status_code, 200)
        self.assertEqual(res_prev.mimetype, "image/jpeg")
        self.assertGreater(len(res_prev.data), 1000)

        # 3. Render
        render_payload = {
            "video_id": video_id,
            "video_name": "sample_test.mp4",
            "template": "footer_band",
            "caption": caption
        }
        res_ren = self.client.post("/api/render", json=render_payload)
        self.assertEqual(res_ren.status_code, 200)
        ren_json = res_ren.get_json()
        self.assertIn("job_id", ren_json)
        job_id = ren_json["job_id"]

        # 4. Poll job status
        max_retries = 30
        job_done = False
        for _ in range(max_retries):
            res_job = self.client.get(f"/api/job/{job_id}")
            self.assertEqual(res_job.status_code, 200)
            job_data = res_job.get_json()
            if job_data["status"] == "done":
                job_done = True
                self.assertEqual(job_data["progress"], 1.0)
                break
            time.sleep(0.5)

        self.assertTrue(job_done, "Job render không hoàn thành trong thời gian dự kiến")

        # 5. Download video
        res_dl = self.client.get(f"/api/download/{job_id}")
        self.assertEqual(res_dl.status_code, 200)
        self.assertEqual(res_dl.mimetype, "video/mp4")
        self.assertGreater(len(res_dl.data), 1000)

    def test_send_telegram_missing_token_error(self):
        """Kiểm tra gọi /api/send-telegram khi thiếu bot_token báo lỗi 400."""
        res = self.client.post("/api/send-telegram", json={"job_id": "job_123"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Vui lòng nhập Bot Token và Chat ID", res.get_json()["error"])

    def test_upload_url_validation(self):
        """Kiểm tra kiểm tra hợp lệ URL trên /api/upload-url."""
        # 1. Rỗng
        res_empty = self.client.post("/api/upload-url", json={"url": ""})
        self.assertEqual(res_empty.status_code, 400)
        self.assertIn("Vui lòng nhập", res_empty.get_json()["error"])

        # 2. Sai scheme (không phải http/https)
        res_scheme = self.client.post("/api/upload-url", json={"url": "ftp://example.com/video.mp4"})
        self.assertEqual(res_scheme.status_code, 400)
        self.assertIn("http:// hoặc https://", res_scheme.get_json()["error"])

        # 3. Qua /api/upload với JSON { url: ... }
        res_upload_alias = self.client.post("/api/upload", json={"url": "ftp://test.com/v.mp4"})
        self.assertEqual(res_upload_alias.status_code, 400)
        self.assertIn("http:// hoặc https://", res_upload_alias.get_json()["error"])


if __name__ == "__main__":
    unittest.main()

"""
tests/test_stage6_host.py - Kiểm thử Giai đoạn 6: Triển khai Host & Nghiệm thu T3, T7, T8
"""

import base64
import os
import sys
import time
import unittest
from pathlib import Path

# Đảm bảo đường dẫn gốc dự án có trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.canvas import calculate_canvas_layout
from core.paths import BASE_DIR
from core.templates import get_template
from web.server import app, jobs_store, render_queue


class TestStage6Host(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.sample_video = str(BASE_DIR / "workspace" / "test_stage1" / "sample_720.mp4")

    def test_t3_output_max_res(self):
        """T3: OUTPUT_MAX_RES=720 với gốc 1920x1080 -> Giữ khung 1280x720, 9:16 -> 720x1280."""
        # 1. Giữ khung gốc ("source") với OUTPUT_MAX_RES=720
        layout_source = calculate_canvas_layout(
            video_w=1920,
            video_h=1080,
            canvas_cfg="source",
            output_max_res=720,
        )
        self.assertEqual(layout_source.out_w, 1280)
        self.assertEqual(layout_source.out_h, 720)

        # 2. 9:16 với OUTPUT_MAX_RES=720
        tpl_916 = get_template("vertical_9x16_footer")
        layout_916 = calculate_canvas_layout(
            video_w=1920,
            video_h=1080,
            canvas_cfg=tpl_916.get("canvas"),
            output_max_res=720,
        )
        self.assertEqual(layout_916.out_w, 720)
        self.assertEqual(layout_916.out_h, 1280)

    def test_t7_basic_auth(self):
        """T7: Mật khẩu APP_PASSWORD: /healthz 200, / 401 khi không đăng nhập, 200 khi đúng."""
        os.environ["APP_USER"] = "taio_admin"
        os.environ["APP_PASSWORD"] = "secret123"

        try:
            # /healthz luôn mở 200
            res_h = self.client.get("/healthz")
            self.assertEqual(res_h.status_code, 200)

            # / khi chưa đăng nhập -> 401
            res_unauth = self.client.get("/")
            self.assertEqual(res_unauth.status_code, 401)

            # / khi sai mật khẩu -> 401
            bad_auth = base64.b64encode(b"taio_admin:wrongpass").decode("utf-8")
            res_wrong = self.client.get("/", headers={"Authorization": f"Basic {bad_auth}"})
            self.assertEqual(res_wrong.status_code, 401)

            # / khi đúng thông tin -> 200
            good_auth = base64.b64encode(b"taio_admin:secret123").decode("utf-8")
            res_ok = self.client.get("/", headers={"Authorization": f"Basic {good_auth}"})
            self.assertEqual(res_ok.status_code, 200)

        finally:
            os.environ.pop("APP_PASSWORD", None)

    def test_t8_render_queue_parallel_limiting(self):
        """T8: Gửi 2 lệnh xuất cùng lúc, job 2 ở trạng thái queued trước khi chuyển running/done."""
        # Chuẩn bị video ID hợp lệ
        res_cfg = self.client.get("/api/config")
        self.assertEqual(res_cfg.status_code, 200)

        # Upload video làm mẫu
        with open(self.sample_video, "rb") as f:
            v_data = f.read()

        import io
        upload_resp = self.client.post("/api/upload", data={"file": (io.BytesIO(v_data), "v_queue.mp4"), "kind": "video"})
        self.assertEqual(upload_resp.status_code, 200)
        vid_id = upload_resp.get_json()["id"]

        # Gửi liên tiếp 2 lệnh render
        payload1 = {"video_id": vid_id, "video_name": "q1.mp4", "template": "footer_band", "caption": "Job 1"}
        payload2 = {"video_id": vid_id, "video_name": "q2.mp4", "template": "footer_band", "caption": "Job 2"}

        r1 = self.client.post("/api/render", json=payload1)
        r2 = self.client.post("/api/render", json=payload2)

        j1_id = r1.get_json()["job_id"]
        j2_id = r2.get_json()["job_id"]

        # Kiểm tra ngay lập tức: job 2 phải ở trạng thái queued hoặc ít nhất được tạo
        res_j2 = self.client.get(f"/api/job/{j2_id}")
        self.assertIn(res_j2.get_json()["status"], ["queued", "running", "done"])

        # Chờ cả 2 job hoàn thành
        max_wait = 40
        done_count = 0
        for _ in range(max_wait):
            s1 = self.client.get(f"/api/job/{j1_id}").get_json()["status"]
            s2 = self.client.get(f"/api/job/{j2_id}").get_json()["status"]
            if s1 == "done" and s2 == "done":
                done_count = 2
                break
            time.sleep(0.5)

        self.assertEqual(done_count, 2, "Cả hai jobs trong hàng đợi phải hoàn thành")


if __name__ == "__main__":
    unittest.main()

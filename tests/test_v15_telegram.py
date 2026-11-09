"""
tests/test_v15_telegram.py — Kiểm tra endpoint /api/send-telegram 1 chạm (FEATURE v1.5 P4).
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from web.server import app, _TELEGRAM_SENT_JOBS, _TELEGRAM_IP_TIMESTAMPS, jobs_store


class TestV15Telegram(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        _TELEGRAM_SENT_JOBS.clear()
        _TELEGRAM_IP_TIMESTAMPS.clear()

    def test_missing_server_config_returns_503(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
            res = self.client.post("/api/send-telegram", json={"job_id": "job_any"})
            self.assertEqual(res.status_code, 503)
            self.assertIn("chưa cấu hình bot Telegram", res.get_json()["error"])

    def test_missing_job_id_returns_400(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "mock_token", "TELEGRAM_CHAT_ID": "123456"}):
            res = self.client.post("/api/send-telegram", json={})
            self.assertEqual(res.status_code, 400)
            self.assertIn("Thiếu mã xuất video", res.get_json()["error"])

    def test_job_not_found_returns_404(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "mock_token", "TELEGRAM_CHAT_ID": "123456"}):
            res = self.client.post("/api/send-telegram", json={"job_id": "job_non_exist"})
            self.assertEqual(res.status_code, 404)
            self.assertIn("Không tìm thấy", res.get_json()["error"])

    def test_duplicate_send_protection(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "mock_token", "TELEGRAM_CHAT_ID": "123456"}):
            _TELEGRAM_SENT_JOBS.add("job_already_sent")
            res = self.client.post("/api/send-telegram", json={"job_id": "job_already_sent"})
            self.assertEqual(res.status_code, 400)
            self.assertIn("đã được gửi về TAIO.CLUB trước đó", res.get_json()["error"])

    def test_rate_limit_20_per_hour(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "mock_token", "TELEGRAM_CHAT_ID": "123456"}):
            ip = "127.0.0.1"
            import time
            now = time.time()
            _TELEGRAM_IP_TIMESTAMPS[ip] = [now - 10] * 20

            res = self.client.post("/api/send-telegram", json={"job_id": "job_rate_limited"}, environ_base={"REMOTE_ADDR": ip})
            self.assertEqual(res.status_code, 429)
            self.assertIn("quá 20 lần trong 1 giờ", res.get_json()["error"])


if __name__ == "__main__":
    unittest.main()

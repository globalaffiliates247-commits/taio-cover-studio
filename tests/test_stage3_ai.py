"""
tests/test_stage3_ai.py - Kiểm thử Giai đoạn 3: AI và Nghiệm thu T5
"""

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Đảm bảo đường dẫn gốc dự án có trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.suggest import get_caption_suggestions
from ai.settings import get_provider_config
from core.paths import BASE_DIR


class MockAIServerHandler(BaseHTTPRequestHandler):
    recorded_requests = []

    def log_message(self, format, *args):
        pass  # Tắt log stdout

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        parsed_body = json.loads(body)

        MockAIServerHandler.recorded_requests.append({
            "path": self.path,
            "headers": {k.lower(): v for k, v in self.headers.items()},
            "body": parsed_body,
        })

        if self.path == "/anthropic":
            # Phản hồi theo chuẩn Claude
            reply_text = json.dumps({
                "summary": "Video phân tích thị trường kinh doanh",
                "captions": [
                    {"text": "Bí mật **tăng trưởng 300%** không ai nói", "angle": "curiosity_gap", "why": "Gợi sự tò mò"},
                    {"text": "**3 sai lầm** khiến bạn phá sản", "angle": "stakes", "why": "Cảnh báo rủi ro"},
                    {"text": "Làm thế nào để **thu hút khách hàng**?", "angle": "question", "why": "Kích thích tương tác"}
                ]
            })
            resp = {
                "id": "msg_mock",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": reply_text}]
            }
        else:
            # Phản hồi theo chuẩn OpenAI
            reply_text = json.dumps({
                "summary": "Video chia sẻ kiến thức hữu ích",
                "captions": [
                    {"text": "Cách kiếm **100 triệu đầu tiên**", "angle": "number", "why": "Mục tiêu cụ thể"},
                    {"text": "Tại sao người giàu **càng giàu hơn**?", "angle": "contrast", "why": "Tương phản mạnh mẽ"},
                    {"text": "Đừng bỏ qua **bí kíp vàng** này", "angle": "stakes", "why": "Sợ bỏ lỡ"}
                ]
            })
            resp = {
                "id": "chatcmpl_mock",
                "object": "chat.completion",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": reply_text},
                    "finish_reason": "stop"
                }]
            }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode("utf-8"))


class TestStage3AI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Khởi động Mock Server trên cổng ngẫu nhiên khả dụng
        cls.server = HTTPServer(("127.0.0.1", 0), MockAIServerHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

        cls.sample_video = str(BASE_DIR / "workspace" / "test_stage1" / "sample_720.mp4")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        MockAIServerHandler.recorded_requests.clear()

    def test_t5_anthropic_mock(self):
        """T5.1: Kiểm tra Claude API nhận đúng 3 ảnh và trả về captions hợp lệ."""
        mock_cfg = {
            "type": "anthropic",
            "label": "Claude Mock",
            "model": "claude-mock",
            "endpoint": f"http://127.0.0.1:{self.port}/anthropic",
            "resolved_api_key": "mock-claude-key",
            "id": "mock_claude",
        }

        from ai.providers.anthropic_provider import call_anthropic
        from core.frames import extract_ai_frames

        frames = extract_ai_frames(self.sample_video, duration=3.0, n_frames=3, max_edge=768)
        self.assertEqual(len(frames), 3)

        res = call_anthropic(
            config=mock_cfg,
            frames=frames,
            system_prompt="system",
            user_prompt="user",
        )

        self.assertEqual(len(MockAIServerHandler.recorded_requests), 1)
        req = MockAIServerHandler.recorded_requests[0]
        self.assertEqual(req["path"], "/anthropic")
        self.assertEqual(req["headers"].get("x-api-key"), "mock-claude-key")

        # Kiểm tra đúng 3 ảnh dạng base64 trong payload
        content = req["body"]["messages"][0]["content"]
        images = [c for c in content if c.get("type") == "image"]
        self.assertEqual(len(images), 3)

        # Kiểm tra kết quả trả về
        self.assertEqual(len(res["captions"]), 3)
        self.assertIn("summary", res)

    def test_t5_openai_compat_mock(self):
        """T5.2: Kiểm tra OpenAI-compatible API nhận đúng 3 ảnh và trả về captions."""
        mock_cfg = {
            "type": "openai_compat",
            "label": "OpenAI Mock",
            "model": "gpt-mock",
            "endpoint": f"http://127.0.0.1:{self.port}/openai",
            "resolved_api_key": "mock-openai-key",
            "id": "mock_openai",
        }

        from ai.providers.openai_compat import call_openai_compat
        from core.frames import extract_ai_frames

        frames = extract_ai_frames(self.sample_video, duration=3.0, n_frames=3, max_edge=768)
        self.assertEqual(len(frames), 3)

        res = call_openai_compat(
            config=mock_cfg,
            frames=frames,
            system_prompt="system",
            user_prompt="user",
        )

        self.assertEqual(len(MockAIServerHandler.recorded_requests), 1)
        req = MockAIServerHandler.recorded_requests[0]
        self.assertEqual(req["path"], "/openai")
        self.assertEqual(req["headers"].get("authorization"), "Bearer mock-openai-key")

        # Kiểm tra đúng 3 ảnh trong payload
        user_content = req["body"]["messages"][1]["content"]
        images = [c for c in user_content if c.get("type") == "image_url"]
        self.assertEqual(len(images), 3)

        # Kiểm tra kết quả trả về
        self.assertEqual(len(res["captions"]), 3)
        self.assertIn("summary", res)

    def test_t5_missing_api_key_error(self):
        """T5.3: Thiếu key -> báo lỗi tiếng Việt chỉ rõ biến môi trường cần đặt."""
        # Tạm xoá biến môi trường ANTHROPIC_API_KEY nếu có
        old_val = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with self.assertRaises(ValueError) as ctx:
                get_provider_config("claude")
            err_msg = str(ctx.exception)
            self.assertIn("Chưa cấu hình API Key", err_msg)
            self.assertIn("ANTHROPIC_API_KEY", err_msg)
        finally:
            if old_val:
                os.environ["ANTHROPIC_API_KEY"] = old_val


if __name__ == "__main__":
    unittest.main()

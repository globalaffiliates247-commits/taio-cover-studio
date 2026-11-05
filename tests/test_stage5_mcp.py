"""
tests/test_stage5_mcp.py - Kiểm thử Giai đoạn 5: MCP Server & Nghiệm thu T6
"""

import asyncio
import sys
import unittest
from pathlib import Path

# Đảm bảo đường dẫn gốc dự án có trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import BASE_DIR
from studio_mcp import mcp


class TestStage5MCP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_video = str(BASE_DIR / "workspace" / "test_stage1" / "sample_720.mp4")

    def test_t6_list_5_tools(self):
        """T6.1: Liệt kê đủ 5 tools chuẩn của MCP Server."""
        async def _run():
            tools = await mcp.list_tools()
            names = [t.name for t in tools]
            expected = ["list_templates", "inspect_video", "suggest_captions", "preview_overlay", "render_overlay_video"]
            self.assertEqual(len(tools), 5)
            for exp in expected:
                self.assertIn(exp, names)

        asyncio.run(_run())

    def test_t6_inspect_video_returns_text_and_3_images(self):
        """T6.2: Gọi inspect_video trả về 1 text tóm tắt + 3 ảnh khung hình."""
        async def _run():
            res = await mcp.call_tool("inspect_video", {"video_path": self.sample_video, "n_frames": 3})
            self.assertEqual(len(res), 4)

            # 1 text đầu tiên
            self.assertEqual(res[0].type, "text")
            self.assertIn("Thông tin video", res[0].text)

            # 3 ảnh JPEG tiếp theo
            images = [item for item in res if item.type == "image"]
            self.assertEqual(len(images), 3)
            for img in images:
                self.assertEqual(img.mimeType, "image/jpeg")
                self.assertGreater(len(img.data), 100)

        asyncio.run(_run())

    def test_preview_overlay_tool(self):
        """Kiểm tra gọi preview_overlay qua MCP."""
        async def _run():
            res = await mcp.call_tool(
                "preview_overlay",
                {
                    "video_path": self.sample_video,
                    "template_id": "footer_band",
                    "caption": "Thử nghiệm **MCP Server**",
                    "time_sec": 1.0,
                },
            )
            self.assertEqual(len(res), 2)
            self.assertEqual(res[0].type, "image")
            self.assertEqual(res[1].type, "text")

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()

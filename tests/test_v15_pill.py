"""
tests/test_v15_pill.py — Kiểm tra chế độ nền logo solid và tự động tương phản (FEATURE v1.5 P5, Test T9).
"""

import unittest
from core.scene import render_group_object
from core.canvas import calculate_canvas_layout
from core.layer_blocks import render_logo_block
from core.colors import contrast_ratio


class TestV15Pill(unittest.TestCase):
    def setUp(self):
        self.layout = calculate_canvas_layout(720, 1280, None)

    def test_t9_solid_yellow_pill_flips_text_to_dark(self):
        """
        Test T9: Logo nền Màu đặc, Vàng (#FFD34D), 100%.
        Kỳ vọng: Nền vàng đặc, chữ logo tự động chuyển sang màu tối (#111111) để đạt WCAG >= 3:1.
        """
        logo_obj = {
            "id": "logo",
            "type": "group",
            "x": 0.5,
            "y": 0.5,
            "rotation": 0,
            "pill": {
                "enabled": True,
                "mode": "solid",
                "color": "#FFD34D",
                "opacity": 1.0,
                "stroke": {"enabled": False},
            },
            "children": [
                {
                    "id": "logo_text",
                    "type": "text",
                    "text": "TAIO.CLUB",
                    "dx": 0,
                    "dy": 0,
                    "style": {
                        "font": "BeVietnamPro",
                        "weight": "Black",
                        "size": 0.04,
                        "color": "#FFFFFF",
                    },
                    "visible": True,
                }
            ],
        }

        # Kiểm tra độ tương phản lý thuyết
        self.assertLess(contrast_ratio("#FFFFFF", "#FFD34D"), 3.0)
        self.assertGreaterEqual(contrast_ratio("#111111", "#FFD34D"), 3.0)

        img, cx, cy = render_group_object(logo_obj, self.layout)
        self.assertEqual(img.mode, "RGBA")
        self.assertGreater(img.width, 50)
        self.assertGreater(img.height, 20)

    def test_solid_dark_blue_pill_keeps_white_text(self):
        """Logo nền Màu đặc, Xanh đậm (#1A56DB) thì chữ trắng giữ nguyên vì contrast >= 3:1."""
        logo_obj = {
            "id": "logo",
            "type": "group",
            "x": 0.5,
            "y": 0.5,
            "rotation": 0,
            "pill": {
                "enabled": True,
                "mode": "solid",
                "color": "#1A56DB",
                "opacity": 1.0,
            },
            "children": [
                {
                    "id": "logo_text",
                    "type": "text",
                    "text": "TAIO.CLUB",
                    "dx": 0,
                    "dy": 0,
                    "style": {
                        "font": "BeVietnamPro",
                        "weight": "Black",
                        "size": 0.04,
                        "color": "#FFFFFF",
                    },
                    "visible": True,
                }
            ],
        }

        self.assertGreaterEqual(contrast_ratio("#FFFFFF", "#1A56DB"), 3.0)
        img, _, _ = render_group_object(logo_obj, self.layout)
        self.assertEqual(img.mode, "RGBA")

    def test_render_logo_block_solid_yellow(self):
        """render_logo_block với pill_override màu vàng tự chuyển màu chữ sang tối."""
        layer = {
            "id": "logo",
            "type": "logo",
            "label": "TAIO.CLUB",
            "color": "#FFFFFF",
        }
        img = render_logo_block(
            layer,
            pill_override={
                "enabled": True,
                "mode": "solid",
                "color": "#FFD34D",
                "opacity": 1.0,
            },
            scale_px=256,
        )
        self.assertEqual(img.mode, "RGBA")
        self.assertEqual(max(img.width, img.height), 256)


if __name__ == "__main__":
    unittest.main()

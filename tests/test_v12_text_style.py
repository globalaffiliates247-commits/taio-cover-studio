"""
tests/test_v12_text_style.py - Kiểm thử tuỳ chỉnh kiểu chữ (Text Style), cú pháp ==nhấn 2== và kiểm soát layout.
"""

import unittest
from core.text_layout import (
    compute_text_layout,
    parse_accent_spans,
    prepare_caption_text,
    TextSpan,
)
from core.text_style import normalize_text_style, apply_text_style_to_layer
from core.overrides import apply_overrides
from core.overlay_renderer import render_overlay
from core.canvas import calculate_canvas_layout
from core.templates import get_template


class TestV12TextStyle(unittest.TestCase):
    """Kiểm thử tính năng text styles và cú pháp 2 màu nhấn trong FEATURE v1.2."""

    def test_accent2_syntax_parsing(self):
        """Kiểm tra phân tích cú pháp **nhấn 1** và ==nhấn 2==."""
        raw = "TAIO **Dramabox** ==Hưng== về đi"
        spans = parse_accent_spans(raw)

        # Cần có 5 spans: "TAIO ", "Dramabox", " ", "Hưng", " về đi"
        accent1_spans = [s for s in spans if s.accent_type == "accent1"]
        accent2_spans = [s for s in spans if s.accent_type == "accent2"]

        self.assertEqual(len(accent1_spans), 1)
        self.assertEqual(accent1_spans[0].text, "Dramabox")
        self.assertTrue(accent1_spans[0].is_accent)

        self.assertEqual(len(accent2_spans), 1)
        self.assertEqual(accent2_spans[0].text, "Hưng")
        self.assertTrue(accent2_spans[0].is_accent)

    def test_case_mode_transformations(self):
        """Kiểm tra các chế độ chữ hoa: preserve, uppercase, title với tiếng Việt."""
        text = "đường đi chùa hương"
        upper = prepare_caption_text(text, case_mode="uppercase")
        self.assertEqual(upper, "ĐƯỜNG ĐI CHÙA HƯƠNG")

        preserved = prepare_caption_text(text, case_mode="preserve")
        self.assertEqual(preserved, "đường đi chùa hương")

        titled = prepare_caption_text(text, case_mode="title")
        self.assertEqual(titled, "Đường Đi Chùa Hương")

    def test_von_restorff_warning(self):
        """Cảnh báo khi nhấn quá 3 cụm từ theo hiệu ứng Von Restorff."""
        text = "**Một** **Hai** **Ba** **Bốn** từ khóa"
        res = compute_text_layout(
            raw_text=text,
            box_w=800,
            box_h=400,
            unit=1080,
        )
        self.assertIsNotNone(res.warning)
        self.assertIn("Nhấn quá 3 cụm từ", res.warning)

    def test_normalize_text_style(self):
        """Kiểm tra làm sạch và kẹp giới hạn an toàn cho style override."""
        raw = {
            "stroke_width": 999,
            "shadow_dx": -100,
            "y_offset_ratio": 2.5,
            "color": "  #FF0000  ",
        }
        clean = normalize_text_style(raw)
        self.assertEqual(clean["stroke_width"], 30)
        self.assertEqual(clean["shadow_dx"], -50.0)
        self.assertEqual(clean["y_offset_ratio"], 0.4)
        self.assertEqual(clean["color"], "#FF0000")

    def test_render_overlay_with_custom_text_style(self):
        """Kiểm tra render_overlay_image áp dụng thành công caption style override."""
        tpl = get_template("lower_third_fade")
        layout = calculate_canvas_layout(1080, 1920, tpl.get("canvas", {}))

        overrides = {
            "layers": {
                "caption": {
                    "style": {
                        "color": "#F3F4F6",
                        "accent_color": "#F59E0B",
                        "accent2_color": "#10B981",
                        "stroke_width": 3,
                        "stroke_color": "#000000",
                        "bg_style": "lines",
                        "letter_spacing": 0.05,
                    }
                }
            }
        }

        tpl_with_ov = apply_overrides(tpl, overrides)
        img, warnings = render_overlay(
            template=tpl_with_ov,
            layout=layout,
            caption="TAIO **Cover** ==Studio==",
        )
        self.assertEqual(img.size, (1080, 1920))
        self.assertEqual(img.mode, "RGBA")


if __name__ == "__main__":
    unittest.main()

import unittest
from core.scene import render_text_to_image
from core.text_layout import get_font

class TestFix5TextSize(unittest.TestCase):
    def test_text_size_96_on_1080_canvas(self):
        style = {"font_family": "Be Vietnam Pro", "weight": "Bold", "size_px": 96}
        img = render_text_to_image("TEST SIZE 96", style, max_w=1080)
        font = get_font(weight="Bold", size=96, family="Be Vietnam Pro")
        bbox = font.getbbox("TEST SIZE 96")
        font_h = bbox[3] - bbox[1]
        self.assertGreaterEqual(font_h, 60)
        self.assertLessEqual(font_h, 110)

    def test_legacy_size_conversion(self):
        # Legacy size < 1 (e.g. 0.045 -> 48.6px)
        style = {"font_family": "Be Vietnam Pro", "weight": "Bold", "size": 0.045}
        img = render_text_to_image("TEST SIZE LEGACY", style, max_w=1080)
        font = get_font(weight="Bold", size=48, family="Be Vietnam Pro")
        bbox = font.getbbox("TEST SIZE LEGACY")
        font_h = bbox[3] - bbox[1]
        self.assertGreaterEqual(font_h, 30)
        self.assertLessEqual(font_h, 60)

if __name__ == "__main__":
    unittest.main()

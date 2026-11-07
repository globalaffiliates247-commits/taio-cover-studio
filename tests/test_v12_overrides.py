"""
tests/test_v12_overrides.py - Kiểm tra mô hình overrides, sticker logo, toạ độ tâm và API layer-image.
"""

import io
import unittest
from PIL import Image

from core.layer_blocks import render_logo_block
from core.overrides import apply_overrides
from core.templates import get_template
from web.server import app


class TestV12Overrides(unittest.TestCase):
    """Kiểm thử tính năng overrides và sticker logo backend (P2)."""

    def setUp(self):
        self.tpl = get_template("lower_third_fade")
        self.assertIsNotNone(self.tpl)
        self.client = app.test_client()

    def test_apply_overrides_basic(self):
        """Kiểm tra apply_overrides gán đúng toạ độ tâm x, y, rotation, w, opacity."""
        overrides = {
            "layers": {
                "logo": {
                    "x": 0.85,
                    "y": 0.12,
                    "w": 0.25,
                    "rotation": 25.0,
                    "opacity": 0.8,
                    "visible": True,
                    "pill": False,
                }
            }
        }
        modified = apply_overrides(self.tpl, overrides)
        logo_layer = next(l for l in modified["layers"] if l.get("id") == "logo")
        self.assertTrue(logo_layer.get("is_sticker"))
        self.assertEqual(logo_layer.get("x"), 0.85)
        self.assertEqual(logo_layer.get("y"), 0.12)
        self.assertEqual(logo_layer.get("w"), 0.25)
        self.assertEqual(logo_layer.get("rotation"), 25.0)
        self.assertEqual(logo_layer.get("opacity"), 0.8)
        self.assertEqual(logo_layer.get("pill_enabled"), False)

    def test_render_logo_block(self):
        """Kiểm tra render_logo_block vẽ ảnh khối logo RGBA độc lập."""
        logo_layer = next(l for l in self.tpl["layers"] if l.get("id") == "logo")
        img = render_logo_block(logo_layer, scale_px=512)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.mode, "RGBA")
        self.assertGreater(img.width, 100)
        self.assertEqual(max(img.width, img.height), 512)

    def test_api_layer_image(self):
        """Kiểm tra endpoint GET /api/layer-image trả về file PNG 512px hợp lệ."""
        res = self.client.get("/api/layer-image?template=lower_third_fade&layer=logo&pill=1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "image/png")
        img = Image.open(io.BytesIO(res.data))
        self.assertEqual(img.mode, "RGBA")
        self.assertEqual(max(img.width, img.height), 512)


    def test_build_preview_with_overrides_and_exclude(self):
        """Kiểm tra build_preview chấp nhận overrides và exclude_layers."""
        from core.compositor import build_preview
        from core.paths import BASE_DIR
        sample_video = BASE_DIR / "workspace" / "test_stage1" / "sample_720.mp4"
        if not sample_video.exists():
            return

        overrides = {
            "layers": {
                "logo": {
                    "x": 0.5,
                    "y": 0.5,
                    "w": 0.3,
                    "rotation": 15.0,
                    "opacity": 0.9,
                }
            }
        }
        img, warnings = build_preview(
            video_path=str(sample_video),
            template=self.tpl,
            caption="Test **Overrides**",
            overrides=overrides,
        )
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (720, 720))

        # Test exclude logo
        img_no_logo, _ = build_preview(
            video_path=str(sample_video),
            template=self.tpl,
            caption="Test Exclude",
            exclude_layers=["logo"],
        )
        self.assertIsInstance(img_no_logo, Image.Image)


if __name__ == "__main__":
    unittest.main()

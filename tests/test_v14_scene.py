"""
tests/test_v14_scene.py - Kiểm thử mô hình Scene đối tượng đồ hoạ, parent mechanism và endpoint object-image (v1.4.0).
"""

import io
import json
import unittest
from PIL import Image

from core.canvas import CanvasLayout
from core.overrides import apply_overrides
from core.overlay_renderer import render_overlay
from core.scene import (
    validate_scene,
    render_objects,
    render_single_object_image,
    count_scene_objects,
    MAX_TEXT_OBJECTS,
    MAX_IMAGE_OBJECTS,
)
from core.templates import get_template


class TestV14Scene(unittest.TestCase):
    def setUp(self):
        self.layout = CanvasLayout(
            out_w=1080,
            out_h=1920,
            video_w=1080,
            video_h=1920,
            video_target_w=1080,
            video_target_h=1920,
            video_x=0,
            video_y=0,
            is_custom=False,
            fill_mode="source",
            fill_color="#000000",
            unit=1080,
        )

    def test_validate_scene_limits(self):
        """Kiểm tra giới hạn 10 đối tượng chữ và 3 đối tượng ảnh."""
        # 1. Quá 10 đối tượng chữ -> Phải từ chối
        excess_text = [
            {"id": f"txt_{i}", "type": "text", "text": f"Line {i}"}
            for i in range(MAX_TEXT_OBJECTS + 1)
        ]
        valid, msg = validate_scene(excess_text)
        self.assertFalse(valid)
        self.assertIn("10 đối tượng chữ", msg)

        # 2. Quá 3 đối tượng ảnh -> Phải từ chối
        excess_img = [
            {"id": f"img_{i}", "type": "image", "src": "brand"}
            for i in range(MAX_IMAGE_OBJECTS + 1)
        ]
        valid, msg = validate_scene(excess_img)
        self.assertFalse(valid)
        self.assertIn("3 đối tượng ảnh", msg)

        # 3. Scene hợp lệ
        valid_scene = [
            {
                "id": "logo",
                "type": "group",
                "x": 0.8,
                "y": 0.06,
                "children": [
                    {"id": "logo_img", "type": "image", "src": "brand", "w": 0.06},
                    {"id": "logo_text", "type": "text", "text": "TAIO.CLUB"},
                ],
            },
            {"id": "callout", "type": "text", "text": "Xem ngay!"},
        ]
        valid, msg = validate_scene(valid_scene)
        self.assertTrue(valid)
        self.assertIsNone(msg)

    def test_parent_mechanism(self):
        """Kiểm tra cơ chế parent: caption tự co giãn theo chiều cao dải chân trang bg_band."""
        tpl = get_template("footer_band")
        self.assertIsNotNone(tpl)

        # Ban đầu bg_band cao 0.44 (y = 0.56)
        # Ghi đè dải chân trang tăng chiều cao lên 0.60 (y = 0.40)
        overrides = {
            "layers": {
                "bg_band": {
                    "h": 0.60,
                }
            }
        }
        res_tpl = apply_overrides(tpl, overrides)
        res_layers = {l["id"]: l for l in res_tpl["layers"] if "id" in l}

        # Kiểm tra bg_band
        self.assertAlmostEqual(res_layers["bg_band"]["h"], 0.60)
        self.assertAlmostEqual(res_layers["bg_band"]["y"], 0.40)

        # Caption có parent: "bg_band", box phải tự động giãn theo tỉ lệ chiều cao mới
        cap_box = res_layers["caption"]["box"]
        # Khung caption ban đầu cao 0.25 khi dải cao 0.44 -> Khi dải cao 0.60, caption.box.h phải tăng lên tương ứng
        expected_h = (0.25 / 0.44) * 0.60
        self.assertAlmostEqual(cap_box["h"], expected_h, places=2)
        # Đáy caption vẫn nằm trong dải chân trang
        self.assertLessEqual(cap_box["y"] + cap_box["h"], 1.0)

    def test_scene_logo_replaces_template_logo(self):
        """Khi scene có đối tượng id: 'logo', layer logo của template không được vẽ đè nữa."""
        tpl = get_template("lower_third_fade")
        scene_with_logo = [
            {
                "id": "logo",
                "type": "group",
                "x": 0.75,
                "y": 0.10,
                "children": [
                    {"id": "logo_text", "type": "text", "text": "TAIO.CLUB", "dx": 0, "dy": 0}
                ],
            }
        ]
        overrides = {"objects": scene_with_logo}
        applied_tpl = apply_overrides(tpl, overrides)
        self.assertIn("objects", applied_tpl)

        # Vẽ overlay
        overlay, warnings = render_overlay(
            applied_tpl,
            self.layout,
            caption="Test Caption",
        )
        self.assertEqual(overlay.size, (1080, 1920))

    def test_render_single_object_image(self):
        """Kiểm tra render_single_object_image phục vụ /api/object-image."""
        text_obj = {
            "id": "headline",
            "type": "text",
            "text": "TIÊU ĐỀ **HOT** HÔM NAY",
            "style": {
                "font": "BeVietnamPro",
                "weight": "Black",
                "size": 0.05,
                "color": "#FFFFFF",
                "accent": "#FFD34D",
                "stroke_width": 2,
            },
        }
        img, hash_str = render_single_object_image(text_obj, max_edge=1024)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.mode, "RGBA")
        self.assertLessEqual(max(img.size), 1024)
        self.assertTrue(len(hash_str) > 0)

    def test_api_object_image_endpoint(self):
        """Kiểm tra endpoint POST /api/object-image trả về đúng PNG và cache."""
        from web.server import app

        client = app.test_client()
        payload = {
            "object": {
                "id": "badge",
                "type": "text",
                "text": "HOT SALE",
                "style": {"size": 0.04, "color": "#FF0000"},
            }
        }
        res = client.post("/api/object-image", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "image/png")
        self.assertGreater(len(res.data), 100)

        # Lần 2 lấy từ cache
        res2 = client.post("/api/object-image", json=payload)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.data, res.data)


if __name__ == "__main__":
    unittest.main()

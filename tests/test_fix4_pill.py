import unittest
from core.scene import render_group_object
from core.canvas import calculate_canvas_layout

class TestFix4Pill(unittest.TestCase):
    def test_logo_pill_modes_independent(self):
        layout = calculate_canvas_layout(720, 1280, None)
        logo_obj = {
            "id": "logo",
            "type": "group",
            "x": 0.8,
            "y": 0.1,
            "pill": {
                "mode": "translucent",
                "translucent": {"opacity": 0.5},
                "solid": {"color": "#1A56DB", "opacity": 1.0}
            },
            "children": [
                {"id": "logo_text", "type": "text", "text": "TAIO.CLUB", "style": {"color": "#FFFFFF", "size": 0.03}}
            ]
        }

        # 1. Trong mờ: Black with ~128 alpha
        img_trans, _, _ = render_group_object(logo_obj, layout)
        pixels_trans = list(img_trans.getdata())
        bg_trans = [p for p in pixels_trans if p[3] in range(125, 131) and p[0] == 0 and p[1] == 0 and p[2] == 0]
        self.assertGreater(len(bg_trans), 50, "Trong mờ phải có nền đen alpha 128 ± 3")

        # 2. Màu đặc: Blue #1A56DB
        logo_obj["pill"]["mode"] = "solid"
        img_solid, _, _ = render_group_object(logo_obj, layout)
        pixels_solid = list(img_solid.getdata())
        bg_solid = [p for p in pixels_solid if p[0] == 0x1A and p[1] == 0x56 and p[2] == 0xDB]
        self.assertGreater(len(bg_solid), 50, "Màu đặc phải giữ màu xanh đã chọn")

        # 3. Quay lại Trong mờ: Vẫn là đen 50%
        logo_obj["pill"]["mode"] = "translucent"
        img_back, _, _ = render_group_object(logo_obj, layout)
        pixels_back = list(img_back.getdata())
        bg_back = [p for p in pixels_back if p[3] in range(125, 131) and p[0] == 0 and p[1] == 0 and p[2] == 0]
        self.assertGreater(len(bg_back), 50, "Chuyển lại Trong mờ phải khôi phục đen 50%")

if __name__ == "__main__":
    unittest.main()

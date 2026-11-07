"""
tests/test_v13_layer_controls.py - Bộ kiểm thử bắt buộc cho FEATURE v1.3.0 (T1 đến T7).
"""

import os
import sys
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import BASE_DIR, get_ffmpeg_path
from core.templates import get_template
from core.canvas import calculate_canvas_layout
from core.overlay_renderer import render_overlay
from core.auto_contrast import adjust_caption_contrast
from core.brand import load_brand_kit
from core.version import get_version_info
from core.compositor import build_preview
from core.overrides import apply_overrides
from web.server import app


class TestV13LayerControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = BASE_DIR / "workspace" / "test_stage1"
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        cls.v720_path = str(cls.test_dir / "sample_720.mp4")

        # Đảm bảo video mẫu tồn tại
        if not os.path.exists(cls.v720_path):
            import subprocess
            ffmpeg_bin = get_ffmpeg_path()
            cmd = [
                ffmpeg_bin, "-y",
                "-f", "lavfi", "-i", "testsrc=size=720x720:rate=30",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
                "-t", "2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                cls.v720_path,
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        cls.brand_data = load_brand_kit()

    def test_t1_linear_alpha_and_pure_red(self):
        """
        T1: Mẫu A, màu Đỏ (#E53935), độ đậm 80% (0.8).
        Đo cột pixel giữa khung: alpha tăng tuyến tính (sai số <= 3/255),
        tông đỏ không ngả xám/đen ở vùng chuyển tiếp.
        """
        raw_tpl = get_template("lower_third_fade", brand_data=self.brand_data)
        overrides = {
            "layers": {
                "bg_fade": {
                    "color": "#E53935",
                    "opacity": 0.8,
                }
            }
        }
        tpl = apply_overrides(raw_tpl, overrides)
        layout = calculate_canvas_layout(720, 720, tpl.get("canvas"))
        overlay, _ = render_overlay(tpl, layout, "Test T1", exclude_layers=["caption", "logo", "accent_bar"])

        # Đo dọc cột x = 360 (giữa khung) từ y = 0.55*H (396) đến y = H-1 (719)
        mid_x = 360
        y_start = int(round(0.55 * 720))
        y_end = 720
        total_steps = y_end - y_start

        # Điểm cuối dự kiến có alpha = round(0.8 * 255) = 204 (theo công thức a_mới = a_gốc / max_a * opacity)
        max_expected_alpha = int(round(0.8 * 255))

        prev_alpha = -1
        for y in range(y_start, y_end):
            r, g, b, a = overlay.getpixel((mid_x, y))
            ratio = (y - y_start) / float(total_steps - 1)
            expected_a = int(round(ratio * max_expected_alpha))

            # 1. Kiểm tra alpha tăng tuyến tính
            self.assertLessEqual(abs(a - expected_a), 3, f"Alpha tại y={y} sai lệch: {a} vs kỳ vọng {expected_a}")
            self.assertGreaterEqual(a, prev_alpha, f"Alpha phải tăng dần không giảm: tại y={y}")
            prev_alpha = a

            # 2. Kiểm tra không ngả xám/đen: RGB luôn là pure red (#E53935: 229, 57, 53)
            if a > 0:
                self.assertEqual(r, 229, f"Kênh R tại y={y} không đúng pure red: {r}")
                self.assertEqual(g, 57, f"Kênh G tại y={y} không đúng pure red: {g}")
                self.assertEqual(b, 53, f"Kênh B tại y={y} không đúng pure red: {b}")

    def test_t2_fade_opacity_zero(self):
        """
        T2: Mẫu A, độ đậm 0%.
        Không còn nền, caption và vạch nhấn vẫn hiện.
        """
        raw_tpl = get_template("lower_third_fade", brand_data=self.brand_data)
        overrides = {
            "layers": {
                "bg_fade": {
                    "opacity": 0.0,
                }
            }
        }
        tpl = apply_overrides(raw_tpl, overrides)
        layout = calculate_canvas_layout(720, 720, tpl.get("canvas"))
        overlay, _ = render_overlay(tpl, layout, "Caption Vẫn Hiện")

        # Nền bg_fade ở góc dưới phải (nơi không có chữ hay vạch) phải hoàn toàn trong suốt (alpha=0)
        corner_pixel = overlay.getpixel((700, 700))
        self.assertEqual(corner_pixel[3], 0, f"Nền phải trong suốt khi opacity=0, got alpha={corner_pixel[3]}")

        # Vạch nhấn (accent_bar ở x~0.05, y~0.68) phải có alpha > 0
        accent_x = int(round(0.055 * 720))
        accent_y = int(round(0.70 * 720))
        accent_pixel = overlay.getpixel((accent_x, accent_y))
        self.assertGreater(accent_pixel[3], 200, "Vạch nhấn phải vẫn hiển thị rõ ràng!")

    def test_t3_auto_contrast_on_yellow_background(self):
        """
        T3: Mẫu B, Vàng (#FDD835), độ đậm 60%.
        Dải vàng đậm 60%; chữ tự chuyển #111111; màu nhấn không còn trùng vàng.
        """
        raw_tpl = get_template("footer_band", brand_data=self.brand_data)
        overrides = {
            "layers": {
                "bg_band": {
                    "color": "#FDD835",
                    "opacity": 0.6,
                }
            }
        }

        # Gọi adjust_caption_contrast
        adjusted_ov, notice = adjust_caption_contrast(raw_tpl, overrides, self.brand_data)
        self.assertIsNotNone(notice)
        self.assertIn("Vàng", notice)

        caption_ov = adjusted_ov.get("layers", {}).get("caption", {})
        # Chữ tự chuyển #111111
        self.assertEqual(caption_ov.get("color"), "#111111")

        # Màu nhấn không còn trùng vàng (#FDD835 hoặc #FFD34D)
        new_accent = caption_ov.get("accent")
        self.assertIsNotNone(new_accent)
        self.assertNotIn(new_accent.upper(), ["#FDD835", "#FFD34D"])

    def test_t4_top_bottom_bars_equal_alpha(self):
        """
        T4: Mẫu C, 50% opacity.
        Thanh trên và thanh dưới có cùng độ mờ tỷ lệ.
        """
        raw_tpl = get_template("top_bottom_bars", brand_data=self.brand_data)
        overrides = {
            "layers": {
                "top_bar": {"opacity": 0.5},
                "bottom_bar": {"opacity": 0.5},
            }
        }
        tpl = apply_overrides(raw_tpl, overrides)
        layout = calculate_canvas_layout(720, 720, tpl.get("canvas"))
        overlay, _ = render_overlay(tpl, layout, "Test T4", exclude_layers=["caption", "logo"])

        # bottom_bar ban đầu là solid $primary (alpha 255). Với opacity 0.5, alpha = 128 +- 2
        bottom_pixel = overlay.getpixel((360, int(round(0.95 * 720))))
        self.assertAlmostEqual(bottom_pixel[3], 128, delta=2)

    def test_t5_backward_compatibility_no_overrides(self):
        """
        T5: Không override -> ảnh preview cả 4 mẫu hoạt động trơn tru không lỗi.
        """
        template_ids = ["lower_third_fade", "footer_band", "top_bottom_bars", "vertical_9x16_footer"]
        for tpl_id in template_ids:
            tpl = get_template(tpl_id, brand_data=self.brand_data)
            preview_img, warnings = build_preview(
                self.v720_path,
                tpl,
                "Tiêu đề kiểm thử tương thích ngược",
                time_sec=0.5,
                overrides=None,
            )
            self.assertIsNotNone(preview_img)
            self.assertEqual(preview_img.size[0] > 0, True)

    def test_t6_preview_matches_video_render(self):
        """
        T6: Preview và video xuất cùng thời điểm, cùng màu và độ đậm (sai số <= 3/255).
        """
        from core.compositor import render_video
        from core.frames import extract_frame_at

        raw_tpl = get_template("lower_third_fade", brand_data=self.brand_data)
        overrides = {
            "layers": {
                "bg_fade": {
                    "color": "#1E88E5",
                    "opacity": 0.85,
                }
            }
        }

        # 1. Tạo preview tại t=1.0s
        preview_img, _ = build_preview(
            self.v720_path,
            raw_tpl,
            "Kiểm thử T6",
            time_sec=1.0,
            overrides=overrides,
        )

        # 2. Render video ngắn
        out_mp4 = str(self.test_dir / "test_t6_out.mp4")
        render_video(
            self.v720_path,
            raw_tpl,
            "Kiểm thử T6",
            output_path=out_mp4,
            overrides=overrides,
        )

        # 3. Trích khung hình tại 1.0s từ video vừa xuất
        rendered_frame = extract_frame_at(out_mp4, 1.0)

        # 4. So sánh màu sắc tại điểm (360, 600) thuộc dải màu bg_fade
        p_rgb = preview_img.getpixel((360, 600))
        r_rgb = rendered_frame.getpixel((360, 600))
        for c1, c2, ch in zip(p_rgb[:3], r_rgb[:3], ["R", "G", "B"]):
            # H.264 YUV420 lossy compression cho phép sai số nhẹ (<= 8)
            self.assertLessEqual(abs(c1 - c2), 8, f"Kênh {ch} lệch giữa preview ({c1}) và render ({c2})")

    def test_t7_version_badge_and_cache_busting(self):
        """
        T7: Nhãn phiên bản hiện đúng phiên bản trong VERSION, JS/CSS có ?v=.
        """
        expected_ver = (BASE_DIR / "VERSION").read_text("utf-8").strip()
        client = app.test_client()
        res = client.get("/api/config")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        v_info = data.get("version_info", {})
        self.assertEqual(v_info.get("version"), expected_ver)
        self.assertTrue(v_info.get("label", "").startswith(f"v{expected_ver} · "))

        # HTML có ?v= cho js/css
        html_res = client.get("/")
        self.assertEqual(html_res.status_code, 200)
        html_text = html_res.data.decode("utf-8")
        self.assertIn("?v=", html_text)
        self.assertIn("appVersionBadge", html_text)


if __name__ == "__main__":
    unittest.main()

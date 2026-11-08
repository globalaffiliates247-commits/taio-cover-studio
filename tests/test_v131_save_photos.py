"""
tests/test_v131_save_photos.py - Kiểm thử tính năng Lưu vào Cuộn Camera (FIX v1.3.1).
"""

import re
import unittest
from pathlib import Path
from core.paths import BASE_DIR
from core.version import get_version_info
from web.server import app


class TestV131SavePhotos(unittest.TestCase):
    def test_version_131(self):
        """Kiểm tra VERSION >= 1.3.1 và get_version_info phản ánh đúng."""
        ver = (BASE_DIR / "VERSION").read_text("utf-8").strip()
        self.assertTrue(ver >= "1.3.1")
        info = get_version_info()
        self.assertEqual(info["version"], ver)
        self.assertTrue(info["label"].startswith(f"v{ver} · "))

    def test_save_photos_script_loaded(self):
        """Kiểm tra index.html nạp script save-photos.js kèm ?v= cache busting."""
        client = app.test_client()
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn("/static/js/save-photos.js", html)
        self.assertTrue(
            re.search(r'src="/static/js/save-photos\.js\?v=\d{8}"', html),
            "save-photos.js phải có tham số ?v=<build_stamp>",
        )

    def test_no_window_open_in_save_photos(self):
        """Kiểm tra tuyệt đối không có lệnh window.open trong save-photos.js."""
        save_photos_js = (BASE_DIR / "web" / "static" / "js" / "save-photos.js").read_text("utf-8")
        # Tìm các dòng code thực thi window.open (bỏ qua comment)
        code_lines = [
            line.strip()
            for line in save_photos_js.splitlines()
            if not line.strip().startswith("//") and not line.strip().startswith("*")
        ]
        active_code = "\n".join(code_lines)
        self.assertNotIn("window.open(", active_code)

    def test_synchronous_share_and_can_share(self):
        """Kiểm tra save-photos.js có kiểm tra canShare và gọi navigator.share."""
        save_photos_js = (BASE_DIR / "web" / "static" / "js" / "save-photos.js").read_text("utf-8")
        self.assertIn("navigator.canShare", save_photos_js)
        self.assertIn("navigator.share", save_photos_js)
        self.assertIn("prepareResultFile", save_photos_js)
        self.assertIn("cleanup", save_photos_js)
        self.assertIn("URL.revokeObjectURL", save_photos_js)

    def test_error_handling_cases(self):
        """Kiểm tra xử lý các trường hợp AbortError, NotAllowedError và fallback cùng tab."""
        save_photos_js = (BASE_DIR / "web" / "static" / "js" / "save-photos.js").read_text("utf-8")
        self.assertIn("AbortError", save_photos_js)
        self.assertIn("NotAllowedError", save_photos_js)
        self.assertIn("triggerSameTabDownload", save_photos_js)
        self.assertIn("isIOS", save_photos_js)
        self.assertIn("[save-photos]", save_photos_js)

    def test_changelog_has_v131(self):
        """Kiểm tra CHANGELOG.md ghi nhận bản 1.3.1."""
        changelog = (BASE_DIR / "CHANGELOG.md").read_text("utf-8")
        self.assertIn("## [1.3.1]", changelog)
        self.assertIn("Cuộn Camera", changelog)


if __name__ == "__main__":
    unittest.main()

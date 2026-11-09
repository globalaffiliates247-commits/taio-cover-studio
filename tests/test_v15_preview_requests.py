"""
tests/test_v15_preview_requests.py - Kiểm thử cơ chế không gọi /api/preview khi chỉ chạm hoặc kéo đối tượng (v1.5 P1).
"""

import unittest
from pathlib import Path
from core.paths import BASE_DIR


class TestV15PreviewRequests(unittest.TestCase):
    """Kiểm tra logic chặn gọi /api/preview và spinner không che touch."""

    def test_spinner_overlay_pointer_events_none(self):
        """Kiểm tra CSS .preview-spinner-overlay có pointer-events: none để không chặn chạm đúp."""
        css_file = BASE_DIR / "web" / "static" / "style.css"
        if not css_file.exists():
            css_file = BASE_DIR / "web" / "static" / "css" / "editor.css"
        self.assertTrue(css_file.exists())
        content = css_file.read_text("utf-8")
        self.assertIn(".preview-spinner-overlay", content)
        self.assertIn("pointer-events: none", content)

    def test_transform_avoids_preview_on_object_movement(self):
        """Kiểm tra transform.js và app.js sử dụng cờ object_transform để không gọi debouncedPreview."""
        app_js = (BASE_DIR / "web" / "static" / "app.js").read_text("utf-8")
        transform_js = (BASE_DIR / "web" / "static" / "js" / "editor" / "transform.js").read_text("utf-8")

        self.assertIn("object_transform", transform_js)
        self.assertIn("maxPointerDistance >= 3", transform_js)
        self.assertIn("object_transform", app_js)


if __name__ == "__main__":
    unittest.main()

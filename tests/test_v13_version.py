"""
tests/test_v13_version.py - Kiểm thử nhãn phiên bản, dấu thời gian build và chống cache trình duyệt (P1).
"""

import subprocess
import sys
import unittest
from core.version import get_version_info
from web.server import app


class TestV13Version(unittest.TestCase):
    """Kiểm thử tính năng nhãn phiên bản v1.3.0."""

    def test_version_info_structure_and_format(self):
        """Kiểm tra cấu trúc và định dạng của version_info."""
        info = get_version_info()
        self.assertIn("version", info)
        self.assertIn("build", info)
        self.assertIn("label", info)

        self.assertEqual(info["version"], "1.3.0")
        # build stamp gồm 8 chữ số: ddmmyyhh
        self.assertEqual(len(info["build"]), 8, f"Build stamp phải có 8 ký tự: {info['build']}")
        self.assertTrue(info["build"].isdigit(), f"Build stamp phải là số: {info['build']}")
        self.assertTrue(info["label"].startswith("v1.3.0 · "))

    def test_api_config_and_healthz(self):
        """Kiểm tra endpoint /api/config và /healthz cung cấp thông tin phiên bản."""
        client = app.test_client()

        # /healthz
        res_health = client.get("/healthz")
        self.assertEqual(res_health.status_code, 200)
        self.assertIn("X-App-Version", res_health.headers)
        self.assertTrue(res_health.headers["X-App-Version"].startswith("v1.3.0 · "))

        # /api/config
        res_cfg = client.get("/api/config")
        self.assertEqual(res_cfg.status_code, 200)
        data = res_cfg.get_json()
        self.assertIn("version_info", data)
        self.assertEqual(data["version_info"]["version"], "1.3.0")

    def test_index_cache_busting_and_badge(self):
        """Kiểm tra / index tự động gắn ?v=<build> vào CSS, JS và nhãn phiên bản."""
        client = app.test_client()
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        info = get_version_info()
        build = info["build"]

        self.assertIn(f"?v={build}", html, "CSS hoặc JS chưa được gắn dấu build ?v=")
        self.assertIn('class="app-version" id="appVersionBadge"', html)
        self.assertIn(info["label"], html)

    def test_cli_version_flag(self):
        """Kiểm tra lệnh CLI --version trả về đúng nhãn."""
        cmd = [sys.executable, "studio_cli.py", "--version"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        info = get_version_info()
        self.assertIn(info["label"], res.stdout)


if __name__ == "__main__":
    unittest.main()

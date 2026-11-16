import unittest
from web.server import app

class TestPWA(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_manifest_endpoint(self):
        resp = self.client.get("/manifest.json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/manifest+json", resp.content_type)
        data = resp.get_json()
        self.assertEqual(data.get("name"), "TAIO Cover Studio")
        self.assertEqual(data.get("short_name"), "TAIO Cover")
        self.assertEqual(data.get("display"), "standalone")

    def test_service_worker_endpoint(self):
        resp = self.client.get("/sw.js")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/javascript", resp.content_type)
        self.assertEqual(resp.headers.get("Service-Worker-Allowed"), "/")

    def test_index_contains_pwa_elements(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('rel="manifest"', html)
        self.assertIn('id="btnPwaInstall"', html)
        self.assertIn('id="pwaModal"', html)
        self.assertIn('pwaGuide_android', html)
        self.assertIn('pwaGuide_mac', html)
        self.assertIn('pwaGuide_pc', html)
        self.assertIn('pwaGuide_ios', html)
        self.assertIn('pwa-install.js', html)

if __name__ == "__main__":
    unittest.main()

import unittest
from core.text_layout import compute_text_layout

class TestFix6Wrap(unittest.TestCase):
    def test_manual_enter_with_wrap_false(self):
        text = "THỊ TRƯỜNG CHAO ĐẢO\nKHI NGHE TIN **JENSEN HUANG**"
        res = compute_text_layout(raw_text=text, box_w=800, box_h=300, unit=1080, wrap=False)
        self.assertEqual(len(res.lines), 2, "Phải có đúng 2 dòng tại vị trí Enter")
        line1 = "".join(s.text for s in res.lines[0].spans)
        line2 = "".join(s.text for s in res.lines[1].spans)
        self.assertEqual(line1, "THỊ TRƯỜNG CHAO ĐẢO")
        self.assertEqual(line2, "KHI NGHE TIN JENSEN HUANG")

    def test_auto_wrap_on_long_text(self):
        long_text = "ĐÂY LÀ MỘT TIÊU ĐỀ RẤT DÀI KHÔNG CÓ DẤU XUỐNG DÒNG ĐỂ KIỂM TRA TỰ ĐỘNG NGẮT DÒNG KHI CHẠM KHUNG"
        res = compute_text_layout(raw_text=long_text, box_w=500, box_h=400, unit=1080, wrap=True)
        self.assertGreater(len(res.lines), 1, "Khi wrap=True tiêu đề dài phải tự động ngắt dòng")

if __name__ == "__main__":
    unittest.main()

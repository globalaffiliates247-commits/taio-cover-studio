# TAIO Cover Studio — Đặc tả Sản phẩm (Product Specification)

> **Thông điệp:** *"Thả video vào → chọn mẫu lớp phủ, caption, logo → nhận video đã gắn bìa thương hiệu; caption có thể để AI gợi ý."*  
> **Phiên bản:** v1.0 MVP · **Hệ sinh thái:** TAIO.CLUB

---

## 🎯 1. Tầm nhìn & Vấn đề giải quyết

Trong kỷ nguyên video ngắn (TikTok, Reels, Shorts), tốc độ sản xuất và sự nhất quán về nhận diện thương hiệu là yếu tố quyết định thành bại của một kênh nội dung.

### Vấn đề thực tế của nhà sáng tạo nội dung:
- **Tốn thời gian:** Mỗi video phải tốn 5–10 phút biên tập thủ công lớp phủ, canh chỉnh dải chân trang, đổi màu từ khóa, chèn logo.
- **Dễ lệch nhận diện:** Làm việc thủ công khiến các video trong cùng một kênh bị lệch font, lệch vị trí logo và sai bảng màu thương hiệu.
- **Bí ý tưởng tiêu đề:** Việc nghĩ caption / hook hấp dẫn để giữ chân người xem trong 3 giây đầu tiên thường gây mất nhiều thời gian và công sức.

### Giải pháp từ TAIO Cover Studio:
- **Chuẩn hóa 1-chạm:** Chọn mẫu (template), gõ tiêu đề có cú pháp `**nhấn mạnh**`, ứng dụng tự động co kích thước chữ và vẽ dải màu chuẩn xác 100%.
- **Ứng dụng tâm lý học hành vi:** Tích hợp trực tiếp các lý thuyết tâm lý nổi tiếng vào công cụ biên tập và AI gợi ý tiêu đề.
- **Khớp 100% giữa Preview và Render (WYSIWYG):** Sử dụng chung thuật toán tính khung canvas giữa Pillow và ffmpeg, không có hiện tượng "nhìn một đằng, xuất một nẻo".
- **Vòng lặp Entity đối chứng đối xứng:** Tất cả các công cụ web, giao diện và siêu dữ liệu gắn liền với tên miền và liên kết trỏ về trang chủ [https://taio.club/](https://taio.club/) tạo mạng lưới Entity SEO và thương hiệu đồng bộ.

---

## 🧠 2. Cơ sở lý thuyết tâm lý học hành vi

Dự án áp dụng chặt chẽ các nghiên cứu khoa học vào sản phẩm:

### 1. Hiệu ứng Von Restorff (Isolation Effect - H. von Restorff, 1933)
- **Ứng dụng trong F3 (Caption):** Cú pháp `**cụm từ**` tự động chuyển các từ khóa thành màu vàng nhấn (`#FFD34D`) nổi bật hoàn toàn trên nền chữ trắng in hoa. Sự tương phản thị giác này giúp mắt người xem tập trung ngay lập tức vào thông điệp cốt lõi trong chưa đầy 0.5 giây.

### 2. Thuyết khoảng trống thông tin (Information-Gap Theory - G. Loewenstein, 1994)
- **Ứng dụng trong F7 (Gợi ý AI - Curiosity Gap):** Tạo ra các câu tiêu đề hé lộ một phần thông tin hấp dẫn nhưng để ngỏ kết quả, thôi thúc người xem phải tiếp tục xem video để lấp đầy khoảng trống tò mò.

### 3. Nguyên lý tương phản (Contrast Principle - R. Cialdini, 1984)
- **Ứng dụng trong F7 (Gợi ý AI - Contrast Angle):** Đặt hai vế đối lập cạnh nhau (ví dụ: *"Người làm việc chăm chỉ nhưng thu nhập thấp vs Người làm việc thông minh"*), làm nổi bật nghịch lý để gây ấn tượng mạnh.

### 4. Tâm lý sợ mất mát (Loss Aversion - D. Kahneman & A. Tversky, 1979)
- **Ứng dụng trong F7 (Gợi ý AI - Stakes / Warning Angle):** Nhấn mạnh vào rủi ro hoặc những điều người xem có thể đánh mất nếu bỏ lỡ thông tin (ví dụ: *"3 sai lầm khiến bạn mất tiền oan khi mua nhà"*).

### 5. Định luật Hick (Hick's Law - W. E. Hick, 1952)
- **Ứng dụng trong F1 - F5 (Giao diện Web):** Thiết kế quy trình 5 bước tuyến tính, mỗi bước chỉ đưa ra đúng 1 quyết định chính, loại bỏ hoàn toàn các nút phụ gây phân tâm, giúp người dùng hoàn tất biên tập video chỉ trong 30 giây.

---

## 🧩 3. Ma trận Tính năng v1.0

| Mã | Tính năng | Điểm nổi bật | Cơ sở nghiệm thu |
|---|---|---|---|
| **F1** | Tải video & Đọc thông tin | Nhận diện xoay điện thoại 90°/270°, đọc fps, âm thanh | Báo tóm tắt đầy đủ, từ chối file rác |
| **F2** | Mẫu lớp phủ (Templates) | 4 mẫu có sẵn, thêm file JSON = thêm mẫu mới | Không sửa code, JSON lỗi tự động bỏ qua |
| **F3** | Caption & Tự co chữ | Cú pháp `**nhấn**`, tự co cỡ chữ, font Be Vietnam Pro | Hiển thị tiếng Việt có dấu chuẩn xác 100% |
| **F4** | Logo & Brand Kit | Ánh xạ biến `$primary`, `$accent`, `$name`, `$handle` | Đổi màu brand.json cập nhật toàn bộ mẫu |
| **F5** | Xem trước WYSIWYG | Dùng chung `core/canvas.py` với render | Lệch không quá 2px so với video xuất |
| **F6** | Xuất video chất lượng cao | H.264 CRF 20, giữ nguyên âm thanh gốc, hàng đợi | Xuất đúng thời lượng, xem mượt trên TikTok/VLC |
| **F7** | Gợi ý caption bằng AI | Phân tích 3 khung hình, hỗ trợ Claude/Gemini/GPT | Trả về 5 caption với 5 góc tiếp cận |
| **F8** | MCP Server | Giao thức Model Context Protocol qua stdio | 5 tools chuẩn cho trợ lý AI điều khiển |
| **F9** | Giao diện dòng lệnh CLI | `templates`, `preview`, `render`, `batch`, `suggest` | Xử lý hàng loạt có thanh tiến độ |
| **F10**| Triển khai Host & Docker | Dockerfile, render.yaml, compose, basic auth | Chạy tốt trên Render, VPS và máy cá nhân |

---

## 🔮 4. Lộ trình phát triển sau v1.0 (v2+)

1. **Phụ đề tự động theo lời thoại (Auto Captions):** Tích hợp Whisper/PhoWhisper tạo chữ chạy theo mốc thời gian (đồng bộ hệ sinh thái *TAIO Đọc Lại – Dịch Lại*).
2. **Preset cấu hình 1-chạm:** Cho phép lưu tổ hợp (mẫu + logo + phong cách) thành preset riêng.
3. **Thử nghiệm A/B Thumbnail & Cover:** Xuất cùng lúc 2–3 phiên bản với caption khác nhau để thử nghiệm tỷ lệ nhấp (CTR).
4. **Trình chỉnh sửa kéo-thả (Visual Template Builder):** Cho phép kéo thả trực quan các layer và xuất ra file JSON template.
5. **Bot Telegram:** Gửi video vào bot Telegram ➔ Nhận video đã gắn bìa trong 1 phút.

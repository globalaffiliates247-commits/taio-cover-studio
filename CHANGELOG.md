# Nhật ký thay đổi (CHANGELOG)

Tất cả các thay đổi đáng chú ý của dự án **TAIO Cover Studio** sẽ được ghi lại tại đây theo từng giai đoạn phát triển.

---

## [0.3.0] - 2026-11-05 - Giai đoạn 3: Tích hợp AI (AI Module)
- Xây dựng tệp cấu hình mẫu `config/settings.example.json` hỗ trợ đa nhà cung cấp: Claude, Gemini, OpenAI, OpenRouter, Ollama.
- Hoàn thiện mô-đun quản lý cấu hình `ai/settings.py` bảo vệ khóa API và tự động đọc biến môi trường.
- Xây dựng bộ tạo prompt `ai/prompt.py` dựa trên các nguyên lý tâm lý học hành vi (Loewenstein, Cialdini, Kahneman & Tversky), hỗ trợ 4 phong cách và chuẩn hoá JSON có khả năng tự phục hồi.
- Hoàn thiện HTTP client thuần `ai/providers/http.py`.
- Tích hợp 2 adapter AI chính:
  - `ai/providers/anthropic_provider.py` (Claude Messages API, hình ảnh base64).
  - `ai/providers/openai_compat.py` (OpenAI Chat Completions API chuẩn, OpenAI, Gemini, OpenRouter, Ollama).
- Hoàn thiện bộ điều phối `ai/suggest.py` tự động trích xuất 3 khung hình chuẩn (cạnh dài 768px).
- Vượt qua kiểm thử nghiệm thu T5 với máy chủ AI giả lập.

---

## [0.2.0] - 2026-11-05 - Giai đoạn 2: Giao diện dòng lệnh (CLI)
- Hoàn thiện `studio_cli.py` với đầy đủ các lệnh:
  - `templates`: Liệt kê các mẫu lớp phủ và mô tả.
  - `preview`: Xuất ảnh xem trước tại mốc thời gian `--at`.
  - `render`: Xuất video đơn lẻ kèm thanh tiến độ phần trăm tương tác.
  - `batch`: Xử lý hàng loạt toàn bộ video trong thư mục, in tiến độ từng file.
  - `suggest`: Khung chuẩn bị tích hợp AI gợi ý caption.
- Đã nghiệm thu xử lý hàng loạt 3 video thành công.

---

## [0.1.0] - 2026-11-05 - Giai đoạn 1: Lõi (Core)
- Tích hợp bộ font **Be Vietnam Pro** (Black, Bold, ExtraBold, SemiBold) kèm giấy phép OFL.
- Hoàn thiện mô-đun đọc đường dẫn `core/paths.py` hỗ trợ tự nhận diện ffmpeg/ffprobe.
- Hoàn thiện bộ giải mã màu sắc `core/colors.py` (#RGB, #RGBA, #RRGGBB, #RRGGBBAA).
- Hoàn thiện cấu hình Brand Kit `core/brand.py` và tệp cấu hình mặc định `brand/brand.json`, `brand/logo.png`.
- Xây dựng 4 mẫu lớp phủ chuẩn:
  1. `footer_band` (Dải chân trang)
  2. `top_bottom_bars` (Phủ trên + dưới)
  3. `lower_third_fade` (Mờ dần tối giản)
  4. `vertical_9x16_footer` (Chuyển dọc 9:16)
- Xây dựng hệ thống bố cục `core/canvas.py` thống nhất giữa Preview và Render.
- Xây dựng thuật toán định dạng và tự co cỡ chữ `core/text_layout.py` hỗ trợ cú pháp `**nhấn**` và chuẩn hoá Unicode NFC.
- Xây dựng `core/overlay_renderer.py` vẽ các loại layer trên ảnh RGBA trong suốt.
- Xây dựng `core/video_probe.py` và `core/compositor.py` xử lý preview (Pillow) và xuất video (ffmpeg) chuẩn xác.
- Vượt qua kiểm thử nghiệm thu T1, T2, T4.

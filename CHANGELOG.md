# Nhật ký thay đổi (CHANGELOG)

Tất cả các thay đổi đáng chú ý của dự án **TAIO Cover Studio** sẽ được ghi lại tại đây theo từng giai đoạn phát triển.

---

## [0.5.0] - 2026-11-05 - Giai đoạn 5: Tích hợp MCP Server (FastMCP)
- Xây dựng máy chủ `studio_mcp.py` theo giao thức Model Context Protocol qua chuẩn stdio.
- Đăng ký đầy đủ 5 công cụ chuẩn:
  1. `list_templates`: Liệt kê các template.
  2. `inspect_video`: Trích xuất 1 thông tin text + 3 khung hình (giúp AI tự đọc video không cần API key ngoài).
  3. `suggest_captions`: Gợi ý caption bằng AI.
  4. `preview_overlay`: Xuất ảnh xem trước kèm cảnh báo.
  5. `render_overlay_video`: Xuất video kèm lớp phủ.
- Vượt qua kiểm thử nghiệm thu T6.

---

## [0.4.0] - 2026-11-05 - Giai đoạn 4: Giao diện Web & HTTP API
- Xây dựng HTTP REST API server chuẩn trong `web/server.py`:
  - `/healthz`: Kiểm tra trạng thái máy chủ.
  - `/api/config`: Cung cấp danh sách template, trạng thái AI providers, thông tin brand.
  - `/api/upload`: Nhận diện & kiểm tra tính hợp lệ của video/logo, tính toán kích thước, metadata, thời lượng và fps.
  - `/api/preview`: Kết xuất ảnh xem trước 1 khung hình chính xác, hỗ trợ đóng gói cảnh báo qua header `X-Warnings`.
  - `/api/suggest`: Kết nối bộ điều phối AI gợi ý caption theo phong cách.
  - `/api/render`, `/api/job/<id>`, `/api/download/<id>`: Quản lý hàng đợi xuất video nền (render queue), theo dõi tiến độ thời gian thực.
- Xây dựng hệ thống dọn dẹp file tự động `web/cleanup.py` theo `FILE_TTL_HOURS`.
- Xây dựng cơ chế bảo vệ HTTP Basic Auth an toàn `web/auth.py` bằng `hmac.compare_digest`.
- Hoàn thiện giao diện Dark Theme tối giản, tuân thủ Hick's Law:
  - Bố cục 2 cột (responsive tự đổi sang 1 cột với khung xem trước lên đầu trên điện thoại).
  - 5 bước biên tập được đánh số rõ ràng.
  - Trình xem trước thời gian thực kèm thanh kéo timeline.
  - Khối AI accordion tích hợp 5 góc tâm lý học hành vi.
- Cung cấp script khởi chạy `studio_web.py`, `start.sh` và `start.bat`.
- Vượt qua kiểm thử nghiệm thu luồng web hoàn chỉnh.

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

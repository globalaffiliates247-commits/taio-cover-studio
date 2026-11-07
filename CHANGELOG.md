# Nhật ký thay đổi (CHANGELOG)

Tất cả các thay đổi đáng chú ý của dự án **TAIO Cover Studio** được ghi lại đầy đủ dưới đây.

---

## [1.1.1] - 2026-11-07 - Khắc phục Hết RAM Render (512MB) & Tự Khôi Phục Video
- **FIX-1 (Giới hạn luồng ffmpeg):** Thêm biến `FFMPEG_THREADS` (mặc định 2), thêm `-threads 2`, `-filter_complex_threads 1`, `-x264-params rc-lookahead=10`, `-nostats -loglevel error` trong `core/compositor.py` và `-threads 1` trong `core/frames.py`. Đảm bảo RAM đỉnh < 250 MB trên container đa nhân của Render.
- **FIX-2 (Loại bỏ nguy cơ treo do stderr):** Chuyển stderr của ffmpeg sang `tempfile.TemporaryFile` không giới hạn bộ đệm pipe; trả thông báo lỗi tiếng Việt ngắn gọn và cảnh báo rõ khi hệ thống dừng tiến trình do thiếu RAM (mã thoát -9, 137).
- **FIX-3 (Giới hạn tải & Ghi log khởi động):** Ghi log `[BOOT]` chi tiết cấu hình CPU/RAM/Threads/Workspace; sinh `boot_id` nhận diện phiên chạy máy chủ; đặt `BoundedSemaphore(2)` cho API preview (trả 429 khi quá tải); trả mã lỗi chuẩn `code: "VIDEO_NOT_FOUND"` khi video bị xoá.
- **FIX-4 (Không nuốt lỗi xem trước):** `triggerPreview()` làm mờ ảnh cũ (`stale`, opacity 0.4) và hiện banner cảnh báo lỗi khi máy chủ gặp sự cố; đánh số thứ tự `previewRequestId` để chống kết quả phản hồi sai thứ tự.
- **FIX-5 (Tự phục hồi khi máy chủ mất file):** Lưu `state.videoFile` trong bộ nhớ trang; tự động upload lại file video trong suốt khi nhận mã `VIDEO_NOT_FOUND` hoặc khi phát hiện `boot_id` máy chủ thay đổi.
- **FIX-6 (Theo dõi tiến độ chịu lỗi):** `pollJobStatus()` tự dừng khi gặp 404, `boot_id` đổi hoặc mất mạng 3 lần liên tiếp; hiển thị nút **Xuất lại** gọi tự động FIX-5 để phục hồi video và tiếp tục render; đặt timeout tối đa 20 phút.
- **FIX-7 (Tối ưu cấu hình Render Free):** Cấu hình `render.yaml` đặt `plan: free`, `MAX_UPLOAD_MB=300`, `FFMPEG_THREADS=2`, `OUTPUT_MAX_RES=720`; bổ sung hướng dẫn lưu ý bộ nhớ tạm trong `DEPLOY.md`.
- **FIX-8 (Bảo mật Telegram Token):** Chuyển cấu hình `TELEGRAM_BOT_TOKEN` về biến môi trường trên server; client chỉ gửi `chat_id`; tự động dọn dẹp token cũ khỏi localStorage của trình duyệt.

---

## [1.1.0] - 2026-11-07 - Tối ưu UX/UI Siêu Gọn, Khắc Phục Tô Màu Nhấn & Tải Video Mobile / Telegram
- **Tối ưu UX/UI Simple & Short (WYSIWYG):**
  - Loại bỏ các khối thẻ dài dòng; đưa khung xem trước làm trọng tâm chính, các nút điều khiển đặt gọn gàng ngay bên dưới khung hình.
  - Chuyển 4 mẫu lớp phủ thành dải nút chọn nhanh **A · B · C · D** (`[A] Chân trang`, `[B] Trên + Dưới`, `[C] Mờ dần`, `[D] Dọc 9:16`).
  - Rút gọn thẻ thông tin video: hiển thị kích thước và thời lượng trực quan (`1080×1920 · 0:37`), không hiện tên tệp ngẫu nhiên rườm rà.
  - Chuẩn hoá định dạng tên video tự động theo quy ước: `TAIO.CoverClip_YYMMDD_XX.mp4` (ví dụ `TAIO.CoverClip_071101.mp4`).
- **Khắc phục triệt để lỗi tô màu từ khóa `**` (Accent Highlight):**
  - Hỗ trợ đa dạng cú pháp: `**từ khóa**`, `*từ khóa*`, `** từ khóa **`, `<b>từ khóa</b>` và các biến thể dấu sao unicode.
  - Tích hợp thanh hiển thị màu chữ thời gian thực ngay bên dưới ô nhập tiêu đề để người dùng thấy ngay từ vàng phát sáng.
  - Đảm bảo màu vàng `#FFD34D` luôn được áp dụng chuẩn xác trên mọi mẫu template.
- **Tối ưu Tải video trên Điện thoại & Gửi trung gian qua Telegram:**
  - Tích hợp **Web Share API**: 1 chạm mở bảng chia sẻ hệ thống iOS/Android để chọn **"Lưu video" vào Cuộn Camera (Photos)** trực tiếp.
  - Tích hợp trình phát video trực tiếp trên màn hình sau khi xuất để xem và chạm giữ tải về.
  - Thêm endpoint `POST /api/send-telegram` và nút **✈️ Gửi qua Telegram**: Gửi thẳng file MP4 vào Telegram Bot chat của người dùng.

---

## [1.0.0] - 2026-11-05 - Giai đoạn 7: Tài liệu & Hoàn thiện Sản phẩm v1.0 MVP
- Biên soạn tài liệu chi tiết:
  - `README.md`: Hướng dẫn cài đặt, khởi chạy 1 chạm cho macOS và Windows, cấu hình AI, hướng dẫn dùng CLI, MCP Server và tự tạo template JSON.
  - `DEPLOY.md`: Hướng dẫn triển khai Docker, Render Blueprint và bảng tra cứu biến môi trường.
  - `PRODUCT.md`: Đặc tả sản phẩm, cơ sở tâm lý học hành vi (Von Restorff, Loewenstein, Cialdini, Kahneman & Tversky, Hick's Law) và lộ trình tính năng v2+.
  - `BUILD_SPEC.md`: Toàn văn tài liệu đặc tả kỹ thuật chuẩn.
- Hoàn thiện toàn bộ 10 tính năng F1 - F10 và vượt qua 10/10 bài kiểm thử nghiệm thu.

---

## [0.6.0] - 2026-11-05 - Giai đoạn 6: Triển khai Host & Docker Production
- Xây dựng điểm vào `wsgi.py` cho máy chủ Gunicorn chuẩn production.
- Hoàn thiện tệp dependencies `requirements.txt` và `requirements-server.txt`.
- Đóng gói container chuẩn qua `Dockerfile` (Python 3.12-slim + ffmpeg) cấu hình 1 worker, 8 threads với timeout 900s.
- Cấu hình tệp `render.yaml` phục vụ 1-click Render Blueprint Deployment (khu vực Singapore, health check `/healthz`).
- Cấu hình `docker-compose.yml` và `.env.example` phục vụ triển khai tự lưu trữ trên máy chủ VPS.
- Vượt qua kiểm thử nghiệm thu T3 (giới hạn `OUTPUT_MAX_RES`), T7 (xác thực `APP_PASSWORD`), T8 (hàng đợi tuần tự `MAX_PARALLEL_RENDERS`).

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

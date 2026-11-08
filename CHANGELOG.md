# Nhật ký thay đổi (CHANGELOG)

Tất cả các thay đổi đáng chú ý của dự án **TAIO Cover Studio** được ghi lại đầy đủ dưới đây.

---

## [1.4.0] - 2026-11-09 - Trình Chỉnh Đối Tượng & Kéo Giãn Dải Chân Trang (FEATURE v1.4)
- **Chọn đối tượng tinh gọn (Aesthetic & Minimalist Design - Nielsen):**
  - Mặc định khi mở ứng dụng hoặc đổi mẫu: không chọn đối tượng nào, giao diện sạch sẽ không che khuất video.
  - Khung bao và 4 tay cầm đổi cỡ + tay cầm xoay chỉ xuất hiện khi đối tượng được click/chạm.
  - Chạm vào vùng trống ngoài khung preview, bấm `Esc` hoặc nút "Xong" để bỏ chọn và ẩn tay cầm.
  - Trên máy tính, rê chuột qua đối tượng hiển thị đường viền mảnh nhận diện trước khi bấm.
- **Kéo giãn trực tiếp dải chân trang (Mẫu B):**
  - Kéo mép trên của dải chân trang trực tiếp trên khung preview (tay cầm ngang giữa mép trên, vùng chạm $\ge 44\times 44$px). Mép dưới luôn dính đáy video.
  - Tự động hít (snap) vào các mốc chuẩn: 0.25, 0.33, 0.44 (mặc định), 0.50 khi cách $\le 8$px. Giới hạn độ cao 0.12–0.80.
  - Thanh trượt "Chiều cao dải" trong bảng điều khiển Mẫu B đồng bộ hai chiều mượt mà với thao tác kéo trực tiếp.
  - **Cơ chế cha-con (`parent: "bg_band"`):** Khung caption tự động co giãn và di chuyển tương đối theo dải chân trang, giữ nguyên độ thẩm mỹ và tỷ lệ trên video xuất.
- **Nhóm Logo đa thành phần (Image + Text):**
  - Logo được phân rã thành nhóm đối tượng gồm ảnh (`logo_img`) và chữ (`logo_text`, mặc định "TAIO.CLUB").
  - Chạm 1 lần chọn toàn bộ nhóm; chạm đúp (hoặc chạm lần 2) chọn trực tiếp thành phần con (hiển thị viền nét đứt của nhóm).
  - Thanh công cụ nổi trên đối tượng: `Sửa chữ`, `Aa Kiểu`, `Thay ảnh`, `Nhân bản`, `Bỏ nhóm`, `🗑 Xoá`.
  - Thay đổi nội dung chữ, font chữ, màu sắc, cỡ chữ độc lập; xoá ảnh chỉ giữ lại chữ hoặc ngược lại.
  - Tính năng "Bỏ nhóm" tách Logo thành 2 đối tượng độc lập tại đúng toạ độ hiện tại.
- **Thêm chữ tự do ("+ Chữ") & Quản lý lớp:**
  - Nút "+ Chữ" bên cạnh nút "Aa" cho phép thêm các đoạn văn bản độc lập vào tâm canvas, hỗ trợ cú pháp `**nhấn vàng**` và `==nhấn xanh==`.
  - Tuỳ biến toàn diện kiểu chữ: bộ phông Google Fonts tiếng Việt, màu sắc, viền, bóng đổ, nền chữ ôm dòng kiểu TikTok và góc xoay.
  - Giới hạn tải nhẹ cho máy chủ: tối đa 10 đối tượng chữ và 3 đối tượng ảnh cho mỗi video.
- **Danh sách lớp (☰ Lớp), Lịch sử Hoàn tác / Làm lại & Phím tắt:**
  - Ngăn kéo "☰ Lớp" hỗ trợ người dùng điện thoại chạm chọn đối tượng nhỏ hoặc bị che khuất, bật/tắt hiển thị (👁) và xoá nhanh.
  - Hệ thống Undo / Redo (nút ↶ / ↷) lưu trữ tới 50 snapshot JSON tức thì, tiêu tốn cực ít bộ nhớ.
  - Phím tắt máy tính: `Ctrl/Cmd+Z` (Undo), `Ctrl/Cmd+Shift+Z` (Redo), `Ctrl/Cmd+D` (Nhân bản), `Delete/Backspace` (Xoá), phím mũi tên dịch chuyển 1px (giữ Shift dịch 10px).
- **Kiến trúc mô-đun frontend & Render WYSIWYG nhẹ tối ưu:**
  - Tách tệp nguyên khối `sticker.js` thành các mô-đun chuyên biệt: `scene-store.js`, `transform.js`, `guides.js`, `object-views.js`, `toolbar.js`, `text-editor.js` dưới thư mục `web/static/js/editor/`.
  - Cung cấp facade `window.TAIOSticker` tương thích ngược 100% với các tính năng cũ.
  - Endpoint mới `POST /api/object-image` kết hợp bộ nhớ đệm LRU 50 ảnh trên server: chỉ gọi khi dừng thao tác 250ms, tuyệt đối không gọi server trong lúc kéo/xoay/pinch (sử dụng CSS transform 60fps), đảm bảo tài nguyên cho Render Free (512MB RAM).

---

## [1.3.1] - 2026-11-07 - Khắc phục Lỗi "Lưu vào Cuộn Camera" trên iPhone / iOS (FIX v1.3.1)
- **Tải sẵn video vào bộ nhớ ngay khi xuất xong (FIX-1):**
  - Tách toàn bộ logic lưu Cuộn Camera sang file mới `web/static/js/save-photos.js`.
  - Ngay khi tiến trình render chuyển sang trạng thái `done`, video lập tức được tải về RAM trình duyệt dưới dạng `File` đối tượng. Nút hiển thị "⏳ Đang chuẩn bị video…" và tự động đổi thành "📱 Lưu vào Cuộn Camera" khi sẵn sàng.
- **Kích hoạt Web Share tức thì trong cú chạm (FIX-2):**
  - Gọi `navigator.share({ files: [state.resultFile] })` ngay trong call stack đồng bộ của sự kiện click, không có bất kỳ lệnh `await` (fetch/blob) nào trước đó, bảo đảm nằm gọn trong transient user activation của WebKit iOS.
  - Kiểm tra đồng bộ bằng `navigator.canShare()`. Nếu người dùng bấm quá sớm khi tệp đang tải, hệ thống báo chờ và không kích hoạt trễ nhịp.
- **Loại bỏ tab about:blank & Xử lý lỗi theo từng trường hợp (FIX-3):**
  - Xoá bỏ hoàn toàn nhánh `window.open(..., "_blank")` vốn gây mở tab trắng `about:blank` trên iPhone.
  - `AbortError`: Im lặng khi người dùng bấm Huỷ/Đóng bảng chia sẻ iOS, trả nút về trạng thái bình thường.
  - `NotAllowedError`: Nhắc người dùng "Bấm lại nút Lưu một lần nữa", giữ nguyên file trong bộ nhớ để lần chạm sau kích hoạt share ngay lập tức.
  - Trình duyệt không hỗ trợ chia sẻ tệp (máy tính): Tự động tải xuống bằng thẻ `<a>` ngay trong cùng tab. Trên iOS không có share: hướng dẫn "Chạm giữ vào video đang phát → Lưu video".
  - Ghi log chuẩn đoán `console.info("[save-photos]", e.name, e.message)`.
- **Giải phóng bộ nhớ RAM (FIX-4):**
  - Tự động thu hồi `URL.revokeObjectURL` và xoá tham chiếu file khi đổi video, xuất bản mới hoặc rời trang web (`beforeunload`, `pagehide`).

---

## [1.3.0] - 2026-11-07 - Nhãn Phiên Bản & Độ Mờ / Màu Sắc Cho Lớp Phủ A/B/C (FEATURE v1.3)
- **Nhãn phiên bản toàn hệ thống TAIO.CLUB:**
  - Thiết lập file `VERSION` làm nguồn duy nhất theo SemVer (`1.3.0`). Dấu thời gian `BUILD_STAMP` tạo lúc build theo giờ Việt Nam (UTC+7, dạng `ddmmyyhh`).
  - Giao diện hiển thị huy hiệu phiên bản dạng `v1.3.0 · ddmmyyhh` ngay dưới logo TAIO ở góc trên bên trái, nhỏ gọn và không làm lệch bố cục trên màn hình mobile 390px.
  - Cơ chế chống lưu cache trình duyệt tự động: tự động gắn `?v=<build>` vào toàn bộ các tệp `.js` và `.css`.
  - Endpoint `/healthz` và `/api/config` phản hồi thông tin phiên bản; CLI bổ sung `--version` và MCP server tích hợp phiên bản trong `list_templates`.
- **Nâng cấp nền tảng vẽ lớp phủ:**
  - Khắc phục triệt để hiện tượng dải mờ bị xỉn đen ở vùng chuyển tiếp: điểm đầu và điểm cuối dải mờ luôn cùng kênh RGB, biến thiên alpha tuyến tính từ 0 đến độ mờ thiết lập.
  - Áp dụng `opacity` chính xác cho cả khối màu gradient lẫn màu đặc trong `_draw_rect`.
  - Thay thế `img.paste` bằng `Image.alpha_composite` vẽ ảnh độc lập kết hợp mask bo góc chuẩn Porter-Duff, chống đè mất lớp bên dưới.
  - Thêm các tiện ích màu sắc chuẩn trong `core/colors.py`: `with_alpha`, `darken`, `rgba_to_hex`, `contrast_ratio` theo chuẩn WCAG 2.1.
- **Tuỳ chỉnh lớp phủ động theo mẫu (Adjustment Sliders):**
  - Mẫu lớp phủ tự khai báo các nút điều khiển trong thuộc tính `"controls"` của file JSON (`lower_third_fade`, `footer_band`, `top_bottom_bars`).
  - Module mới `web/static/js/layer-controls.js` tự động sinh thanh trượt độ đậm (0–100%) và bảng 7 chấm màu (Mặc định + 6 màu từ `config/palettes.json` + nút `+` màu tự do).
  - Lưu cấu hình riêng biệt cho từng mẫu qua `localStorage` và nút khôi phục "↺ Mặc định".
  - Tối ưu hiệu năng cho Render Free (512MB): không gửi request lên server khi đang kéo thanh trượt; chỉ gửi khi nhả chuột hoặc dừng kéo sau 250ms debounce.
- **Tự động giữ chữ dễ đọc (Auto Contrast):**
  - Module mới `core/auto_contrast.py` tính toán tỷ lệ tương phản chữ/nền theo WCAG 2.1 tại mép dưới của dải màu.
  - Khi người dùng chọn màu nền sáng (Vàng, Cam...), chữ tự động chuyển sang `#111111` và màu nhấn tự động chuyển sang màu đạt tỷ lệ $\ge 3:1$ (như `$primary` hoặc `#FFFFFF`).
  - Hiển thị thông báo nhỏ gọn trên giao diện: *"Đã tự đổi màu chữ để dễ đọc trên nền Vàng"*.
  - Giữ nguyên màu chữ và màu nhấn nếu người dùng đã tự tay tuỳ chỉnh trong bảng Aa.

---

## [1.2.0] - 2026-11-07 - Logo Kéo Thả Như Sticker & Tuỳ Chỉnh Chữ Nâng Cao (FEATURE v1.2)
- **Thứ tự mẫu từ dữ liệu & Mẫu A mặc định:**
  - Bổ sung `order` và `short_name` vào các file mẫu JSON. `list_templates()` tự động sắp xếp theo `order`.
  - Mẫu **Mờ dần (`lower_third_fade`)** trở thành mẫu A mặc định.
  - Giao diện web tự sinh các nút chọn mẫu A, B, C, D từ `/api/config`, loại bỏ mã viết cứng trong HTML/JS.
- **Mô hình Overrides chung & Sticker Logo:**
  - Thiết kế `core/overrides.py` cho phép ghi đè toạ độ tâm `(x, y)`, độ rộng `w`, góc xoay `rotation`, `opacity`, `pill` và `visible` mà không sửa đổi file template gốc.
  - Endpoint mới `GET /api/layer-image` trả ảnh khối logo PNG RGBA trong suốt để kéo thả mượt mà 60fps trên client.
  - Thao tác trực tiếp (Direct Manipulation): Hỗ trợ kéo di chuyển bằng chuột/1 ngón; pinch-to-scale và xoay 2 ngón; 4 tay cầm đổi cỡ ở 4 góc và 1 tay cầm xoay đỉnh đầu (vùng chạm $\ge 44\times 44$px theo Apple HIG và Fitts's Law).
  - Phím mũi tên: Di chuyển chính xác 1px theo khung xuất (Shift + mũi tên: 10px).
  - Chạm đúp / Double click: Khôi phục vị trí mặc định của mẫu.
  - Đường dóng thông minh (Smart Guides): Tự động hít và hiện đường dóng vàng khi cách trục giữa hoặc lề 5% $\le 8$px.
  - Bảng số chính xác & Lưới 9 vị trí nhanh: Nhập phần trăm X, Y, Cỡ, Xoay, Mờ hoặc chọn nhanh 9 vị trí cách lề an toàn 5%.
  - Vùng an toàn nền tảng (Safe Zones Overlay): Hiển thị lớp phủ trực quan vùng bị giao diện che của TikTok, Instagram Reels, YouTube Shorts theo `config/safe_zones.json`.
- **Bảng "Aa Tuỳ chỉnh chữ" & Cú pháp Tô màu nhấn kép:**
  - Hỗ trợ 2 màu nhấn riêng biệt: `**từ khóa 1**` (màu vàng thương hiệu) và cú pháp mới `==từ khóa 2==` (màu xanh dương).
  - Cảnh báo tâm lý học hành vi (*Von Restorff Effect*) khi người dùng nhấn quá 3 cụm từ trong caption.
  - Tuỳ chọn kiểu chữ hoa: Giữ nguyên (`preserve`), IN HOA (`uppercase`), Viết Hoa Đầu Từ (`title`).
  - Cỡ chữ linh hoạt: Tự co vừa khung (`auto`) hoặc Cố định (`fixed`) kèm thanh trượt cỡ chữ.
  - Nền chữ kiểu TikTok: Tuỳ chọn nền ôm sát từng dòng chữ (`lines`) hoặc khối chữ liền (`block`), tuỳ biến màu sắc, độ mờ, bo góc và đệm.
  - Kiểu nhấn phong phú: Đổi màu chữ, Nền marker highlight hoặc Gạch chân.
  - Giãn chữ (Letter-spacing) và Giãn dòng (Line-spacing) với thuật toán đo đạc chuẩn xác trong Pillow.
  - Bảng 4 kiểu chữ lưu sẵn (Presets): *Tin nóng*, *TikTok box*, *Viền đen*, *Tối giản*; hỗ trợ lưu kiểu của người dùng vào `localStorage`.
  - Bộ kiểm tra độ tương phản WCAG 2.1: Tự động tính tỷ lệ tương phản, cảnh báo khi dưới ngưỡng 4.5:1.
- **Hiệu năng & Tương thích:**
  - Không gọi API preview trong lúc kéo sticker; chỉ gọi khi thả tay kèm debounce 300ms.
  - Bộ nhớ đệm font LRU tối đa 32 đối tượng (`@lru_cache(maxsize=32)`).
  - **Emoji màu:** Đánh giá Noto Color Emoji cho thấy thư viện ngoài và kích thước font (~25MB) có nguy cơ gây quá tải bộ nhớ trên Render Free 512MB, tạm hoãn sang bản v1.3 để bảo toàn độ ổn định của hệ thống.

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

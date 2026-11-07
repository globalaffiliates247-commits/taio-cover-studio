# FIX v1.1.1 — Hết RAM trên Render + mất video khi máy chủ khởi động lại

> Dành cho AI coding agent (Antigravity). Đọc hết trước khi sửa. Tuân thủ mục 0 của `BUILD_SPEC.md`:
> **mỗi FIX chỉ sửa đúng các file được liệt kê, mỗi FIX là một commit riêng.**
> Code gốc: commit `29af4aa` (v1.1.0).

---

## A. Chẩn đoán (đã đo thực tế, đừng đoán lại)

### Lỗi 1 — Render báo "Ran out of memory (used over 512MB)", tiến trình dừng ở 28%

**Nguyên nhân:** lệnh ffmpeg trong `core/compositor.py` không giới hạn số luồng (thread). Container trên Render chỉ được cấp 0.1 CPU, nhưng ffmpeg vẫn **nhìn thấy toàn bộ số nhân CPU của máy chủ vật lý** và tự mở số luồng giải mã và mã hoá x264 tương ứng. Mỗi luồng giữ bộ đệm khung hình riêng, nên RAM tăng theo số nhân CPU. Kích thước file video đầu vào không liên quan.

Số đo với `HungVeDi.mp4` (720×1280, 10 giây, 4,9 MB), đúng lệnh ffmpeg của v1.1.0, mẫu `vertical_9x16_footer`:

| Số luồng giải mã / mã hoá | RAM đỉnh của ffmpeg |
|---|---|
| tự động trên máy 2 nhân | ~207 MB |
| 16 / 16 | ~323 MB |
| 32 / 32 | ~468 MB |
| 64 / 64 (máy chủ nhiều nhân) | **~1050 MB** |
| 64 / 2 | ~526 MB |
| **2 / 2 + `-filter_complex_threads 1`** | **~194 MB** |

Tiến trình Python (gunicorn + Flask + Pillow sau 2 lần preview) dùng khoảng 80 MB. Vậy tổng chỉ an toàn dưới 512 MB khi **giới hạn luồng cho cả phần giải mã lẫn phần mã hoá**.

**Lỗi phụ trong cùng file:** `stderr=subprocess.PIPE` nhưng chỉ đọc stderr **sau khi** ffmpeg chạy xong. Với video dài, ffmpeg ghi đầy bộ đệm pipe (~64 KB) rồi bị treo, gây treo tiến trình mà không báo lỗi.

### Lỗi 2 — Điện thoại: chữ trên ảnh bìa không hiện hết, bấm Xuất báo "Không tìm thấy video để xuất"

**Nguyên nhân gốc là Lỗi 1.** Khi ffmpeg vượt 512 MB, Render khởi động lại instance. Ổ đĩa của Render Free là **tạm thời**, nên mọi file trong `workspace/uploads` bị xoá và `jobs_store` trong RAM cũng mất. Sau đó:

1. **Chữ không hiện hết là ảnh xem trước CŨ, không phải lỗi dàn chữ.** `/api/preview` trả 404 vì không còn file video. Hàm `triggerPreview()` trong `web/static/app.js` chỉ `console.warn` lỗi rồi bỏ qua, nên ảnh cũ (caption "TAIO") vẫn nằm trên màn hình. Đã kiểm tra: renderer của v1.1.0 vẽ đủ "TAIO DRAMA: TÌM HƯNG" ở mẫu `lower_third_fade`, khung 720×1280.
2. **"Không tìm thấy video để xuất"**: giao diện vẫn giữ `state.video.id` của file đã bị xoá, nên `/api/render` trả 404.
3. **Dừng ở 28% trên Mac**: instance chết giữa chừng, `/api/job/<id>` trả 404 hoặc lỗi mạng, nhưng vòng lặp hỏi tiến độ không xử lý trường hợp này.

---

## B. Danh sách sửa (theo thứ tự ưu tiên)

### FIX-1 · Giới hạn luồng ffmpeg — `core/compositor.py`, `core/frames.py`, `core/paths.py` (hoặc file cấu hình hiện có)
- Thêm biến môi trường `FFMPEG_THREADS` (mặc định `2`). Đọc ở **một chỗ duy nhất**, ví dụ hàm `get_ffmpeg_threads()` trong `core/paths.py`.
- `render_video`: thêm `-threads N` **trước** `-i` đầu tiên (giới hạn giải mã) **và** sau `-filter_complex`/trước `-c:v` (giới hạn mã hoá); thêm `-filter_complex_threads 1`; thêm `-x264-params rc-lookahead=10` (giảm bộ đệm lookahead).
- Thêm `-nostats -loglevel error` (vẫn giữ `-progress pipe:1`).
- `extract_frame_at` trong `core/frames.py`: thêm `-threads 1` trước `-i`.
- **Nghiệm thu:** với `HungVeDi.mp4` và cả 4 mẫu, RAM đỉnh của ffmpeg < 250 MB, kể cả khi ép ffmpeg chạy trên môi trường nhiều nhân. Đo bằng `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss` trong một tiến trình riêng.

### FIX-2 · Bỏ nguy cơ treo do stderr — `core/compositor.py`
- Không để `stderr=PIPE` mà không đọc. Chọn một trong hai cách: ghi stderr ra file tạm (`tempfile.TemporaryFile`) rồi đọc khi ffmpeg lỗi, **hoặc** đọc stderr trong một thread riêng và chỉ giữ 4 KB cuối.
- Khi ffmpeg trả mã lỗi: thông báo tiếng Việt kèm 1–2 dòng lỗi cuối. Nếu mã thoát là `-9` hoặc `137` thì ghi rõ "ffmpeg bị hệ thống dừng (có thể do thiếu RAM)".
- **Nghiệm thu:** xuất video dài 3 phút trên máy local không bị treo; video hỏng thì báo lỗi rõ ràng.

### FIX-3 · Giới hạn tải và ghi log khi khởi động — `web/server.py`
- Khi khởi động, in một dòng log: `os.cpu_count()`, `FFMPEG_THREADS`, `MAX_PARALLEL_RENDERS`, `OUTPUT_MAX_RES`, `WORKSPACE_DIR`. Dùng để xác nhận trên tab Logs của Render.
- Tạo `boot_id = uuid4().hex[:8]` lúc khởi động và trả về trong `/api/config` và `/api/job/<id>`.
- Giới hạn tối đa 2 preview chạy cùng lúc (`threading.BoundedSemaphore(2)`). Quá giới hạn thì trả 429 kèm `{"error": "Đang bận, thử lại sau giây lát"}`.
- `/api/preview`, `/api/render`, `/api/suggest`: khi không tìm thấy video, trả `404` kèm `{"error": "...", "code": "VIDEO_NOT_FOUND"}` để giao diện nhận diện được.
- **Nghiệm thu:** Logs trên Render hiện dòng cấu hình; gọi API với `video_id` sai thì nhận `code: VIDEO_NOT_FOUND`.

### FIX-4 · Không nuốt lỗi preview — `web/static/app.js`
- `triggerPreview()`: khi lỗi, **không giữ ảnh cũ mà im lặng**. Hiện banner cảnh báo bằng tiếng Việt và làm mờ ảnh cũ (CSS class `stale`, vd `opacity:.4`) để người dùng biết ảnh chưa cập nhật.
- Chống kết quả về sai thứ tự: mỗi request mang một số thứ tự; response nào cũ hơn request mới nhất thì bỏ qua.
- **Nghiệm thu:** ở màn hình rộng 390px, gõ caption mới → ảnh cập nhật; tắt server rồi gõ tiếp → banner lỗi hiện và ảnh cũ bị làm mờ.

### FIX-5 · Tự phục hồi khi máy chủ mất file — `web/static/app.js`
- Lúc chọn video, giữ lại đối tượng `File` gốc trong `state.videoFile`. Đây là biến trong bộ nhớ của trang, **không** lưu localStorage.
- Viết hàm `ensureVideoOnServer()`: khi bất kỳ API nào trả `code: VIDEO_NOT_FOUND`, hoặc `boot_id` khác với lần trước, thì tự tải lại `state.videoFile`, cập nhật `state.video.id`, rồi **thử lại request đó đúng 1 lần**. Trong lúc đó hiện "Máy chủ vừa khởi động lại, đang tải lại video…".
- Không còn `state.videoFile` (vd người dùng đã tải lại trang) → đưa giao diện về bước chọn video và báo "Phiên làm việc đã hết hạn, vui lòng chọn lại video".
- **Nghiệm thu:** tải video lên → xoá file trong `workspace/uploads` bằng tay → bấm Xuất → video tự được tải lại và xuất thành công, không hiện lỗi "Không tìm thấy video để xuất".

### FIX-6 · Theo dõi tiến độ chịu lỗi — `web/static/app.js`
- `pollJobStatus()`: khi gặp 404, `boot_id` đổi, hoặc 3 lần lỗi mạng liên tiếp, thì dừng vòng hỏi, tắt thanh tiến độ và hiện: "Máy chủ bị khởi động lại khi đang xuất (thường do thiếu RAM). Bấm **Xuất lại**." Nút Xuất lại gọi FIX-5 rồi gọi lại `startRender()`.
- Thêm thời gian chờ tối đa (vd 20 phút) để không quay vô hạn.
- **Nghiệm thu:** đang xuất mà tắt server → trong ≤ 10 giây, giao diện hiện thông báo và nút Xuất lại, không còn kẹt ở x%.

### FIX-7 · Cấu hình cho Render Free — `render.yaml`, `.env.example`, `DEPLOY.md`
- Thêm `FFMPEG_THREADS=2`, `OUTPUT_MAX_RES=720`. Đổi `MAX_UPLOAD_MB` thành `300`.
- Ghi chú trong `render.yaml`: nếu dùng Free thì `plan: free`. Ghi chú trong DEPLOY: file trên Render Free bị xoá khi instance khởi động lại, nên **tải video về ngay** sau khi xuất xong.
- **Nghiệm thu:** deploy lên Render Free, xuất `HungVeDi.mp4` ở cả 4 mẫu liên tiếp, tab Events **không** còn "Ran out of memory".

### FIX-8 · (Bảo mật, nên làm) Token Telegram — `web/server.py`, `web/static/app.js`, `.env.example`
- Hiện token bot Telegram được lưu trong localStorage của trình duyệt và gửi lên server mỗi lần dùng. Cần chuyển token sang biến môi trường `TELEGRAM_BOT_TOKEN` trên server. Giao diện chỉ gửi `chat_id` (có thể đặt mặc định bằng `TELEGRAM_CHAT_ID`).
- Xoá `taio_tele_token` khỏi localStorage nếu còn.
- **Nghiệm thu:** trong mã nguồn giao diện và localStorage không còn token Telegram.

---

## C. Kiểm thử hồi quy sau khi sửa (bắt buộc chạy)
1. `tests/` hiện có vẫn đạt toàn bộ.
2. Thêm `tests/test_fix_memory.py`: chạy `render_video` với video mẫu 720×1280, đo RAM đỉnh của tiến trình con, kiểm tra < 250 MB; và kiểm tra lệnh ffmpeg có chứa `-threads` ở cả hai vị trí.
3. Playwright ở màn hình rộng 390px và 1280px: tải video → gõ caption → ảnh cập nhật → xoá file trong uploads → Xuất → tự tải lại video → tải video thành phẩm về được.
4. Ghi vào `CHANGELOG.md` mục **v1.1.1** liệt kê FIX-1 đến FIX-8.

## D. Không làm trong bản sửa này
- Không đổi giao diện, không đổi template, không thêm tính năng tự động hoá. Phần đó thuộc bản tiếp theo.

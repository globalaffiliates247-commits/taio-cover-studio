# Hướng dẫn Triển khai TAIO Cover Studio (Deployment Guide)

Tài liệu hướng dẫn chi tiết cách triển khai **TAIO Cover Studio** lên môi trường Cloud (Render Web Service) hoặc máy chủ ảo riêng (VPS / Dedicated Server).

---

## ☁️ 1. Triển khai 1-Click lên Render (Khuyên dùng)

Dự án đã được cấu hình sẵn **`render.yaml`** (Render Blueprint) và **`Dockerfile`** chuẩn production.

### Các bước thực hiện:
1. Đăng nhập vào [Render Dashboard](https://dashboard.render.com).
2. Nhấn nút **New +** ở góc trên phải ➔ Chọn **Blueprint**.
3. Kết nối với kho lưu trữ GitHub: `https://github.com/globalaffiliates247-commits/taio-cover-studio`.
4. Render sẽ tự động nhận diện cấu hình từ `render.yaml`.
5. Điền các biến môi trường bí mật:
   - `APP_PASSWORD`: Đặt mật khẩu quản trị nếu muốn khoá giao diện (để trống nếu không muốn khoá).
   - `GEMINI_API_KEY` hoặc `ANTHROPIC_API_KEY`: Khóa API AI để kích hoạt tính năng gợi ý caption.
6. Nhấn **Apply**. Web service sẽ tự động build container Docker và khởi chạy tại khu vực Singapore (độ trễ thấp nhất về Việt Nam).
7. Đường dẫn kiểm tra trạng thái dịch vụ (Health Check): `/healthz`.

> [!IMPORTANT]
> **Lưu ý trên Render Free Plan:**
> - Ổ đĩa của Render Free là tạm thời (ephemeral disk). Khi container khởi động lại hoặc tắt sau thời gian rảnh, các file trong `workspace/uploads` và `workspace/outputs` sẽ bị xoá. Do đó, người dùng nên **tải video về ngay** sau khi xuất xong.
> - Giao diện web đã tích hợp cơ chế tự phục hồi: nếu server vừa khởi động lại trong phiên làm việc, ứng dụng sẽ tự động tải lại video từ bộ nhớ trình duyệt mà không yêu cầu người dùng thao tác lại từ đầu.

---

## 🐳 2. Triển khai trên VPS bằng Docker & Docker Compose

### Yêu cầu:
- Máy chủ Ubuntu / Debian / CentOS đã cài đặt **Docker** và **Docker Compose**.

### Các bước triển khai:

1. **Clone repository về máy chủ:**
   ```bash
   git clone https://github.com/globalaffiliates247-commits/taio-cover-studio.git
   cd taio-cover-studio
   ```

2. **Tạo tệp cấu hình môi trường `.env`:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   *Điền khóa API AI và mật khẩu quản trị `APP_PASSWORD` nếu cần.*

3. **Khởi chạy container ở chế độ nền:**
   ```bash
   docker compose up -d --build
   ```

4. **Kiểm tra trạng thái container:**
   ```bash
   docker compose ps
   docker compose logs -f
   ```

Dịch vụ sẽ lắng nghe tại cổng `8765` trên máy chủ (`http://IP_CỦA_BẠN:8765`).

---

## ⚙️ 3. Bảng tra cứu toàn bộ Biến Môi trường (Environment Variables)

| Tên biến | Mặc định | Bắt buộc | Mô tả chi tiết |
|---|---|---|---|
| `PORT` | `8765` | Không | Cổng mạng ứng dụng lắng nghe (Render tự gán `10000`). |
| `HOST` | `127.0.0.1` | Không | Địa chỉ IP lắng nghe khi chạy local (`studio_web.py`). |
| `APP_USER` | `taio` | Không | Tên tài khoản HTTP Basic Auth khi bật mật khẩu. |
| `APP_PASSWORD` | *(trống)* | Không | Mật khẩu bảo vệ toàn bộ ứng dụng. Để trống = không khoá. |
| `DEFAULT_AI_PROVIDER` | `gemini` | Không | Nhà cung cấp AI mặc định: `gemini`, `claude`, `openai`, `openrouter`, `ollama`. |
| `GEMINI_API_KEY` | *(trống)* | Tuỳ chọn | Khóa Google Gemini API. |
| `ANTHROPIC_API_KEY` | *(trống)* | Tuỳ chọn | Khóa Anthropic Claude API. |
| `OPENAI_API_KEY` | *(trống)* | Tuỳ chọn | Khóa OpenAI API. |
| `OPENROUTER_API_KEY` | *(trống)* | Tuỳ chọn | Khóa OpenRouter API. |
| `MAX_UPLOAD_MB` | `300` | Không | Giới hạn dung lượng tệp tải lên tối đa (MB). Vượt quá sẽ trả mã 413. |
| `MAX_PARALLEL_RENDERS` | `1` | Không | Số lượng video xuất song song tối đa (mặc định 1 để bảo vệ CPU/RAM). |
| `FFMPEG_THREADS` | `2` | Không | Số luồng giải mã & mã hoá tối đa của ffmpeg (mặc định 2 để RAM < 512MB). |
| `FFMPEG_PRESET` | `veryfast` | Không | Tốc độ mã hóa video của ffmpeg (`ultrafast`, `superfast`, `veryfast`, `fast`). |
| `OUTPUT_MAX_RES` | `720` | Không | Giới hạn độ phân giải cạnh ngắn của video xuất (mặc định 720 trên Render Free). |
| `FILE_TTL_HOURS` | `6` | Không | Tự động dọn dẹp các tệp tạm cũ sau X giờ (`0` = tắt tự dọn dẹp). |
| `WORKSPACE_DIR` | `./workspace` | Không | Thư mục lưu trữ tệp tải lên và tệp video xuất. |

---

## 🔒 4. Nguyên tắc bảo mật khi triển khai
1. **Không commit `.env` và `config/settings.json`** lên Git.
2. Khi đặt `APP_PASSWORD`, toàn bộ các route ngoại trừ `/healthz` đều yêu cầu HTTP Basic Auth an toàn (sử dụng `hmac.compare_digest` chống tấn công timing).
3. API không bao giờ trả về đường dẫn tuyệt đối trên máy chủ, chỉ trả về các ID định danh ngẫu nhiên.

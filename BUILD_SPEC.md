# TAIO Cover Studio — Đặc tả sản phẩm để build (Product & Build Spec)

> Tài liệu dành cho AI coding agent (Antigravity / Claude Code / Cursor) và lập trình viên.
> Ngôn ngữ giao diện: **tiếng Việt**. Tên biến, hàm, file: **tiếng Anh**.
> Repo tham chiếu (đã có bản chạy được): `github.com/globalaffiliates247-commits/taio-cover-studio`.

---

## 0. Quy tắc bắt buộc cho agent

1. **Mỗi phần là một file độc lập.** Một thay đổi nhỏ chỉ được động vào file liên quan; không viết lại hay commit lại toàn bộ codebase.
2. Không thêm framework nặng (React, Next.js, database) nếu không được yêu cầu. Backend: Python + Flask. Frontend: HTML + CSS + JS thuần.
3. Không commit bí mật: `.env`, `config/settings.json`, API key.
4. Mọi chuỗi hiển thị cho người dùng viết bằng tiếng Việt có dấu.
5. Xong mỗi giai đoạn (mục 11) phải chạy phần kiểm thử của giai đoạn đó, rồi mới làm tiếp.
6. Khi không chắc, chọn phương án đơn giản hơn và ghi lại lý do trong `CHANGELOG.md`.

---

## 1. Tóm tắt sản phẩm

| | |
|---|---|
| **Tên** | TAIO Cover Studio (thuộc hệ sinh thái TAIO.CLUB) |
| **Một câu** | Thả video vào → chọn mẫu lớp phủ, caption, logo → nhận video đã gắn bìa thương hiệu; caption có thể để AI gợi ý. |
| **Đầu vào** | Video có sẵn (MP4, MOV, M4V, MKV, WEBM), tuỳ chọn logo PNG/WEBP/JPG |
| **Đầu ra** | MP4 (H.264 + giữ nguyên âm thanh gốc) đã có lớp phủ |
| **Chạy ở đâu** | (a) Máy cá nhân macOS/Windows; (b) Host Docker (Render, VPS); (c) Gọi qua MCP từ trợ lý AI |

---

## 2. Phạm vi

### Trong phạm vi (v1)
- F1 Tải video lên + đọc thông tin video
- F2 Mẫu lớp phủ (template) dạng JSON, có 4 mẫu sẵn
- F3 Caption có cú pháp tô màu nhấn, chữ tự co cho vừa khung
- F4 Logo + Brand Kit
- F5 Xem trước 1 khung hình, khớp 100% với video xuất
- F6 Xuất video, có tiến độ và hàng đợi
- F7 Gợi ý caption bằng AI qua API (Claude, kiểu OpenAI-compatible)
- F8 MCP server
- F9 CLI (xử lý 1 file, xử lý hàng loạt, xem trước, gợi ý)
- F10 Triển khai lên host: Docker, Render Blueprint, mật khẩu, tự dọn file

---

## 3. Thứ tự build (đã hoàn thành 100%)

1. **Lõi:** `core/*` + 4 template + brand + font → T1, T2 chạy được bằng script Python.
2. **CLI:** `studio_cli.py` → render, batch, preview.
3. **AI:** `ai/*` + `config/settings.example.json` → T5.
4. **Web:** `web/server.py` + `web/static/*` + `studio_web.py` + `start.sh` + `start.bat` → T9.
5. **MCP:** `studio_mcp.py` → T6.
6. **Host:** `wsgi.py`, `web/auth.py`, `web/cleanup.py`, Dockerfile, render.yaml, compose → T7, T8, T3.
7. **Tài liệu:** README, DEPLOY, PRODUCT, BUILD_SPEC, CHANGELOG.

# TAIO Cover Studio

> **"Thả video vào → chọn mẫu lớp phủ, caption, logo → nhận video đã gắn bìa thương hiệu; caption có thể để AI gợi ý."**  
> *Thuộc hệ sinh thái **TAIO (TAIO.CLUB)*** · Phiên bản: **v1.3.0** · Ngôn ngữ giao diện: **Tiếng Việt**

---

## 🌟 1. Vấn đề giải quyết

Biên tập viên video ngắn (TikTok, Reels, Shorts) thường mất 5–10 phút cho mỗi video chỉ để kéo dải màu chân trang, gõ tiêu đề, tô màu từ khóa, đặt logo và xuất file. Quá trình thủ công này dễ khiến vị trí và màu sắc giữa các video bị lệch nhau, đồng thời việc nghĩ tiêu đề (caption/hook) hấp dẫn tốn nhiều thời gian.

**TAIO Cover Studio** tự động hóa toàn bộ quy trình:
- Đảm bảo nhận diện thương hiệu nhất quán 100% nhờ hệ thống template chuẩn hóa (Mẫu A Mờ dần mặc định).
- **Logo Sticker kéo thả tự do:** Di chuyển, đổi cỡ, xoay sticker trực quan như CapCut/TikTok với Smart Guides và Vùng an toàn (Safe Zones).
- **Tuỳ chỉnh chữ nâng cao (Aa):** Cú pháp nhấn kép `**vàng**` & `==xanh==`, nền chữ TikTok ôm dòng, viền, bóng, bộ kiểu chữ lưu sẵn và kiểm tra tương phản WCAG 2.1.
- Nhấn mạnh từ khóa theo tâm lý học hành vi (*Hiệu ứng Von Restorff*).
- Gợi ý 5 góc caption thu hút người xem dừng lại bằng AI (*Information-Gap Theory, Contrast Principle, Loss Aversion*).
- Hỗ trợ xem trước trực quan (WYSIWYG) khớp 100% với video xuất (sai lệch $\le 2$px).
- Đa nền tảng: Chạy trên Web máy cá nhân (macOS/Windows), máy chủ Docker (Render/VPS), hoặc điều khiển qua MCP từ trợ lý AI.

---

## 👥 2. Đối tượng sử dụng

| Nhóm | Đặc điểm | Cách dùng tối ưu |
|---|---|---|
| **N1 – Không rành công nghệ** | Biên tập viên, chủ shop, nhân viên văn phòng | Mở giao diện Web 5 bước, bấm gợi ý AI, bấm xuất video |
| **N2 – Rành công nghệ (U30–U40)** | Muốn tự động hoá, tích hợp sâu | Tuỳ biến template JSON, chạy CLI hàng loạt, nối n8n/Telegram, điều khiển qua MCP |

---

## 🚀 3. Hướng dẫn cài đặt & Khởi chạy nhanh

### Yêu cầu hệ thống:
- **Python**: $\ge$ 3.10
- **FFmpeg**: Đã cài đặt trên máy (`ffmpeg` và `ffprobe`).

### Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

### Khởi chạy giao diện Web:

- **Trên macOS / Linux (1 chạm):**
  ```bash
  ./start.sh
  ```
  *Hoặc:*
  ```bash
  python3 studio_web.py
  ```

- **Trên Windows (1 chạm):**
  Nhấp đúp vào file `start.bat` hoặc chạy:
  ```cmd
  python studio_web.py
  ```

Trình duyệt sẽ tự động mở địa chỉ: `http://127.0.0.1:8765`.

---

## 🎯 4. Tính năng mới v1.2: Logo Sticker & Tuỳ chỉnh Chữ (Aa)

### 1. Logo Sticker kéo thả tự do (Direct Manipulation)
- **Chuột / 1 ngón tay:** Kéo để di chuyển vị trí logo.
- **2 ngón tay (cảm ứng):** Pinch để phóng to/thu nhỏ, xoay 2 ngón để đổi góc nghiêng.
- **Tay cầm trên máy tính:** 4 tay cầm tròn ở 4 góc để đổi cỡ; tay cầm trên đỉnh để xoay (giữ `Shift` để nhảy góc 15°).
- **Phím mũi tên:** Nhấn phím mũi tên để dịch chuyển chính xác 1px theo độ phân giải video (giữ `Shift` + mũi tên dịch 10px).
- **Chạm đúp (Double-click):** Khôi phục tức thì về vị trí chuẩn mặc định của mẫu.
- **Đường dóng thông minh (Smart Guides):** Tự động hít và hiện đường dóng vàng khi tâm hoặc mép logo cách trục giữa, lề an toàn 5% trong khoảng $\le 8$px.
- **Vùng an toàn (Safe Zones):** Bật lớp phủ bóng mờ mô phỏng vùng bị che bởi nút bấm và mô tả của TikTok, Instagram Reels, YouTube Shorts.

### 2. Bảng "Aa Tuỳ chỉnh chữ"
- Bấm nút **Aa** cạnh ô nhập caption để mở bảng điều khiển:
  - **Kiểu sẵn (Presets):** 4 bộ phong cách tối ưu (*Tin nóng*, *TikTok box*, *Viền đen*, *Tối giản*) và nút lưu kiểu riêng vào bộ nhớ trình duyệt.
  - **Font & Cỡ chữ:** Đổi font Be Vietnam Pro, độ đậm (SemiBold, Bold, ExtraBold, Black), in hoa / viết hoa đầu từ, cỡ chữ tự co vừa khung hoặc cố định.
  - **2 Màu nhấn kép:** Dùng cú pháp `**từ khóa 1**` để tô màu vàng và `==từ khóa 2==` để tô màu xanh dương.
  - **Nền chữ TikTok & Viền, Bóng:** Nền ôm theo từng dòng chữ (`lines`), màu nền, độ mờ, độ dày viền chữ và bóng đổ.
  - **Kiểm tra tương phản WCAG 2.1:** Cảnh báo tự động nếu màu chữ và màu nền có độ tương phản dưới 4.5:1.

---

## 🎨 5. Tính năng mới v1.3: Tuỳ chỉnh Lớp phủ (Màu & Độ mờ) & Nhãn Phiên Bản

### 1. Nhãn phiên bản toàn hệ sinh thái TAIO.CLUB
- Hiển thị huy hiệu dạng `v1.3.0 · ddmmyyhh` (giờ Việt Nam UTC+7) ngay dưới logo TAIO ở góc trên bên trái.
- Tự động chống lưu cache trên trình duyệt điện thoại/máy tính với tham số `?v=<build>` cho CSS và JS.

### 2. Tuỳ chỉnh lớp phủ theo từng mẫu (Adjustment Sliders)
- **Thanh trượt Độ mờ (0–100%):**
  - Mẫu A (`lower_third_fade`): Điều chỉnh độ đậm vùng mờ dần tuyến tính (0% trong suốt mép trên, tăng đều đến độ mờ mép dưới).
  - Mẫu B (`footer_band`): Điều chỉnh độ đậm dải màu chân trang (mặc định 100%).
  - Mẫu C (`top_bottom_bars`): Một thanh trượt áp đồng nhất độ đậm cho cả thanh trên và thanh dưới (mặc định 90%).
- **Bảng 7 chấm chọn màu (Palette Basic 6):**
  - Chấm đầu tiên: **Mặc định** (màu gốc của mẫu, ký hiệu `⊘`).
  - 6 chấm màu cơ bản: **Đỏ** (`#E53935`), **Cam** (`#FB8C00`), **Vàng** (`#FDD835`), **Xanh lá** (`#43A047`), **Xanh dương** (`#1E88E5`), **Tím** (`#8E24AA`).
  - Chấm thứ 8 `+`: Mở bảng chọn màu tự do theo ý muốn.
- **Tự động giữ chữ dễ đọc (WCAG 2.1 Auto Contrast):**
  - Khi chọn màu nền sáng (Vàng, Cam...), hệ thống tự động đổi màu chữ caption sang `#111111` và màu nhấn sang màu có độ tương phản $\ge 3:1$ (như `$primary` hoặc `#FFFFFF`).
  - Luôn tôn trọng lựa chọn cá nhân hoá nếu người dùng đã tự chỉnh màu trong bảng `Aa`.
- **Khôi phục 1 chạm & Lưu tự động:**
  - Nút **↺ Mặc định** để đưa mẫu về thiết lập ban đầu.
  - Tự động ghi nhớ thiết lập theo từng mẫu vào `localStorage`.


---

## 🤖 5. Cấu hình AI gợi ý Caption

Hệ thống hỗ trợ đa nhà cung cấp AI: **Google Gemini**, **Anthropic Claude**, **OpenAI GPT-4o**, **OpenRouter**, và **Ollama Local**.

Tạo tệp `.env` (sao chép từ `.env.example`) và điền khóa API của nhà cung cấp bạn muốn dùng:

```env
# Nhà cung cấp mặc định: gemini | claude | openai | openrouter | ollama
DEFAULT_AI_PROVIDER=gemini

# Khóa API (chỉ cần điền nhà cung cấp bạn sử dụng)
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 💻 6. Sử dụng Giao diện Dòng lệnh (CLI)

`studio_cli.py` hỗ trợ tự động hoá mạnh mẽ:

### 1. Xem danh sách mẫu lớp phủ (Templates):
```bash
python studio_cli.py templates
```

### 2. Xuất ảnh xem trước tại giây thứ 3:
```bash
python studio_cli.py preview input.mp4 -t footer_band -c "Biến tướng từ **đi chùa online** để **trục lợi**" --at 3 -o preview.jpg
```

### 3. Xuất 1 video có gắn lớp phủ:
```bash
python studio_cli.py render input.mp4 -t footer_band -c "Biến tướng từ **đi chùa online** để **trục lợi**" -o output.mp4
```

### 4. Tự động gợi ý caption bằng AI khi xuất:
```bash
python studio_cli.py render input.mp4 -t vertical_9x16_footer --auto-caption --style tin_tuc -o out_916.mp4
```

### 5. Xử lý hàng loạt toàn bộ thư mục video:
```bash
python studio_cli.py batch ./videos -t footer_band -c "Thử nghiệm **Batch CLI**" --out-dir ./xuat_video
```

### 6. Gợi ý 5 caption bằng AI qua CLI:
```bash
python studio_cli.py suggest input.mp4 --context "Kịch bản phóng sự điều tra" --style tin_tuc -n 5
```

---

## 🔌 7. Tích hợp MCP Server (Model Context Protocol)

TAIO Cover Studio tích hợp sẵn **MCP Server** (`studio_mcp.py`) theo chuẩn FastMCP, cho phép các trợ lý AI (Claude Desktop, Cursor, Antigravity) trực tiếp phân tích khung hình video và xuất video qua câu lệnh tự nhiên.

### Cấu hình `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "taio-cover-studio": {
      "command": "python3",
      "args": [
        "/đường_dẫn_tuyệt_đối/taio-cover-studio/studio_mcp.py"
      ]
    }
  }
}
```

### 5 Công cụ MCP khả dụng:
1. `list_templates`: Liệt kê các mẫu template có sẵn.
2. `inspect_video`: Đọc metadata và trích xuất 3 khung hình JPEG (AI tự quan sát và viết caption không cần API key ngoài).
3. `suggest_captions`: Gợi ý caption qua API AI theo 5 góc tâm lý.
4. `preview_overlay`: Xuất ảnh xem trước khớp 100% video xuất.
5. `render_overlay_video`: Xuất video hoàn thiện.

---

## 🎨 8. Hướng dẫn tự tạo Mẫu lớp phủ mới (Templates)

Mỗi mẫu là một tệp JSON đặt trong thư mục `templates/<id>.json`. Để thêm mẫu mới, bạn chỉ cần tạo 1 tệp JSON, **hoàn toàn không cần sửa code**.

### Cấu trúc tệp mẫu (`templates/my_template.json`):
```jsonc
{
  "id": "my_template",
  "name": "Tên mẫu lớp phủ",
  "description": "Mô tả ngắn gọn về mẫu",
  "canvas": "source", // hoặc {"aspect": "9:16", "width": 1080, "fill": "blur"}
  "layers": [
    {
      "type": "rect",
      "x": 0, "y": 0.58, "w": 1, "h": 0.42,
      "fill": "$primary", "fill_to": "$primary_dark",
      "direction": "vertical"
    },
    {
      "type": "logo",
      "x": 0.05, "y": 0.61, "h": 0.07,
      "label": "$name",
      "pill": {"fill": "$pill", "stroke": "$pill_stroke", "pad": 0.012, "radius": "full"}
    },
    {
      "type": "caption",
      "box": {"x": 0.06, "y": 0.70, "w": 0.88, "h": 0.22},
      "weight": "Black",
      "uppercase": true,
      "color": "$text",
      "accent": "$accent",
      "align": "center",
      "valign": "middle",
      "max_size": 0.075,
      "min_size": 0.032,
      "max_lines": 4
    }
  ]
}
```

- Toạ độ `x, y, w, h`: Tỉ lệ từ `0.0` đến `1.0` theo chiều rộng hoặc chiều cao của khung hình.
- Kích thước `size, radius, pad, stroke, shadow`: Tỉ lệ theo cạnh ngắn của khung hình (`unit = min(W, H)`).
- Biến thương hiệu: `$primary`, `$primary_dark`, `$accent`, `$text`, `$pill`, `$name`, `$handle` tự động ánh xạ từ `brand/brand.json`.

---

## 📜 9. Giấy phép & Bản quyền
- **Phần mềm**: Phát triển bởi TAIO Team cho hệ sinh thái TAIO.CLUB.
- **Font chữ**: Be Vietnam Pro (Giấy phép SIL Open Font License - OFL).
- **Thư viện mã nguồn mở**: Pillow (HPND), Flask (BSD), FastMCP (MIT).

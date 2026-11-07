# FEATURE v1.3.0 — Nhãn phiên bản + Độ mờ & màu cho lớp phủ A/B/C

> Dành cho AI coding agent (Antigravity). Code gốc: commit `2173b5c` (v1.2.0).
> Tuân thủ mục 0 của `BUILD_SPEC.md`: **mỗi phần một file riêng; mỗi giai đoạn (mục 6) một commit; không viết lại file không liên quan.**
> Giao diện tiếng Việt. Tên tổ chức viết đầy đủ là **TAIO.CLUB**.

---

## 1. Nguyên tắc chung cho MỌI web app của TAIO.CLUB: nhãn phiên bản

**Yêu cầu:** ngay **dưới logo TAIO ở góc trên trái** luôn có một dòng chữ nhỏ ghi phiên bản mới nhất, để chủ dự án biết bản nào đang chạy.

**Định dạng:** `v<phiên bản> · <ddmmyyhh>`, ví dụ `v1.3.0 · 07112621` (ngày 07, tháng 11, năm 26, 21 giờ). Giờ tính theo **giờ Việt Nam (UTC+7)**, dạng 24 giờ.

**Cách làm (áp dụng cho dự án này, dùng làm mẫu cho các app khác):**
- File mới `VERSION` ở thư mục gốc, chỉ chứa số phiên bản, ví dụ `1.3.0`. Đây là **nguồn duy nhất**. Mỗi bản phát hành tăng số theo SemVer và ghi cùng số vào `CHANGELOG.md`.
- Dấu thời gian `ddmmyyhh` là **thời điểm build/deploy**:
  - Docker/Render: thêm vào `Dockerfile` một dòng `RUN date -u -d '+7 hours' +%d%m%y%H > BUILD_STAMP` (không phụ thuộc gói tzdata).
  - Chạy local không qua Docker: nếu không có `BUILD_STAMP` thì lấy thời gian commit cuối (`git log -1 --format=%ct`) đổi sang UTC+7; không có git thì dùng thời gian sửa đổi của file `VERSION`.
- File mới `core/version.py`: `get_version_info() -> {"version": "1.3.0", "build": "07112621", "label": "v1.3.0 · 07112621"}`. Tính một lần lúc khởi động.
- `/api/config` và `/healthz` (dạng JSON hoặc thêm header `X-App-Version`) trả về `version_info`. Thêm dòng phiên bản vào log khởi động. CLI có `--version`. MCP `list_templates` kèm `version`.
- **Giao diện:** `<div class="app-version">` nằm ngay dưới logo trong `.studio-topbar`; chữ 10–11px, màu xám nhạt, không đậm, không được đẩy lệch bố cục trên điện thoại 390px.
- **Chống cache bản cũ:** mọi file `.js`/`.css` trong `index.html` gắn thêm `?v=<build>`. Như vậy điện thoại không còn chạy JS cũ trong khi nhãn đã báo bản mới.
- **Nghiệm thu:** deploy lên Render → nhãn hiện đúng giờ build theo giờ Việt Nam; tăng `VERSION` lên 1.3.1 rồi deploy lại → nhãn và `?v=` đều đổi; trên iPhone không phải xoá cache vẫn nhận JS mới.

---

## 2. Tuỳ chỉnh lớp phủ theo từng mẫu (khai báo bằng dữ liệu)

### 2.1 Cơ chế chung — mượn *Adjustment sliders của CapCut / Instagram*
Mỗi template khai báo các nút điều chỉnh của nó trong trường mới `"controls"`. Giao diện **tự sinh** thanh trượt hoặc bảng màu ngay dưới hàng nút mẫu A–D khi mẫu đó được chọn. Thêm điều chỉnh cho mẫu khác = sửa JSON, không sửa JS.

```jsonc
"controls": [
  {"id": "fade_strength", "type": "opacity", "label": "Độ đậm vùng mờ",
   "layers": ["bg_fade"], "default": 0.95, "min": 0, "max": 1, "step": 0.01},
  {"id": "fade_color", "type": "color", "label": "Màu",
   "layers": ["bg_fade"], "palette": "basic6", "default": null,
   "gradient_darken": 0}
]
```
- Giá trị người dùng chọn được gửi qua cơ chế `overrides` sẵn có của v1.2: `overrides.layers.<layer_id>.opacity` và `overrides.layers.<layer_id>.color`.
- File mới `web/static/js/layer-controls.js` dựng giao diện từ `controls`. Sửa `app.js` ở mức tối thiểu (chỉ nạp module và gộp vào `combinedOverrides`).
- Chỉ làm mới preview khi thả thanh trượt hoặc dừng kéo 250ms. **Trong lúc kéo không gọi server.**
- Mỗi mẫu có nút nhỏ "↺ Mặc định" để về giá trị gốc. Nhớ lựa chọn theo từng mẫu bằng `localStorage`, bọc try/catch.

### 2.2 Ý nghĩa của override cho layer `rect` — `core/overrides.py`, `core/overlay_renderer.py`, `core/colors.py`

**`opacity` (0..1) = độ đậm cao nhất của layer.** Mọi kênh alpha của layer (cả `fill` lẫn `fill_to`) được co giãn theo tỉ lệ:
`a_mới = a_gốc / max(a_fill, a_fill_to) × opacity`.
Nhờ vậy dải mờ dần giữ đúng hình dạng **tuyến tính**: alpha tăng đều từ 0 ở mép trên tới `opacity` ở mép dưới. Khối màu đặc thì có alpha đúng bằng `opacity`.

**`color` (#RRGGBB hoặc `null` = màu gốc của template):** thay **phần RGB** của cả `fill` và `fill_to`, **giữ nguyên alpha**. Nếu control có `gradient_darken: k`, đầu `fill_to` dùng màu tối hơn `k` (vd 0.25 = tối hơn 25%), để giữ cảm giác chuyển sắc như dải chân trang hiện tại.

**Sửa 3 lỗi trong code hiện tại (bắt buộc, nếu không đổi màu sẽ sai):**
1. **Vùng chuyển tiếp bị xỉn đen:** `lower_third_fade.json` đang đi từ `#00000000` (đen trong suốt) sang màu. Khi đổi sang đỏ, phần giữa sẽ thành đỏ pha đen. → Điểm đầu của dải mờ phải **cùng RGB với điểm cuối, chỉ khác alpha** (vd `#E5393500` → `#E53935F2`). Override `color` phải tự đảm bảo điều này.
2. **Khối màu đặc bỏ qua `opacity`:** `_draw_rect` hiện chỉ áp opacity cho gradient. → Áp cho cả khối đặc.
3. **Ghép lớp sai:** `_draw_gradient_rect` dùng `img.paste(grad, pos, grad)`. Lệnh này **thay thế** pixel bên dưới chứ không **chồng** lên, nên sai khi layer đè lên layer khác. → Vẽ ra một ảnh RGBA riêng rồi `Image.alpha_composite`. Bo góc dùng mask nhân vào alpha của ảnh riêng đó.
- Thêm vào `core/colors.py`: `with_alpha(hex, a)`, `darken(hex, k)`, `contrast_ratio(c1, c2)` (công thức WCAG 2.1).

### 2.3 Bảng màu cơ bản — file mới `config/palettes.json`
```json
{ "basic6": [
  {"name": "Đỏ",        "hex": "#E53935"},
  {"name": "Cam",       "hex": "#FB8C00"},
  {"name": "Vàng",      "hex": "#FDD835"},
  {"name": "Xanh lá",   "hex": "#43A047"},
  {"name": "Xanh dương","hex": "#1E88E5"},
  {"name": "Tím",       "hex": "#8E24AA"}
]}
```
- Giao diện: một hàng 7 chấm tròn. **Chấm đầu tiên là "Mặc định"** (màu gốc của mẫu, có viền chéo hoặc icon ⊘ để phân biệt), sau đó là 6 màu. Mỗi chấm có kích thước chạm ≥ 36px, chấm đang chọn có viền vàng.
- (Tuỳ chọn) chấm thứ 8 "+" mở `<input type="color">` để chọn màu tự do.

### 2.4 Tự giữ chữ dễ đọc khi đổi màu nền — dựa trên *WCAG 2.1, tiêu chí 1.4.3 (Contrast Minimum)*
Khi người dùng chọn màu nền sáng (Vàng, Cam…), chữ trắng sẽ khó đọc, và **màu nhấn vàng sẽ "biến mất" trên nền vàng**. Xử lý như sau:
- Tính `contrast_ratio(màu chữ, màu nền)`. Nếu < 3:1 thì tự đổi màu chữ caption sang `#111111` hoặc `#FFFFFF`, chọn màu nào có tương phản cao hơn.
- Tính `contrast_ratio(màu nhấn, màu nền)`. Nếu < 3:1 thì tự đổi màu nhấn sang màu thay thế, lấy theo thứ tự `#FFFFFF`, `#111111`, `$primary`, chọn màu đầu tiên đạt ≥ 3:1.
- Chỉ đổi khi người dùng **chưa** tự đặt màu chữ trong bảng "Aa" của v1.2. Nếu người dùng đã tự đặt thì giữ nguyên lựa chọn của họ, chỉ hiện cảnh báo tương phản như v1.2.
- Hiện một dòng nhỏ: "Đã tự đổi màu chữ để dễ đọc trên nền Vàng".
- Viết logic trong file mới `core/auto_contrast.py`. Lấy màu nền để so sánh là màu ở **mép dưới của dải** (nơi đậm nhất).

---

## 3. Điều chỉnh cụ thể cho từng mẫu

| Mẫu | Layer áp dụng | Thanh trượt | Bảng màu | Mặc định |
|---|---|---|---|---|
| **A · Mờ dần** (`lower_third_fade`) | `bg_fade` | **"Độ đậm vùng mờ"** 0–100%. Dải mờ **tuyến tính**: trong suốt ở mép trên, đậm bằng giá trị thanh trượt ở mép dưới. | 7 chấm: Mặc định (đen) + 6 màu; `gradient_darken: 0` | 95%, đen |
| **B · Chân trang** (`footer_band`) | `bg_band` | **"Độ đậm"** 0–100%, đồng đều cả dải | 7 chấm: Mặc định (màu thương hiệu) + 6 màu; `gradient_darken: 0.25` | 100%, màu thương hiệu |
| **C · Trên + Dưới** (`top_bottom_bars`) | `top_bar` **và** `bottom_bar` | **"Độ đậm"** 0–100%, **một thanh trượt áp đồng nhất cho cả hai thanh**: hai thanh có cùng độ đậm | Không có (giữ nguyên màu) | 90% |

Ghi chú:
- Ở mẫu A, khi độ đậm = 0% thì vạch màu nhấn `accent_bar` và caption vẫn hiển thị. Chỉ nền biến mất.
- Ở mẫu C, thanh dưới đang là gradient màu thương hiệu: khi áp độ đậm thì co giãn alpha theo mục 2.2, không đổi màu.
- Mẫu D (`vertical_9x16_footer`) chưa có điều chỉnh trong bản này.

---

## 4. API và tương thích ngược
- `/api/config`: thêm `version_info`, `templates[].controls`, `palettes`.
- Override `opacity`/`color` cho layer `rect` hoạt động như nhau ở `/api/preview`, `/api/render`, MCP (`overrides`) và CLI (`--overrides`).
- Không gửi override → kết quả **giống hệt v1.2.0**. Viết test so sánh ảnh để chứng minh.

## 5. Danh sách file
- **Mới:** `VERSION`, `core/version.py`, `core/auto_contrast.py`, `config/palettes.json`, `web/static/js/layer-controls.js`, `tests/test_v13_version.py`, `tests/test_v13_layer_controls.py`.
- **Sửa:** `Dockerfile` (1 dòng BUILD_STAMP), `templates/lower_third_fade.json`, `templates/footer_band.json`, `templates/top_bottom_bars.json` (thêm `controls`, sửa điểm đầu dải mờ), `core/overrides.py`, `core/overlay_renderer.py`, `core/colors.py`, `web/server.py`, `web/static/index.html`, `web/static/style.css`, `web/static/app.js` (tối thiểu), `studio_cli.py` (`--version`), `studio_mcp.py` (version), `README.md`, `CHANGELOG.md`.
- **Không đụng:** `ai/*`, `sticker.js`, `text-panel.js`, `web/auth.py`, `web/cleanup.py`, `render.yaml`.

## 6. Giai đoạn (mỗi giai đoạn một commit)
1. **P1 · Nhãn phiên bản:** `VERSION`, `core/version.py`, Dockerfile, API, giao diện, `?v=` chống cache.
2. **P2 · Sửa nền tảng vẽ:** 3 lỗi ở mục 2.2 + helper màu + test so sánh ảnh (không override thì giống v1.2.0).
3. **P3 · Override `opacity`/`color` + `controls` trong 3 template + `palettes.json`.**
4. **P4 · `layer-controls.js`:** thanh trượt, bảng màu, nút Mặc định, nhớ theo mẫu.
5. **P5 · Tự giữ chữ dễ đọc** (`core/auto_contrast.py`) + dòng thông báo.
6. **P6 · Kiểm thử và tài liệu:** chạy toàn bộ test, Playwright ở 390px và 1280px, `VERSION` = 1.3.0, CHANGELOG v1.3.0, README (mục "Tuỳ chỉnh lớp phủ").

## 7. Kiểm thử bắt buộc
| # | Kiểm tra | Kỳ vọng |
|---|---|---|
| T1 | Mẫu A, màu Đỏ, độ đậm 80% | Đo cột pixel giữa khung: alpha tăng **tuyến tính** (sai số ≤ 3/255), tông đỏ không ngả xám/đen ở vùng chuyển tiếp |
| T2 | Mẫu A, độ đậm 0% | Không còn nền, caption và vạch nhấn vẫn hiện |
| T3 | Mẫu B, Vàng, 60% | Dải vàng đậm 60%; chữ tự chuyển `#111111`; màu nhấn không còn trùng vàng |
| T4 | Mẫu C, 50% | Thanh trên và thanh dưới có cùng alpha tối đa = 128 ± 2 |
| T5 | Không override | Ảnh preview của cả 4 mẫu giống v1.2.0 (sai khác pixel ≤ 1) |
| T6 | Preview và video xuất | Cùng thời điểm, cùng màu và độ đậm (sai số ≤ 3/255) |
| T7 | Nhãn phiên bản | Hiện `v1.3.0 · ddmmyyhh` đúng giờ Việt Nam; JS/CSS có `?v=` |
| T8 | Hiệu năng trên Render Free | Kéo thanh trượt không gọi server liên tục; không có "Ran out of memory" |

## 8. Ngoài phạm vi v1.3 (để sau)
- Thanh trượt "Chiều cao vùng mờ" và kiểu đường cong mờ (ease-in / ease-out) cho mẫu A.
- Bảng màu cho mẫu C và mẫu D.
- Lưu bộ màu riêng của thương hiệu vào `brand.json` (mượn Brand Kit của Canva).

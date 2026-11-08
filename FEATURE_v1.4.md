# FEATURE v1.4.0 — Trình chỉnh đối tượng: chọn mới hiện khung, kéo giãn dải chân trang, logo tách ảnh + chữ, thêm chữ tự do

> Dành cho AI coding agent (Antigravity). Code gốc: commit `a879ec5` (v1.3.1).
> Tuân thủ mục 0 của `BUILD_SPEC.md` và **quy tắc tách file**: file quá lớn thì tách theo nhóm đối tượng, nhưng không chia thành quá nhiều file nhỏ không cần thiết. Mỗi giai đoạn (mục 8) một commit.
> Giao diện tiếng Việt. Tên tổ chức viết đầy đủ là **TAIO.CLUB**. Sau khi xong: `VERSION` = `1.4.0` + CHANGELOG.

---

## 0. Mục tiêu

1. **Chỉ đối tượng đang chọn mới hiện khung và tay cầm.** Hiện nay logo luôn hiện tay cầm, gây rối mắt và che hình.
2. **Dải chân trang (mẫu B) kéo giãn được:** kéo mép trên để tăng hoặc giảm chiều cao. Caption nằm trong dải tự di chuyển theo.
3. **Logo là một nhóm gồm 2 đối tượng riêng: Ảnh + Chữ.** Mỗi đối tượng chọn, kéo giãn, xoá, sửa được riêng; nhóm vẫn di chuyển cùng nhau.
4. **Thêm chữ tự do (+ Chữ):** thêm nhiều dòng chữ, chọn font, màu, cỡ và các tuỳ chọn cơ bản.
5. Preview và video xuất vẫn khớp nhau (lệch không quá 2px). Không vượt RAM của Render Free.

## 1. Cơ sở thiết kế (dùng cho marketing sau này)

| Tính năng | Mượn từ app nổi tiếng | Khung lý thuyết |
|---|---|---|
| Chạm để chọn, chạm ra ngoài để bỏ chọn; tay cầm chỉ hiện khi đang chọn | Canva, CapCut, Figma | **Aesthetic & minimalist design** — 10 Usability Heuristics, Jakob Nielsen (1994) |
| Nhóm / Bỏ nhóm; chạm đúp để chọn đối tượng con trong nhóm | Figma, Keynote, Canva "Group" | **Gestalt — Common Region** (Stephen Palmer, 1992): các phần tử nằm chung một vùng được nhận là một nhóm |
| Hoàn tác / Làm lại | Mọi trình chỉnh sửa | **User control & freedom** — Nielsen (1994) |
| Danh sách lớp để chọn đối tượng nhỏ khó chạm | Canva "Layers", CapCut timeline | **Fitts's Law** (Fitts, 1954) |
| Kéo trực tiếp mép dải để đổi chiều cao | Thanh chia khung trong mọi trình chỉnh sửa | **Direct Manipulation** (Shneiderman, 1983) |

## 2. Mô hình dữ liệu: "Scene" gồm các đối tượng

Mở rộng `overrides` của v1.2/v1.3 bằng khoá mới **`objects`**. Không có `objects` thì hoạt động như v1.3.1 (tương thích ngược).

```jsonc
"overrides": {
  "layers": { /* giữ nguyên như v1.3: opacity, color, style... */ },
  "objects": [
    { "id": "logo", "type": "group", "x": 0.80, "y": 0.06, "rotation": 0, "z": 10,
      "pill": { "enabled": true },                       // nền viên thuốc của cả nhóm
      "children": [
        { "id": "logo_img",  "type": "image", "src": "brand|<logo_id>", "dx": -0.06, "dy": 0, "w": 0.07, "visible": true },
        { "id": "logo_text", "type": "text",  "text": "TAIO.CLUB", "dx": 0.04, "dy": 0,
          "style": { "font": "BeVietnamPro", "weight": "Black", "size": 0.035, "color": "#FFFFFF" }, "visible": true }
      ]},
    { "id": "text_1", "type": "text", "text": "Xem đến cuối!", "x": 0.5, "y": 0.2, "rotation": -4, "z": 20,
      "style": { /* xem mục 5 */ } }
  ]
}
```
- **Toạ độ:** `x, y` là tâm, tỉ lệ 0..1 theo khung xuất. Phần tử con dùng `dx, dy` tính từ tâm nhóm, cùng đơn vị. `w` và `size` tính theo chiều rộng khung xuất.
- **`z`:** thứ tự chồng lớp. Layer của template (nền, caption) giữ `z` mặc định thấp hơn đối tượng của người dùng.
- Backend: file mới **`core/scene.py`** gồm `validate_scene()` và `render_objects(overlay, objects, layout, ctx)`, vẽ theo `z` sau các layer template. Vẽ chữ tái sử dụng engine text-style của v1.2. Vẽ ảnh tái sử dụng `layer_blocks.py`.
- Khi template có layer `logo` và scene có đối tượng `id: "logo"` thì **không vẽ layer logo của template nữa**. Scene thay thế hoàn toàn.
- **Chuyển đổi tự động lần đầu:** khi mở mẫu mà chưa có scene, giao diện tạo nhóm `logo` từ layer logo của template (ảnh brand + nhãn `$name`, có pill nếu template có pill). Người dùng thấy giống hệt v1.3.1 nhưng giờ chỉnh được từng phần.

## 3. Chọn đối tượng và tay cầm (áp dụng cho mọi đối tượng)

- **Chạm hoặc click** vào đối tượng → chọn, hiện khung + tay cầm. **Chạm vào chỗ trống**, nhấn `Esc`, hoặc bấm "Xong" → bỏ chọn, ẩn toàn bộ tay cầm.
- **Mặc định khi mở app: không chọn gì.** Logo không còn luôn hiện tay cầm như v1.3.1.
- Máy tính: rê chuột lên đối tượng thì hiện viền mảnh (chưa có tay cầm) để biết bấm vào được.
- **Tay cầm theo loại đối tượng:**

| Đối tượng | Tay cầm |
|---|---|
| Nhóm logo, ảnh, chữ tự do | 4 góc (đổi cỡ, giữ tỉ lệ) + tay cầm xoay; ảnh có thêm 4 cạnh (đổi cỡ tự do, tắt mặc định) |
| Dải chân trang (mẫu B) | **Chỉ mép trên** (kéo lên/xuống). Xem mục 4 |
| Caption | Chưa có trong bản này (giữ vị trí theo template, đi theo dải) |

- Tay cầm ≥ 44×44 px vùng chạm trên điện thoại (hình vẽ có thể nhỏ hơn).
- **Thanh công cụ nổi** hiện phía trên đối tượng đang chọn (kiểu Canva): `Sửa chữ` (với chữ) · `Thay ảnh` (với ảnh) · `Nhân bản` · `Lên lớp / Xuống lớp` · `Bỏ nhóm` (với nhóm) · `🗑 Xoá`.
- **Chọn trong nhóm:** chạm 1 lần chọn cả nhóm; **chạm đúp** (hoặc chạm lần 2 khi nhóm đang chọn) chọn đối tượng con dưới ngón tay. Khi đang chọn đối tượng con, khung nhóm hiện viền nét đứt.
- **Danh sách lớp** (nút "☰ Lớp" cạnh khung preview): liệt kê các đối tượng theo `z`, kèm biểu tượng 👁 ẩn/hiện và nút xoá. Chạm vào tên để chọn. Đây là cách chọn đối tượng nhỏ hoặc bị che.
- **Hoàn tác / Làm lại:** nút ↶ ↷ và phím `Ctrl/Cmd+Z`, `Shift+Ctrl/Cmd+Z`. Lưu tối đa 50 bước (chỉ snapshot JSON của scene).
- **Phím tắt máy tính:** `Delete/Backspace` xoá (khi không đang gõ chữ), mũi tên dịch 1px, `Shift` + mũi tên dịch 10px, `Ctrl/Cmd+D` nhân bản.
- Giữ nguyên đường dóng (smart guides) và vùng an toàn của v1.2, áp dụng cho mọi đối tượng.

## 4. Kéo giãn dải chân trang (mẫu B)

- Chạm vào dải để chọn → hiện **1 tay cầm ở giữa mép trên** (hình viên thuốc ngang) kèm đường mép sáng.
- Kéo lên/xuống để đổi chiều cao. **Mép dưới luôn dính đáy khung.** Giới hạn chiều cao 0.12–0.80 khung, hít vào các mốc 0.25 / 0.33 / 0.44 (mặc định) / 0.50 khi cách ≤ 8px.
- Lưu dưới dạng `overrides.layers.bg_band.h` (và `y = 1 - h`).
- **Caption và logo (nếu đặt trong dải) đi theo dải:** thêm vào template trường `"parent": "bg_band"` cho layer `caption`. Toạ độ của layer con được tính **tương đối trong khung cha**. Dải cao lên → khung caption giãn theo tỉ lệ; chữ tự co như cũ.
- Cơ chế `parent` viết tổng quát trong `core/overrides.py` (hoặc `core/scene.py`) để áp dụng được cho mẫu C (`top_bar`, `bottom_bar`) ở bản sau. Bản này chỉ bật cho mẫu B.
- Thanh trượt "Chiều cao dải" (0–100%) trong bảng điều khiển của mẫu B (khai báo bằng `controls` như v1.3), đồng bộ hai chiều với thao tác kéo.

## 5. Chữ tự do (+ Chữ) và chữ trong logo — cùng một loại đối tượng `text`

- Nút **"+ Chữ"** cạnh nút "Aa". Bấm vào → thêm đối tượng chữ "Nhập chữ…" ở giữa khung, tự chọn và mở ô sửa.
- **Sửa nội dung:** chạm đúp vào chữ (hoặc nút `Sửa chữ`). Điện thoại hiện bottom sheet có ô nhập (không gõ trực tiếp lên ảnh, để bàn phím không che), máy tính hiện ô nhập nổi. Hỗ trợ xuống dòng và cú pháp `**nhấn**` như caption.
- **Bảng tuỳ chọn chữ** (bottom sheet trên điện thoại, tab giống v1.2):
  - Font: danh sách trong `assets/fonts/fonts.json` (đã có từ v1.2) + độ đậm
  - Cỡ chữ: thanh trượt; kéo tay cầm góc cũng đổi cỡ
  - Màu chữ: 6 màu cơ bản (`palettes.json`) + Trắng + Đen + "＋" chọn tự do; màu nhấn
  - Canh lề: trái / giữa / phải
  - Viền chữ (độ dày + màu); bóng đổ (bật/tắt + độ nhoè)
  - Nền chữ: không / khối theo dòng / một khối (màu + độ mờ + bo góc)
  - Độ mờ của cả đối tượng
  - **Kiểu sẵn**: dùng lại `brand/text_styles.json` của v1.2
- Chữ trong nhóm logo (`logo_text`) dùng **đúng bảng này**: đổi nội dung (vd "TAIO.CLUB"), font, màu, cỡ. Ảnh logo (`logo_img`) có `Thay ảnh`, kéo giãn, `Xoá`. Xoá ảnh thì nhóm còn mỗi chữ, và ngược lại. Xoá cả hai thì nhóm tự biến mất.
- **Bỏ nhóm:** ảnh và chữ trở thành 2 đối tượng độc lập ở đúng vị trí cũ. **Nhóm:** trên máy tính chọn nhiều đối tượng bằng Shift + click rồi bấm `Nhóm`; trên điện thoại có thể để bản sau.
- **Giới hạn để giữ nhẹ:** tối đa 10 đối tượng chữ, 3 ảnh mỗi video. Quá giới hạn thì hiện thông báo.

## 6. Hiển thị trong lúc chỉnh (giữ chính xác mà vẫn nhẹ)

- Mỗi đối tượng được hiển thị trên khung preview bằng **ảnh PNG do server vẽ** (`/api/layer-image` mở rộng thành `POST /api/object-image` nhận JSON của 1 đối tượng, trả PNG cạnh dài ≤ 1024px). Nhờ vậy chữ trên màn hình giống hệt chữ trong video (cùng font, cùng engine Pillow).
- **Trong lúc kéo, xoay, đổi cỡ: chỉ biến đổi bằng CSS transform, không gọi server.**
- Khi sửa nội dung, font hoặc màu: gọi `object-image` sau khi dừng 250ms. Trong lúc chờ, hiện tạm bằng chữ DOM có cùng font (nạp font qua `@font-face` từ `assets/fonts`).
- Ảnh preview nền (`/api/preview`) được gọi với `exclude_objects: true` trong khi đang chỉnh. Khi bỏ chọn, gọi một lần ảnh đầy đủ để kiểm tra.
- Cache `object-image` theo hash JSON của đối tượng (LRU tối đa 50 ảnh trên server, xoá khi job bị dọn). Giữ nguyên các giới hạn RAM và semaphore của v1.1.1.

## 7. Tách file frontend (bắt buộc trong bản này)

`web/static/js/sticker.js` (928 dòng) được tách theo trách nhiệm. Mỗi file khoảng 150–350 dòng, không chia nhỏ hơn mức cần thiết:

| File | Trách nhiệm |
|---|---|
| `js/editor/scene-store.js` | Giữ scene (danh sách đối tượng), chọn/bỏ chọn, hoàn tác/làm lại, phát sự kiện thay đổi |
| `js/editor/transform.js` | Kéo, pinch, xoay, tay cầm, quy đổi toạ độ màn hình ⇄ khung xuất, phím mũi tên |
| `js/editor/guides.js` | Đường dóng, vùng an toàn (chuyển từ sticker.js) |
| `js/editor/object-views.js` | Dựng phần tử DOM cho từng loại đối tượng (group / image / text / band handle), nạp ảnh `object-image` |
| `js/editor/toolbar.js` | Thanh công cụ nổi + danh sách lớp |
| `js/editor/text-editor.js` | Bottom sheet sửa nội dung và tuỳ chọn chữ (tái sử dụng phần chung với `text-panel.js`; đưa phần chung vào một hàm dùng chung, không sao chép code) |

Sau khi tách, xoá `sticker.js`. `app.js` chỉ khởi tạo editor và gộp `scene` vào payload preview/render.

## 8. Giai đoạn (mỗi giai đoạn một commit, chạy test xong mới làm tiếp)

1. **P1 · Tách file** `sticker.js` → `js/editor/*` mà **không đổi hành vi**. Chạy lại test v1.2/v1.3: phải đạt hết.
2. **P2 · Chọn / bỏ chọn:** tay cầm chỉ hiện khi chọn, rê chuột hiện viền, Esc, chạm chỗ trống.
3. **P3 · Backend scene:** `core/scene.py`, `objects` trong overrides, `object-image`, cơ chế `parent`, tự chuyển layer logo thành nhóm.
4. **P4 · Dải chân trang kéo giãn** (mẫu B) + thanh trượt "Chiều cao dải" + caption đi theo dải.
5. **P5 · Nhóm logo:** chọn đối tượng con, thay/xoá/kéo giãn ảnh, sửa chữ logo, bỏ nhóm.
6. **P6 · "+ Chữ":** thêm, sửa, tuỳ chọn chữ, nhân bản, xoá, đổi lớp.
7. **P7 · Danh sách lớp + hoàn tác/làm lại + phím tắt.**
8. **P8 · Kiểm thử và tài liệu:** README (mục "Chỉnh đối tượng"), CHANGELOG v1.4.0, `VERSION` = 1.4.0.

## 9. Kiểm thử bắt buộc

| # | Kiểm tra | Kỳ vọng |
|---|---|---|
| T1 | Mở app, chọn mẫu bất kỳ | Không có tay cầm nào hiện. Chạm logo → hiện; chạm chỗ trống → ẩn |
| T2 | Mẫu B, kéo mép trên dải từ 44% lên 60% | Dải cao 60%, mép dưới vẫn ở đáy, caption giãn theo, video xuất khớp preview (≤ 2px) |
| T3 | Chạm đúp chữ "TAIO" trong logo → đổi thành "TAIO.CLUB", font Montserrat, màu vàng | Preview và video đúng nội dung, font, màu; ảnh logo không bị đổi |
| T4 | Chọn ảnh logo → Xoá | Còn lại chữ ở đúng vị trí; Hoàn tác → ảnh quay lại |
| T5 | Bỏ nhóm logo → kéo ảnh và chữ ra 2 góc khác nhau | Video xuất có 2 đối tượng ở đúng 2 vị trí |
| T6 | "+ Chữ" × 3, mỗi chữ một font/màu/góc xoay khác nhau | Hiện đúng thứ tự lớp; đổi lớp có tác dụng; video khớp preview |
| T7 | Điện thoại 390px: chạm vào chữ nhỏ khó trúng | Chọn được qua "☰ Lớp"; kéo không làm cuộn trang |
| T8 | Không gửi `objects` | Ảnh preview 4 mẫu giống v1.3.1 (sai khác ≤ 1 pixel) |
| T9 | Render Free: 10 đối tượng chữ + xuất video 1:30 | Không có "Ran out of memory"; trong lúc kéo không gọi server |
| T10 | Nhãn phiên bản | `v1.4.0 · ddmmyyhh` |

## 10. Ngoài phạm vi v1.4 (để sau)
- Kéo/giãn khung caption tự do; cơ chế `parent` cho mẫu C và D.
- Chọn nhiều đối tượng và nhóm trên điện thoại.
- Thêm ảnh/sticker từ thư viện có sẵn (emoji pack, mũi tên, khung).
- Chữ hiện theo thời gian hoặc có hiệu ứng động.
- Lưu cả scene thành preset dùng lại (cần ổ lưu trữ bền).

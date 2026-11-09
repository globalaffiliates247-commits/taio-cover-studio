# TAIO Cover Studio — FIX v1.6.0 (sửa giao diện chỉnh sửa trên điện thoại)

> Dành cho AI coding agent (Antigravity). Code gốc: commit `34619ee` (v1.5.0).
> Tuân thủ mục 0 của `BUILD_SPEC.md` và quy tắc tách file. Mỗi FIX là một commit, push lên `main`. Xong thì đặt `VERSION` = `1.6.0` và cập nhật CHANGELOG.
> Giao diện tiếng Việt. Tên tổ chức viết đầy đủ là **TAIO.CLUB**.

---

## FIX-1 · Bỏ hàng nút trùng ở mép trên khung preview
- **Hiện tượng:** mép trên khung preview có ↶ ↷ "≡ Lớp", trùng với cột icon bên phải đã có Hoàn tác, Làm lại, Lớp.
- **Sửa:** xoá 3 nút đó khỏi `.preview-top-pills`. Chỉ giữ nhãn độ phân giải ở bên trái (vd `1080×1920 · 0:54`) và nút "Đổi video" ở bên phải. Các phím tắt và hàm undo/redo vẫn nối với cột icon bên phải.
- **File:** `web/static/index.html`, `web/static/css/layout.css`, phần khởi tạo trong `js/layout/quick-rail.js` (nếu đang gắn sự kiện cho nút cũ).

## FIX-2 · Tay cầm quá to và thanh công cụ nổi bị tràn
- **Hiện tượng:** tay cầm ở 4 góc là những vòng tròn trắng khoảng 48px, che mất logo và chữ. Thanh công cụ nổi ("Sửa chữ · Aa Kiểu · Nhân bản · Xoá") có lúc bị cắt ở mép trái hoặc đè lên thanh trên.
- **Sửa tay cầm** (`css/editor.css`, `js/editor/object-views.js`):
  - Phần nhìn thấy: chấm tròn **12px**, nền trắng, viền 2px `#4F8BFF`. Tay cầm xoay: chấm **14px** màu `#FFD34D`, nối với khung bằng đoạn thẳng 1.5px.
  - Phần chạm được: vẫn **44×44px**, tạo bằng pseudo-element trong suốt (`::before { inset: -16px }`) để dễ chạm trên điện thoại mà không che hình.
  - Khung chọn: viền 1.5px `#4F8BFF`. Khung nhóm khi đang chọn đối tượng con: viền nét đứt.
- **Sửa thanh công cụ nổi** (`js/editor/toolbar.js`):
  - Luôn nằm trong khung preview, cách mép 8px.
  - Không đủ chỗ phía trên đối tượng thì hiện xuống phía dưới.
  - Nếu rộng hơn khung thì cuộn ngang được.
  - Không bao giờ đè lên thanh trên hay cột icon bên phải.
- **Nghiệm thu:** trên iPhone 390px, chọn logo ở sát mép trên và chọn chữ ở sát mép trái: tay cầm nhỏ, không che nội dung; thanh công cụ hiện đủ, không bị cắt; chạm trúng tay cầm 10/10 lần.

## FIX-3 · Tab Cap: bỏ nút "+ Chữ" đè lên ô nhập
- **Hiện tượng:** trong tab Cap, nút "+ Chữ" nằm trong ô caption và che chữ gợi ý. Chức năng này đã có ở tab "+ Chữ" và ở cột icon bên phải.
- **Sửa** (`web/static/index.html`, `css/panels.css`):
  - Bỏ nút "+ Chữ" khỏi tab Cap.
  - Ô caption chiếm hết chiều ngang, là ô nhập nhiều dòng (xem FIX-6).
  - Ngay **dưới** ô nhập là một hàng 2 nút: **[Aa Kiểu chữ]** và **[✨ AI]**.
  - Dòng "Màu chữ: …" (xem trước màu nhấn) nằm dưới hàng nút.

## FIX-4 · Nền logo: nút dạng icon và lỗi "Trong mờ" vẫn trông như màu đặc
- **Đổi 3 nút chữ thành 3 nút icon** (nhóm nút segmented), mỗi nút có `aria-label` và `title`:
  - **Không:** icon vòng tròn có gạch chéo ⊘.
  - **Trong mờ:** icon vòng tròn tô nửa / ô caro mờ.
  - **Màu đặc:** icon vòng tròn tô kín.
  - Khi mới chuyển chế độ, hiện tên chế độ trong ~1,5 giây dưới nhóm nút để người dùng biết vừa chọn gì.
- **Nguyên nhân lỗi (đã đọc code):** `core/scene.py` lấy chung `pill.color` và `pill.opacity` cho mọi chế độ. Khi chuyển từ Màu đặc sang Trong mờ, giá trị `opacity = 100` và màu của Màu đặc vẫn còn, nên nền logo vẫn đặc.
- **Sửa** (`core/scene.py`, tab Logo):
  - Lưu giá trị **riêng cho từng chế độ**: `pill.translucent = {opacity}` và `pill.solid = {color, opacity}`. Chuyển chế độ thì dùng giá trị của chế độ đó; quay lại chế độ cũ thì giá trị cũ vẫn còn.
  - **Mặc định của Trong mờ** giống bản ≤ v1.4: nền `#000000` độ đậm 50%, viền `#FFFFFF` độ đậm 25%. Chế độ này **không dùng màu thương hiệu**.
  - **Logo mới mặc định ở chế độ Trong mờ.**
  - Thanh trượt độ đậm hiện ở cả Trong mờ (0–80%) và Màu đặc (0–100%). Bảng màu chỉ hiện ở Màu đặc.
- **Nghiệm thu:** chọn Màu đặc + Xanh → chuyển sang Trong mờ → nền logo thành đen 50% (đo pixel alpha 128 ± 3); chuyển lại Màu đặc → vẫn là Xanh như trước.

## FIX-5 · Chữ tự do: tăng cỡ lên 96 mà chữ không đổi
- **Nguyên nhân (đã đọc code):**
  1. Nút "Aa Kiểu" trên thanh công cụ của chữ tự do gọi `onOpenTextOptions()` trong `js/editor/toolbar.js`, hàm này chỉ bấm hộ nút `#btnOpenTextStyleModal`. Đó là **bảng chữ của caption**, nên bạn đang sửa caption chứ không phải chữ tự do đang chọn.
  2. Hai bên dùng **hai đơn vị khác nhau**: `text-panel.js` tính cỡ theo px (`size: 42`, thanh trượt tới 96), còn đối tượng chữ trong `scene-store.js` / `core/scene.py` tính theo tỉ lệ chiều rộng (`size: 0.045`).
- **Sửa:**
  1. Bảng "Aa Tuỳ chỉnh chữ" nhận tham số **`target`**: `"caption"` hoặc `{objectId}`. Mở từ thanh công cụ của chữ tự do thì `target` là đối tượng đó. Tiêu đề bảng ghi rõ đang chỉnh gì: "Đang chỉnh: Caption" hoặc "Đang chỉnh: Chữ tự do · 'Nhập chữ…'".
  2. **Một đơn vị cỡ chữ cho toàn app:** `size_px` = cỡ chữ tính trên khung rộng **1080px**; khi xuất ở khung rộng hơn hoặc hẹp hơn thì nhân theo tỉ lệ. Chuyển đổi dữ liệu cũ: `size_px = size × 1080` (với `size < 1`). Thanh trượt hiện đúng px này.
  3. Chữ tự do mới có cỡ mặc định **48px**, chế độ cỡ "Cố định". Kéo tay cầm góc cũng cập nhật `size_px` và thanh trượt.
  4. Gom phần chung giữa `text-panel.js` và `js/editor/text-editor.js` vào một module duy nhất. Không chép code ở hai nơi.
- **Nghiệm thu:**
  1. Thêm chữ tự do → Aa Kiểu → cỡ 96 → chữ trên preview và trong video xuất đều to ra tương ứng (đo chiều cao chữ ≈ 96px ở khung 1080).
  2. Caption không bị đổi.
  3. Mở lại bảng thì hiện đúng 96.

## FIX-6 · Tự xuống dòng bằng Enter, không bắt buộc ngắt dòng tự động
- **Yêu cầu:** cả **caption** và **chữ tự do** phải cho người dùng tự bấm Enter để xuống dòng đúng chỗ mình muốn. Hệ thống không được tự ngắt dòng khi chạm khung nếu người dùng không muốn.
- **Sửa:**
  1. Ô nhập caption và ô sửa chữ tự do là **`<textarea>`** tự giãn từ 2 đến 5 dòng. **Enter = xuống dòng** trên cả điện thoại lẫn máy tính, không gửi form.
  2. Giữ nguyên ký tự `\n` xuyên suốt: state, JSON `overrides`, `/api/preview`, render ffmpeg, preset, và sau này là Telegram (v1.7). Cú pháp `**nhấn**` và `==nhấn 2==` vẫn hoạt động, kể cả khi vắt qua nhiều dòng.
  3. Thêm công tắc **"Tự xuống dòng khi chạm khung"** trong bảng Aa (áp dụng cho từng caption hoặc từng chữ tự do). Mặc định:
     - **Bật** nếu nội dung chưa có Enter nào.
     - **Tự tắt** ngay khi người dùng gõ Enter lần đầu. Người dùng vẫn bật lại được.
  4. Khi công tắc **tắt** mà có dòng dài hơn khung:
     - Chế độ cỡ "Tự co vừa khung": thu nhỏ chữ cho tới khi dòng dài nhất vừa khung.
     - Chế độ cỡ "Cố định": giữ cỡ và hiện cảnh báo "Dòng 2 vượt khung — rút ngắn hoặc bật Tự xuống dòng".
  5. Dòng "Màu chữ: …" dưới ô caption hiển thị đúng các chỗ xuống dòng.
- **File:** `core/text_layout.py` (thêm tham số `wrap: bool`), `core/scene.py`, `core/text_style.py`, `web/static/js/...` (module chữ dùng chung ở FIX-5), `web/static/index.html`.
- **Nghiệm thu:**
  1. Caption `THỊ TRƯỜNG CHAO ĐẢO\nKHI NGHE TIN **JENSEN HUANG**` → đúng 2 dòng ở đúng chỗ ngắt, ở cả preview lẫn video.
  2. Bật lại Tự xuống dòng với caption dài không có Enter → tự ngắt như v1.5.

## Kiểm thử chung
| # | Kiểm tra | Kỳ vọng |
|---|---|---|
| T1 | iPhone 390px, mở app | Không còn ↶ ↷ "Lớp" ở mép trên preview; cột icon bên phải đủ chức năng |
| T2 | Chọn logo / chữ ở sát các mép | Tay cầm 12px; thanh công cụ không bị cắt, không đè thanh trên |
| T3 | Tab Cap | Không có nút "+ Chữ"; ô nhập rộng hết, Aa và AI nằm ở hàng dưới |
| T4 | Nền logo Màu đặc → Trong mờ → Màu đặc | Đen 50% ở Trong mờ; quay lại giữ màu cũ |
| T5 | Chữ tự do cỡ 96 | Preview + video đúng cỡ; caption không đổi |
| T6 | Enter trong caption và chữ tự do | Xuống dòng đúng chỗ ở preview và video |
| T7 | Không có thay đổi nào khác | Ảnh preview 4 mẫu với dữ liệu v1.5 giống hệt (sai khác ≤ 1 pixel), ngoại trừ nền logo đã chuyển về Trong mờ mặc định |
| T8 | Nhãn phiên bản | `v1.6.0 · ddmmyyhh` |

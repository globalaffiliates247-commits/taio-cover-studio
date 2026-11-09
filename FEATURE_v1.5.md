# FEATURE v1.5.0 — Chọn mức nén khi xuất · Bố cục tab kiểu CapCut · Preview mượt, không chặn chạm · Nền logo solid · Lưu/chia sẻ trên iPhone · Gửi Telegram 1 chạm

> Dành cho AI coding agent (Antigravity). Code gốc: commit `e093bdd` (v1.4.0).
> Tuân thủ mục 0 của `BUILD_SPEC.md` và **quy tắc tách file**: file quá lớn thì tách theo nhóm chức năng, nhưng không chia quá vụn. Mỗi giai đoạn (mục 9) một commit.
> Giao diện tiếng Việt, tên tổ chức viết đầy đủ là **TAIO.CLUB**. Xong thì đặt `VERSION` = `1.5.0` và cập nhật CHANGELOG.

---

## 1. Popup chọn mức nén khi bấm "Xuất video"

### 1.1 Vì sao cần (đã đo)
Video gốc từ báo điện tử thường đã nén rất mạnh, khoảng 0,4 Mbps. Lệnh hiện tại `-crf 20` giữ chất lượng cố định nên tạo ra khoảng 1,6 Mbps. File 4,6 MB thành 17,9 MB (**gấp 3,9 lần**) mà không đẹp hơn, vì bộ mã hoá tốn dung lượng để giữ lại cả vết nén cũ. Đo thử: CRF 23 kèm giới hạn bitrate theo nguồn chỉ còn **gấp 1,4 lần**.

### 1.2 Ba mức nén — `core/encode_profiles.py` (file mới), `core/compositor.py`, `core/video_probe.py`

| Mức | Dùng khi | CRF | Giới hạn bitrate video (`-maxrate`, `-bufsize` = 2×) |
|---|---|---|---|
| **Nhẹ** | Gửi Telegram, Zalo, xem nhanh | 26 | `max(1.0 × bitrate gốc, sàn)` |
| **Cân bằng** *(mặc định)* | Đăng TikTok, Reels, Facebook | 23 | `max(1.5 × bitrate gốc, sàn)` |
| **Chất lượng cao** | Lưu trữ, đăng YouTube | 20 | `max(3.0 × bitrate gốc, sàn)` |

- **Sàn bitrate** để video không bị vỡ hình: 720p trở xuống 600 kbps, 1080p 1200 kbps. Lưu trong `encode_profiles.py`.
- `video_probe.py`: đọc thêm `bit_rate` của luồng video. Nếu luồng không có thì lấy `format.bit_rate` trừ bitrate âm thanh. Không đọc được thì bỏ giới hạn, chỉ dùng CRF.
- **Giữ `-preset veryfast` cho cả 3 mức.** Như vậy thời gian xử lý trên Render gần như không đổi. `-maxrate` và CRF cao hơn còn giúp xuất nhanh hơn một chút.
- Âm thanh vẫn `-c:a copy`.
- API `/api/render`, MCP và CLI nhận thêm `quality: "light" | "balanced" | "high"` (mặc định `balanced`).

### 1.3 Popup (bottom sheet) — `web/static/js/export/export-sheet.js` (file mới)
- Bấm **Xuất video** → mở sheet có **3 thẻ**. Mỗi thẻ ghi tên mức, dòng mô tả "Dùng khi…", và **dung lượng ước tính**.
- Dung lượng ước tính tính **ngay trên trình duyệt**: `(bitrate video dự kiến + bitrate âm thanh) × thời lượng`. Bitrate dự kiến = `min(maxrate, mức CRF ước lượng theo độ phân giải)`. Ghi rõ "≈ ước tính". **Không gọi server**, nên popup không làm chậm Render.
- Thẻ **Cân bằng được chọn sẵn**, nút "🚀 Xuất" nằm ngay dưới. Người dùng chỉ cần bấm thêm 1 lần.
- Ô "Nhớ lựa chọn, lần sau xuất luôn" (localStorage, bọc try/catch). Khi đã bật: bấm Xuất là xuất ngay, cạnh nút hiện chữ nhỏ "Cân bằng · đổi" để mở lại sheet.
- Chỉ có 3 lựa chọn, theo **Hick's Law** (Hick 1952): mỗi lựa chọn thêm làm người dùng quyết định chậm hơn.

## 2. Bố cục điều khiển dạng tab ngang, kiểu CapCut/TikTok

### 2.1 Mục tiêu
Hiện nay các bảng tuỳ chọn xếp dọc, đẩy nút Xuất xuống thấp, phải cuộn trang. Bản mới: **toàn bộ app nằm gọn trong 1 màn hình (100dvh), không cuộn trang**. Nút Xuất luôn nhìn thấy, ngay dưới khu vực điều khiển.

Cơ sở thiết kế:
- Thanh công cụ dưới của CapCut / TikTok editor.
- **Progressive disclosure** (Nielsen Norman Group): chỉ hiện nhóm chức năng đang dùng.
- **Vùng ngón cái** (Steven Hoober, 2013, *"How Do Users Really Hold Mobile Devices?"*): đặt nút chính ở nửa dưới màn hình, nơi ngón cái dễ chạm.

> **Mockup đã duyệt:** canvas "TAIO Cover Studio v1.5 mockup" (6 khung: tương tác, chọn dải, popup nén, đang tải, xong, máy tính). Khi mockup và văn bản lệch nhau thì làm theo mockup.

### 2.2 Bố cục điện thoại (từ trên xuống)
```
┌ Thanh trên: logo TAIO.CLUB + nhãn phiên bản ·················· Đổi video ┐  ~52px
│ KHUNG PREVIEW (co giãn, chiếm phần còn lại)                  [cột icon] │  flex: 1
│ Thanh tua thời gian (chỉ vùng này nhận thao tác tua)                    │  ~36px
├ Bảng nội dung của tab đang mở (~166px, cuộn bên trong)                  ┤
├ Hàng TAB có icon, cuộn ngang: Mẫu · Nền · Cap · Logo · + Chữ · AI · Lớp ▸┤  ~60px
└ [ Xuất video ]  (dính đáy, có padding safe-area cho iPhone)             ┘  ~80px
```

### 2.2a Tab có icon 2D kiểu CapCut
- Mỗi tab gồm **icon nét 22px phía trên, chữ 11px phía dưới**. Tab đang mở có icon và chữ màu vàng `#FFD34D`, nền cùng màu bảng nội dung, giống ngăn hồ sơ được kéo ra.
- Icon (SVG nét, `stroke="currentColor"`, không dùng emoji): **Mẫu** = khung chia dải · **Nền** = giọt màu · **Cap** = chữ T (caption chính) · **Logo** = huy hiệu tròn · **+ Chữ** = chữ T có dấu + · **AI** = lấp lánh · **Lớp** = 3 tấm xếp chồng.
- Đặt toàn bộ icon trong **một file** `web/static/js/layout/icons.js` (map tên → path SVG), để thanh tab, cột icon và thanh công cụ nổi dùng chung.

### 2.2b Cột icon nổi bên phải khung video kiểu TikTok — `web/static/js/layout/quick-rail.js` (file mới)
- Cột dọc ở mép phải khu preview, nằm khoảng 1/3 dưới. Icon **trắng 28px, không có chữ**, có `drop-shadow` để nổi trên mọi nền. Vùng chạm 44×44px, mỗi nút có `aria-label` và `title`.
- **Khi đang chỉnh:** Hoàn tác · Làm lại · Thêm chữ · Lớp · **Tải xuống** (mở popup chọn mức nén, mục 1.3). Hoàn tác/Làm lại **chuyển từ thanh trên xuống đây**.
- **Sau khi xuất xong:** Lưu / Chia sẻ · Gửi về TAIO.CLUB · Tải MP4 · Chỉnh tiếp.
- **Lần đầu mở app** (lưu cờ trong localStorage, bọc try/catch): hiện chú thích chữ nhỏ bên trái từng icon trong 4 giây hoặc tới khi người dùng chạm bất kỳ đâu, sau đó không hiện lại. Giúp người dùng mới hiểu icon mà vẫn giữ giao diện tối giản.
- Tab ở dạng "ngăn hồ sơ" cuộn ngang (`overflow-x: auto`, `scroll-snap-type: x`). Tab đang mở được làm nổi bật như ngăn hồ sơ kéo ra. Tab bị cắt ở mép phải có viền mờ dần để báo còn tab để cuộn tiếp.
- Bấm tab đang mở lần nữa → thu bảng lại để preview to hơn.
- Nội dung mỗi tab:

| Tab | Nội dung |
|---|---|
| **Mẫu** | 4 thẻ A–D |
| **Nền** | Thanh trượt độ đậm, chiều cao dải, bảng màu (từ `controls` v1.3/v1.4) |
| **Cap** (caption chính) | Ô caption + Kiểu sẵn + "Aa" nâng cao |
| **Logo** | Đổi logo, kiểu nền logo (mục 4), sửa chữ logo |
| **+ Chữ** | Thêm chữ tự do, danh sách chữ đã thêm |
| **AI** | Gợi ý caption |
| **Lớp** | Danh sách mọi đối tượng trên khung, xếp theo thứ tự chồng (trên cùng ở đầu): chữ tự do, nhóm logo (ảnh + chữ), caption, nền. Chạm tên để chọn đối tượng (kể cả đối tượng nhỏ hoặc bị che); 👁 ẩn/hiện; giữ-kéo để đổi thứ tự trên/dưới; nút xoá. Chuyển từ drawer v1.4. |

- Khi đang chọn một đối tượng trên preview, tự mở tab tương ứng (chọn logo → tab Logo; chọn chữ → tab + Chữ).
- Màn hình máy tính (≥ 1024px): preview bên trái kèm cột icon nổi; bên phải là hàng tab có icon (ngăn mở xuống) + bảng nội dung, nút Xuất dính đáy cột phải, dưới nút ghi "Mức nén: Cân bằng · đổi".
- Sau khi xuất xong: khu dưới chỉ còn **thanh tiến độ tải + 1 nút chính "Lưu / Chia sẻ" + "Chỉnh tiếp"**. Gửi TAIO.CLUB và Tải MP4 nằm ở cột icon bên phải (mục 2.2b).

### 2.3 Tách file (bắt buộc)
- `web/static/app.js` (979 dòng) và `web/static/style.css` (1755 dòng) đều quá lớn.
- JS mới: `js/layout/tabs.js` (hàng tab + bảng), `js/layout/icons.js`, `js/layout/quick-rail.js`, `js/export/export-sheet.js`, `js/export/result-actions.js` (Lưu / Telegram / Tải sau khi xuất), `js/preview/preview-engine.js` (mục 3). `app.js` chỉ còn khởi tạo và nối các module, mục tiêu < 400 dòng.
- CSS tách thành `css/base.css`, `css/layout.css`, `css/editor.css`, `css/panels.css`, `css/sheets.css`. Tất cả nạp kèm `?v=<build>`.

## 3. Preview mượt và không chặn chạm

### 3.1 Nguyên nhân (đã đọc code)
1. **Mỗi lần nhấc ngón tay đều gọi server.** Trong `js/editor/transform.js`, hàm `onPointerUp` **luôn** gọi `recordSnapshot()` và `notifyChange()`, kể cả khi chỉ chạm để chọn chứ không kéo. Kết quả là `debouncedPreview()` → `/api/preview` chạy mỗi lần chạm.
2. **Lớp "Đang cập nhật…" phủ kín và chặn chạm.** `.preview-spinner-overlay` có `inset: 0; z-index: 10`, không có `pointer-events: none`, lại hiện ở mỗi lần gọi preview. Cú chạm thứ hai của thao tác chạm đúp (để sửa chữ logo) rơi vào lớp phủ này, nên **không mở được ô sửa chữ**.
3. Từ v1.4, đối tượng (logo, chữ) đã được vẽ bằng DOM, nhưng di chuyển chúng vẫn khiến server vẽ lại cả khung hình.

### 3.2 Sửa
1. **Chỉ báo thay đổi khi scene thật sự đổi.** So sánh hash JSON của scene trước và sau khi nhấc tay. Chạm để chọn, hoặc kéo dưới 3px, thì không ghi lịch sử và không gọi server.
2. **Di chuyển, xoay, đổi cỡ đối tượng → không gọi `/api/preview`.** Đối tượng đã hiển thị bằng ảnh `object-image` (v1.4), nên chỉ cần CSS transform. `/api/preview` chỉ được gọi khi đổi **mẫu, caption, kiểu chữ caption, thông số nền, logo template, hoặc thời điểm tua**.
3. **Spinner không chặn chạm:** đổi thành vòng xoay nhỏ ở góc khung preview, có `pointer-events: none`. **Giữ nguyên ảnh cũ** cho tới khi ảnh mới về, không phủ đen cả khung.
4. **Chỉ thanh tua nhận thao tác tua.** Thao tác trên vùng ảnh preview chỉ dùng để chọn hoặc kéo đối tượng.

### 3.3 Cache ở trình duyệt — `js/preview/preview-engine.js` (file mới)
1. **Cache ảnh preview** theo khoá `hash(template + overrides không gồm objects + caption + t làm tròn 0,1s)`. Dùng `Map` LRU tối đa 40 ảnh (blob URL); khi xoá khỏi cache thì gọi `revokeObjectURL`. Quay lại trạng thái đã xem → hiện ngay, không gọi server.
2. **Tua thời gian mượt:** khi tua, hiện ngay khung hình từ **video gốc phát tại chỗ** (thẻ `<video>` dùng `URL.createObjectURL(file)` nếu video được chọn từ máy; nếu dán link thì dùng `/api/video/<id>` có hỗ trợ HTTP Range để trình duyệt tự cache). Ảnh lớp phủ của khung hình cũ tạm hiện chồng lên. Chỉ khi dừng tua 300ms mới gọi `/api/preview` để lấy ảnh chính xác.
3. **(Nên có) Tách lớp phủ khỏi khung hình:** endpoint mới `POST /api/overlay-image` trả **PNG trong suốt chỉ chứa lớp phủ template** (nền, caption) cùng thông tin bố cục (vị trí video trong khung). Trình duyệt ghép PNG này lên `<video>` tại chỗ. Khi đó tua thời gian **không cần gọi server**; chỉ gọi lại khi lớp phủ đổi. Mẫu D (nền mờ) dùng CSS `filter: blur()` để xem trước, ảnh chính xác vẫn từ server khi dừng. Nếu phần này phức tạp thì làm sau 3.2 và 3.3.1, ghi rõ trong CHANGELOG.
- **Nghiệm thu:**
  1. Chạm đúp chữ logo trên iPhone mở được ô sửa chữ 10/10 lần.
  2. Chạm hoặc chọn đối tượng không hiện spinner, không phát sinh request `/api/preview` (kiểm tra bằng Playwright đếm request).
  3. Kéo logo 10 lần → 0 request `/api/preview`.
  4. Tua qua lại đã có cache → không có request mới.

## 4. Nền của logo: thêm chế độ màu đặc (solid) — `core/scene.py`, tab Logo

- `pill.mode`: `"none"` (không nền) · `"translucent"` (trong mờ, như hiện tại) · **`"solid"`** (màu đặc).
- `pill.color` (mặc định màu thương hiệu), `pill.opacity` (0–100%, mặc định 100% cho solid và 50% cho trong mờ), `pill.stroke` (viền bật/tắt + màu), `pill.radius` (`full` bo tròn hẳn, hoặc số).
- Giao diện ở tab Logo: hàng 3 nút **Không · Trong mờ · Màu đặc**. Chọn Màu đặc thì hiện bảng màu (Mặc định thương hiệu + 6 màu cơ bản + Trắng + Đen + "＋") và thanh trượt độ đậm.
- Tự giữ chữ logo dễ đọc khi chọn nền màu sáng: dùng lại `core/auto_contrast.py` của v1.3.
- Gọi đúng tên là **"Trong mờ"**: hiện tại nền chỉ là màu bán trong suốt, không làm nhoè hình phía sau. Không đặt tên "kính mờ" để tránh hiểu nhầm.

## 5. Lưu và chia sẻ trên iPhone

### 5.1 Nguyên nhân "Video đang được chuẩn bị" dù đã 100% (đã đọc code)
1. 100% là tiến độ **xuất trên server**. Sau đó trình duyệt còn phải **tải file về điện thoại** (17,9 MB qua Render Free và 4G) nhưng không có thanh tiến độ cho bước này.
2. **File bị tải 2 lần cùng lúc:** `save-photos.js` tải trước để lưu, đồng thời `playerResultVideo.src = downloadUrl` cũng tải lại file đó để phát thử. Hai luồng tranh băng thông nên càng chậm.

### 5.2 Sửa — `js/export/result-actions.js`, `js/save-photos.js`
1. **Chỉ tải một lần:** tải bằng `fetch` + đọc stream để hiện tiến độ "Đang tải về điện thoại… 42%" (dùng `Content-Length`). Xong thì tạo blob, rồi gán `playerResultVideo.src = blobURL`, không gọi URL server lần nữa.
2. Mức nén **Cân bằng/Nhẹ** (mục 1) làm file nhỏ hơn 2–3 lần nên cũng tải nhanh hơn.
3. **Gộp thành một nút "📤 Lưu / Chia sẻ"** mở bảng chia sẻ của iOS (`navigator.share({files})`). Trong bảng có sẵn **"Lưu video"** (vào Ảnh), **"Lưu vào Tệp"** (người dùng chọn thư mục bất kỳ, kể cả iCloud Drive), AirDrop, Telegram, Zalo…
4. **Giới hạn của iOS, ghi rõ trong app:** web app không tự chọn được thư mục lưu mặc định. Nút "Tải MP4" của Chrome iOS luôn lưu vào *Tệp → Trên iPhone → Chrome*. Khi người dùng bấm "Tải MP4" trên iPhone, hiện dòng gợi ý: "Muốn lưu vào thư mục khác hoặc vào Ảnh, hãy dùng **Lưu / Chia sẻ**."
5. Máy tính giữ nguyên tải MP4 trong cùng tab như v1.3.1.

## 6. Gửi Telegram 1 chạm về bot của admin

- **Bỏ modal và ô nhập Chat ID.** Icon **✈ Gửi về TAIO.CLUB** ở cột icon bên phải (mục 2.2b) gửi video ngay tới chat của admin, cấu hình trên server bằng `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`.
- **Nội dung tin nhắn kèm video:** caption của video, tên file, mẫu đã dùng, mức nén, dung lượng, thời gian (giờ Việt Nam) và phiên bản app.
- **Ô "Ghi chú cho admin" (tuỳ chọn):** một dòng chữ nhỏ có thể bỏ trống, ví dụ tên hoặc số điện thoại người cần nhận lại. Ẩn sau link "+ thêm ghi chú" để giữ thao tác 1 chạm.
- **Chống spam:** mỗi job chỉ gửi 1 lần; tối đa 20 lần/giờ cho mỗi IP. Vượt giới hạn thì báo bằng tiếng Việt.
- **Giới hạn dung lượng:** bot Telegram chỉ gửi được file tối đa ~50 MB. File lớn hơn thì báo "Video quá lớn để gửi Telegram — hãy xuất lại ở mức Nhẹ" và có nút làm việc đó ngay.
- Server chưa cấu hình token hoặc chat ID → **ẩn nút** Gửi về TAIO.CLUB, không hiện lỗi cho người dùng.
- Xoá mọi đoạn code còn đọc hoặc ghi token/chat ID trong localStorage.

## 7. Danh sách file
- **Mới:** `core/encode_profiles.py`, `web/static/js/layout/tabs.js`, `web/static/js/layout/icons.js`, `web/static/js/layout/quick-rail.js`, `web/static/js/export/export-sheet.js`, `web/static/js/export/result-actions.js`, `web/static/js/preview/preview-engine.js`, `web/static/css/{base,layout,editor,panels,sheets}.css`, `tests/test_v15_encode.py`, `tests/test_v15_preview_requests.py`.
- **Sửa:** `core/compositor.py`, `core/video_probe.py`, `core/scene.py`, `web/server.py` (quality, `/api/video/<id>` có Range, `/api/overlay-image` nếu làm 3.3.3, telegram), `web/static/app.js` (thu gọn), `web/static/index.html`, `web/static/js/editor/transform.js`, `web/static/js/editor/scene-store.js`, `web/static/js/save-photos.js`, `studio_cli.py`, `studio_mcp.py`, `README.md`, `CHANGELOG.md`, `VERSION`.
- **Xoá:** `web/static/style.css` (đã tách), modal Telegram trong `index.html`.

## 8. Ràng buộc
- Giữ nguyên toàn bộ giới hạn luồng ffmpeg và semaphore của v1.1.1.
- Không có thao tác nào trong lúc kéo hoặc chạm gọi `/api/preview`.
- Mọi localStorage bọc try/catch.

## 9. Giai đoạn (mỗi giai đoạn một commit)
1. **P1 · Sửa chạm và spinner** (mục 3.1–3.2). Sửa nhỏ, nhiều tác dụng nên làm trước.
2. **P2 · Mức nén** ở backend + popup chọn mức (mục 1).
3. **P3 · Tải một lần + Lưu / Chia sẻ + tiến độ tải** (mục 5).
4. **P4 · Gửi Telegram 1 chạm** (mục 6).
5. **P5 · Nền logo solid** (mục 4).
6. **P6 · Tách CSS/JS + bố cục tab ngang** (mục 2). Làm sau cùng phần giao diện vì đụng nhiều file nhất.
7. **P7 · Cache preview + tua mượt** (mục 3.3.1–3.3.2), rồi 3.3.3 nếu kịp.
8. **P8 · Kiểm thử và tài liệu:** bảng mục 10, README, CHANGELOG, `VERSION` = 1.5.0.

## 10. Kiểm thử bắt buộc
| # | Kiểm tra | Kỳ vọng |
|---|---|---|
| T1 | Video nguồn ~0,42 Mbps, 1:28, mức Cân bằng | Kết quả ≤ 1,6 lần dung lượng gốc; mức Nhẹ ≤ 1,2 lần; mức Chất lượng cao không bị giới hạn khi nguồn có bitrate cao |
| T2 | Thời gian xuất trên Render Free ở mức Cân bằng so với v1.4.0 | Không chậm hơn (sai số ±10%) |
| T3 | iPhone 390×844: mở app, chọn video | Không phải cuộn trang; nút Xuất luôn hiện; hàng tab có icon cuộn ngang được; cột icon bên phải hiện đủ 5 nút, bấm Tải xuống mở popup nén; lần đầu có chú thích 4 giây rồi tự ẩn |
| T4 | Chạm đúp chữ logo 10 lần | Mở ô sửa chữ 10/10 lần; 0 request `/api/preview` khi chỉ chạm/chọn |
| T5 | Kéo logo, chữ tự do 10 lần | 0 request `/api/preview`; video xuất đúng vị trí |
| T6 | Tua tới một mốc đã xem | Ảnh hiện ngay từ cache, không có request mới |
| T7 | Xuất xong trên iPhone | Có tiến độ "Đang tải về điện thoại…"; file chỉ tải 1 lần (đếm request `/api/download`); Lưu / Chia sẻ có "Lưu video" và "Lưu vào Tệp" |
| T8 | Gửi về TAIO.CLUB | Không có ô nhập; admin nhận video kèm caption, thời gian, phiên bản; gửi lần 2 cùng job bị chặn |
| T9 | Logo nền Màu đặc, Vàng, 100% | Nền vàng đặc; chữ logo tự chuyển màu tối; video khớp preview |
| T10 | Nhãn phiên bản | `v1.5.0 · ddmmyyhh` |

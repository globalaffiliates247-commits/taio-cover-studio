# FIX v1.3.1 — "Lưu vào Cuộn Camera" trên iPhone mở tab about:blank và tải MP4 thay vì lưu vào Ảnh

> Dành cho AI coding agent (Antigravity). Code gốc: commit `a0fa64a` (v1.3.0).
> Chỉ sửa đúng các file liệt kê. Mỗi FIX một commit. Sau khi xong, tăng `VERSION` lên `1.3.1` và ghi CHANGELOG.

## A. Chẩn đoán (đã đọc code, đừng đoán lại)

`saveVideoToPhotos()` trong `web/static/app.js` **không đổi từ v1.1.0**. Trình tự hiện tại:

```
click → await fetch(/api/download/...) → await resp.blob() → navigator.share({files})
                                                   ↘ lỗi → catch → window.open(downloadUrl, "_blank")
```

1. **iOS (Safari và Chrome iOS đều dùng WebKit) chỉ cho gọi `navigator.share()` trong "transient user activation"**, tức là ngay sau cú chạm. Việc tải video qua mạng trước khi gọi `share` có thể vượt quá khoảng thời gian này, nhất là trên 4G, Render Free hoặc video lớn. Khi đó `share()` ném `NotAllowedError`.
2. Khối `catch` bắt **mọi lỗi khác `AbortError`** rồi gọi `window.open(downloadUrl, "_blank")`. URL này trả về file kèm header tải xuống, nên iOS mở một tab **about:blank** và tải MP4 vào Downloads/Files. Kết quả là video không vào Ảnh.
3. Lỗi không ổn định: mạng nhanh thì chạy được (như bản trước), mạng chậm thì hỏng. Đó là lý do người dùng thấy "phiên bản trước được, bản này không".

## B. Danh sách sửa

### FIX-1 · Tải sẵn video ngay khi xuất xong — `web/static/js/save-photos.js` (file mới), `web/static/app.js` (tối thiểu)
- Tách toàn bộ logic lưu vào Ảnh sang **file mới `save-photos.js`**. Trong `app.js` chỉ giữ lời gọi khởi tạo và lời gọi `prepareResultFile(jobId, filename)` khi job chuyển sang `done`.
- Khi job `done`: **tải sẵn** video về bộ nhớ trình duyệt (`fetch` → `blob` → `new File([blob], name, {type: "video/mp4"})`), lưu vào `state.resultFile`. Trong lúc tải, nút hiện "⏳ Đang chuẩn bị video…" và bị vô hiệu hoá; xong thì đổi thành "📱 Lưu vào Cuộn Camera".
- Kiểm tra `resp.ok` và `blob.type`/kích thước. Nếu server trả lỗi JSON (vd job đã mất sau khi Render khởi động lại) thì không tạo File giả; hiện thông báo và nút Xuất lại (dùng cơ chế FIX-5/6 của v1.1.1).

### FIX-2 · Gọi share ngay trong cú chạm — `web/static/js/save-photos.js`
- Trong handler click: **lệnh đầu tiên phải là `navigator.share({ files: [state.resultFile] })`**. Không được có `await` nào (fetch, blob, setTimeout…) trước lệnh này.
- Kiểm tra trước bằng `navigator.canShare({ files: [file] })`, đồng bộ, không chờ.
- Nếu `state.resultFile` chưa sẵn sàng (người dùng bấm quá sớm): **không gọi share sau khi chờ**. Chỉ hiện "Video đang được chuẩn bị, bấm lại sau giây lát".

### FIX-3 · Bỏ nhánh `window.open` gây ra tab about:blank — `web/static/js/save-photos.js`
Xử lý theo từng loại lỗi, **tuyệt đối không mở tab mới**:

| Trường hợp | Xử lý |
|---|---|
| `AbortError` (người dùng đóng bảng chia sẻ) | Im lặng, trả nút về trạng thái thường |
| `NotAllowedError` | Hiện "Bấm lại nút Lưu một lần nữa"; giữ nguyên `state.resultFile` để lần bấm sau gọi share ngay |
| Trình duyệt không hỗ trợ chia sẻ file (`canShare` = false, vd máy tính) | Tải xuống bằng `<a href=blobURL download=name>` **trong cùng tab**. Trên iOS mà không có share thì hiện hướng dẫn: "Chạm giữ vào video đang phát → Lưu video" (video kết quả đã có sẵn trong khung preview) |
| Lỗi khác | Hiện tên lỗi (`e.name`) trong dòng trạng thái nhỏ để dễ chẩn đoán |

- Ghi `console.info("[save-photos]", e.name, e.message)` để xem được log khi gỡ lỗi từ xa.

### FIX-4 · Giải phóng bộ nhớ — `web/static/js/save-photos.js`
- Khi người dùng đổi video, xuất bản mới hoặc rời trang: xoá `state.resultFile` và gọi `URL.revokeObjectURL` cho blob URL đã tạo.
- Không lưu file vào localStorage hay IndexedDB.

## C. Kiểm thử
1. **iPhone, Safari và Chrome iOS, mạng 4G** (hoặc giả lập mạng chậm trong DevTools: "Slow 3G"): xuất video → đợi nút đổi thành "Lưu vào Cuộn Camera" → bấm → **bảng chia sẻ iOS hiện ra, có mục "Lưu video"** → video nằm trong app Ảnh. Không có tab about:blank.
2. Bấm Lưu khi video còn đang chuẩn bị → hiện thông báo chờ, không mở tab, không tải file.
3. Đóng bảng chia sẻ (huỷ) → không có thông báo lỗi; bấm lại vẫn mở được bảng chia sẻ.
4. Chrome trên Mac (không hỗ trợ chia sẻ file) → tải MP4 xuống trong cùng tab, đúng tên file.
5. Playwright: giả lập `navigator.share` ném `NotAllowedError` → kiểm tra `window.open` **không** được gọi.
6. Nhãn phiên bản hiện `v1.3.1 · ddmmyyhh` sau khi deploy.

## D. Danh sách file
- **Mới:** `web/static/js/save-photos.js`
- **Sửa:** `web/static/app.js` (xoá hàm cũ, gọi module mới), `web/static/index.html` (nạp script, kèm `?v=`), `VERSION`, `CHANGELOG.md`
- **Không đụng:** backend, templates, các module JS khác.

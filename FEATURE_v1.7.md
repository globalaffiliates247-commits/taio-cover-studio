# TAIO Cover Studio — FEATURE v1.7.0 (Bot Telegram + Preset JSON + máy Mac xử lý video)

> Dành cho AI coding agent (Antigravity). Code gốc: bản **v1.6.0** (làm sau `FIX v1.6`).
> Tuân thủ mục 0 của `BUILD_SPEC.md` và quy tắc tách file. Mỗi giai đoạn (mục 10) một commit, push lên `main`. Xong thì đặt `VERSION` = `1.7.0` và cập nhật CHANGELOG.
> Giao diện và tin nhắn bot bằng tiếng Việt. Tên tổ chức viết đầy đủ là **TAIO.CLUB**.

---

## 0. Các quyết định chủ dự án đã chốt

| # | Câu hỏi | Chốt |
|---|---|---|
| 1 | Bot chạy ở đâu | **Cả hai:** Render nhận tin và điều phối; Mac xử lý video khi đang bật |
| 2 | Lưu preset và cài đặt | **Preset mặc định trong repo** + **cài đặt lúc chạy lưu trong một kênh Telegram riêng** (0đ) |
| 3 | Ai được dùng bot | **Chỉ admin** |
| 4 | Duyệt preview trước khi xuất | **Luôn luôn** |
| 5 | Bot nào | **Bot đang có** của admin |
| 6 | Video lớn hơn 20 MB | **Xử lý trên Mac** |

> ⚠ **Điều kiện bắt buộc trước khi bắt đầu:** mỗi bot Telegram chỉ có **một nơi nhận tin** (một webhook hoặc một tiến trình polling). Bot được chọn **không được đang nối với OpenClaw hay bất kỳ dịch vụ nào khác**. Ở P1, chạy `getWebhookInfo` để kiểm tra rồi báo cho chủ dự án. Nếu bot đang bị dùng, dừng lại và hỏi nên chọn bot khác hay gỡ kết nối cũ.

## 1. Kiến trúc: Hub trên Render + Worker trên Mac

```
 Admin (Telegram) ──video / lệnh──▶  HUB (Render, webhook)                      WORKER (Mac, studio_worker.py)
                                    ├ bot/: lệnh, /menu, nút duyệt              ├ hỏi Hub có việc không (long-poll)
                                    ├ core/presets.py: ghép cấu hình theo tầng  ├ tải video gốc qua MTProto (≤ 2 GB)
                                    ├ storage/: repo + kênh Telegram lưu trữ     ├ render bằng core/ (CPU mạnh)
                                    ├ hàng đợi job + chọn máy xử lý             ├ gửi video kết quả qua MTProto (≤ 2 GB)
                                    └ render dự phòng (≤ 20 MB, khi Mac tắt)     └ báo tiến độ / heartbeat về Hub
```
- **Hub là nơi duy nhất ghi cấu hình** (single writer). Worker không đọc kho lưu trữ: mỗi job Hub gửi kèm **cấu hình đã ghép xong**.
- **Chọn máy xử lý cho mỗi job:**
  1. Mac online (có heartbeat trong vòng 45 giây) → Mac xử lý.
  2. Mac offline và video ≤ 20 MB → Render xử lý (Bot API thường).
  3. Mac offline và video > 20 MB → job chờ; bot báo "Video lớn, sẽ xử lý khi máy Mac bật". Admin có thể huỷ.
  4. `/menu → Máy xử lý` cho chọn `Tự động` (mặc định) / `Chỉ Mac` / `Chỉ Render`.
- **Nhận tin từ Telegram:** webhook `POST /tg/webhook`, kiểm tra header `X-Telegram-Bot-Api-Secret-Token`. Nhận xong **trả 200 ngay**, việc xử lý chạy nền. Chống xử lý trùng theo `update_id` (nhớ 500 id gần nhất). Đây là cách để Render Free thức dậy khi có tin mà không cần tiến trình chạy liên tục.
- **Gọi Bot API:** dùng HTTP trực tiếp (`bot/tg_api.py`), không thêm framework bot, để giữ RAM thấp.
- **Worker trên Mac dùng Telethon** (MTProto, giấy phép MIT, còn được bảo trì), đăng nhập bằng **bot token** + `TG_API_ID`/`TG_API_HASH` (lấy tại my.telegram.org). Worker **không nhận update** từ Telegram, chỉ tải và gửi file. Tải video theo `chat_id` + `message_id` do Hub gửi sang (`get_messages` → `download_media`), không dùng `file_id` của Bot API.

## 2. P1 là bước thử nghiệm kỹ thuật bắt buộc (spike, làm trước mọi thứ khác)
Viết script nhỏ `tools/spike_mtproto.py` để chứng minh 3 điều sau khi webhook của Hub đang bật:
1. Telethon đăng nhập bằng bot token **không làm webhook ngừng nhận tin** (gửi thử 5 tin, Hub vẫn nhận đủ).
2. Tải được video **> 20 MB** mà admin gửi cho bot, bằng `chat_id` + `message_id`.
3. Gửi lại được video **> 50 MB** vào chat admin.

Nếu có điểm nào không đạt: **dừng lại, báo chủ dự án**, kèm phương án thay thế. Phương án thay thế là chạy Telegram Bot API server riêng trên Mac. Cách đó buộc bot chỉ nhận tin khi Mac bật (không dùng được webhook trên Render), nên chủ dự án phải đồng ý mới được làm.

## 3. Cấu hình theo tầng (mượn cách `git config` chia system / global / local)
Thứ tự ghép, tầng sau ghi đè tầng trước. Viết trong `core/presets.py`, hàm `resolve_config(chat_id, message) -> dict`:
1. **Mặc định hệ thống:** template + brand kit trong code.
2. **Preset:** preset đang chọn của chat. Có thể là preset có sẵn trong repo (`presets/*.json`) hoặc preset người dùng tải lên (trong kênh lưu trữ).
3. **Cài đặt riêng của chat:** các thay đổi lẻ làm qua `/menu` hoặc `/set`.
4. **Thông số của riêng tin nhắn:** phần chú thích gửi kèm video là caption chính (giữ nguyên Enter `\n` và `**nhấn**`).

Lệnh `/get` hiển thị giá trị cuối cùng kèm **nguồn của nó**, ví dụ `nen.opacity = 0.6 (từ /menu)` hay `template = footer_band (từ preset Tin nóng)`. Cách này giúp hiểu vì sao kết quả ra như vậy.

## 4. Preset JSON
- File schema: `config/preset.schema.json` (JSON Schema draft 2020-12). Kiểm tra ở server trước khi lưu, dung lượng tối đa 64 KB. Sai cấu trúc thì báo lỗi tiếng Việt kèm đường dẫn trường bị sai.
- Ví dụ:
```json
{
  "schema": "taio.cover.preset/1",
  "name": "tin_nong",
  "label": "Tin nóng",
  "template": "lower_third_fade",
  "overrides": { "layers": { "bg_fade": { "opacity": 0.95, "color": null } }, "objects": [] },
  "caption": { "source": "message", "fallback": "ask", "style": { "preset": "Tin nóng", "wrap": true } },
  "logo": { "asset": "brand", "pill": { "mode": "translucent" } },
  "quality": "balanced",
  "approval": "always"
}
```
- `caption.source`: `message` (lấy từ chú thích video) · `fixed` (dùng `caption.text`) · `ai` (AI gợi ý, admin chọn).
- `caption.fallback` (khi video không có chú thích): `ask` (bot hỏi) · `ai` · `empty`.
- `overrides` **dùng đúng định dạng của web app** (v1.2–v1.6). Nhờ vậy thiết kế trên web xong là thành preset dùng được cho bot.
- Preset chỉ được trỏ tới logo bằng **ID tài nguyên**, không nhận đường dẫn file.

## 5. Kho lưu trữ (lựa chọn 2C) — `storage/`
- Viết theo kiểu **adapter** (`storage/base.py`) để sau này đổi sang cơ sở dữ liệu mà không phải sửa phần khác.
- **`storage/repo_presets.py`:** đọc `presets/*.json` trong repo, chỉ đọc. Có sẵn 4 preset mặc định, tương ứng 4 mẫu A–D.
- **`storage/telegram_channel.py`:** lưu trong một **kênh Telegram riêng tư** (ví dụ "TAIO Cover Storage") mà bot là admin. Biến môi trường: `TG_STORAGE_CHANNEL_ID`.
  - Mỗi bản ghi (`settings.json` của từng chat, preset người dùng, logo) là một **file tài liệu** gửi vào kênh.
  - Một **tin nhắn chỉ mục được ghim** chứa JSON `{ tên: {file_id, version, updated_at} }`.
  - **Khi khởi động:** đọc tin ghim → tải các file → giữ trong RAM.
  - **Khi ghi:** gửi file mới → sửa tin chỉ mục. Gộp các lần ghi gần nhau trong 2 giây. Giữ 5 phiên bản gần nhất của mỗi bản ghi để khôi phục khi cần (`/restore`).
  - Nếu kênh lưu trữ không truy cập được: bot vẫn chạy bằng preset trong repo và báo admin một lần.

## 6. Trải nghiệm trên bot

### 6.1 Gửi video và duyệt
1. Admin gửi **video** (kèm chú thích làm caption nếu muốn) hoặc **link video**.
2. Bot trả lời ngay: "Đã nhận ✓ · Xử lý trên: Mac / Render / chờ Mac".
3. Bot gửi **ảnh preview** theo cấu hình đã ghép, kèm các nút bấm:
   `[✅ Xuất] [✏️ Caption] [🎨 Mẫu] [🤖 AI] [⚙️ Nén] [✖ Huỷ]`
   - Mỗi lần sửa thì **cập nhật chính ảnh đó** (`editMessageMedia`), không gửi thêm tin mới.
   - **✏️ Caption:** bot hỏi lại bằng ForceReply. Admin gõ nhiều dòng tuỳ ý, giữ nguyên chỗ Enter.
   - **🤖 AI:** hiện 5 gợi ý dạng nút, bấm để chọn.
4. **Bấm ✅ Xuất:** job vào hàng đợi. Bot sửa dòng trạng thái theo tiến độ ("Đang xuất trên Mac… 40%"), tối đa 1 lần cập nhật mỗi 3 giây.
5. **Kết quả:**
   - Xuất trên Mac: gửi video qua MTProto (≤ 2 GB).
   - Xuất trên Render: video ≤ 50 MB thì gửi file, lớn hơn thì gửi link `/api/download`.
   - Kèm dòng thông tin: mẫu, mức nén, dung lượng, máy xử lý, phiên bản app.

### 6.2 `/menu` — mượn kiểu `/mybots` của BotFather
- **Màn hình đầu là thẻ tóm tắt cấu hình**, bên dưới là các nút: `Mẫu · Nền · Cap · Logo · Mức nén · Preset · Máy xử lý`.
- **Mỗi màn hình tối đa 6 nút** (Hick's Law). Người dùng bấm nút chọn thay vì phải nhớ lệnh (nguyên tắc "Recognition rather than recall" của Nielsen). Luôn có nút "⬅ Quay lại".
- **Thông số dạng số:** nút `−` / `+` theo bước cố định, kèm nút "Nhập số" (bot hỏi lại bằng ForceReply).
- **Màu:** 6 màu cơ bản + Mặc định, giống bảng màu trên web.
- **Preset:** Chọn preset · Lưu cấu hình hiện tại thành preset mới · Xuất file JSON · Nhập (gửi file `.json` cho bot) · Xoá.
- `callback_data` mã hoá ngắn, tối đa 64 byte (ví dụ `m:nen:op:+`).

### 6.3 Lệnh (đăng ký bằng `setMyCommands` khi khởi động)
`/start` · `/menu` · `/presets` · `/preset <tên>` · `/set <đường dẫn> <giá trị>` (vd `/set nen.opacity 0.6`) · `/get [đường dẫn]` · `/reset` · `/export` · `/import` (gửi kèm file .json) · `/restore` · `/status` (Mac online? hàng đợi?) · `/help`

### 6.4 Chỉ admin
- Biến môi trường `TELEGRAM_ADMIN_IDS` (danh sách ID, cách nhau bằng dấu phẩy).
- Người không phải admin: bot trả một câu lịch sự "Bot đang ở chế độ riêng tư" rồi bỏ qua mọi tin sau của người đó trong 24 giờ, để không bị spam.

## 7. Web app (bổ sung)
- **Lưu thành preset:** trong popup chọn mức nén (v1.5) thêm nút "💾 Lưu thành preset cho bot". Lưu nguyên trạng thái editor hiện tại thành preset vào kho lưu trữ.
- **Trang Preset** (`/presets`, có mật khẩu như trang chính): danh sách preset · tải lên file JSON · tải về · đặt làm preset mặc định của bot · xoá. Kiểm tra schema ngay lúc tải lên và báo lỗi theo từng trường.
- **Trạng thái bot** ở cuối trang: Mac online/offline, số job đang chờ.

## 8. API mới
| Method | Đường dẫn | Ghi chú |
|---|---|---|
| POST | `/tg/webhook` | Telegram gọi vào; kiểm tra secret header |
| GET/POST/DELETE | `/api/presets[/<name>]` | Danh sách, tải lên (validate), tải về, xoá |
| POST | `/api/presets/from-editor` | Lưu trạng thái editor thành preset |
| GET | `/api/worker/next` | Worker long-poll tối đa 25 giây; header `Authorization: Bearer <WORKER_TOKEN>` |
| POST | `/api/worker/heartbeat` | Mỗi 15 giây |
| POST | `/api/worker/jobs/<id>/status` | Tiến độ / xong / lỗi |
| GET | `/api/bot/status` | Cho web hiển thị |

## 9. Bảo mật và giới hạn
- Bí mật chỉ đặt trong biến môi trường: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_ADMIN_IDS`, `TG_STORAGE_CHANNEL_ID`, `WORKER_TOKEN` (cả Hub và Mac), `TG_API_ID`, `TG_API_HASH` (chỉ Mac). Không ghi token vào log.
- Job lưu trong RAM của Hub. Nếu Render khởi động lại giữa chừng, bot báo admin "Job bị gián đoạn, bấm Xuất lại" (dựa vào tin preview còn lưu trong chat).
- Giữ nguyên toàn bộ giới hạn RAM và luồng ffmpeg của v1.1.1 khi render trên Render.

## 10. Danh sách file (mỗi file một trách nhiệm)
- **Mới:**
  - `bot/tg_api.py`, `bot/webhook.py`, `bot/router.py`, `bot/video_flow.py`, `bot/menu.py`, `bot/keyboards.py`, `bot/commands.py`
  - `core/presets.py`, `config/preset.schema.json`, `presets/*.json` (4 preset mặc định)
  - `storage/base.py`, `storage/repo_presets.py`, `storage/telegram_channel.py`
  - `worker/studio_worker.py`, `worker/hub_client.py`, `worker/tg_mtproto.py`
  - `web/routes_presets.py`, `web/routes_worker.py`, `web/static/js/presets/presets-page.js`
  - `tools/spike_mtproto.py`
  - `config/macos/club.taio.coverworker.plist` (tự chạy worker khi đăng nhập Mac)
  - `tests/test_v17_presets.py`, `tests/test_v17_bot_flow.py`, `tests/test_v17_worker.py`
- **Sửa:** `web/server.py` (chỉ đăng ký route mới), `render.yaml` + `.env.example` (biến mới), `requirements*.txt` (Telethon chỉ cho worker: `requirements-worker.txt`), `README.md`, `DEPLOY.md` (mục "Bot Telegram & Worker Mac"), `CHANGELOG.md`, `VERSION`.

## 11. Giai đoạn (mỗi giai đoạn một commit)
1. **P1 · Kiểm tra bot + spike MTProto** (mục 0 và mục 2). Báo kết quả trước khi làm tiếp.
2. **P2 · Preset:** schema, `core/presets.py` (ghép theo tầng + nguồn giá trị), storage adapter (repo + kênh Telegram), 4 preset mặc định.
3. **P3 · Webhook + chỉ admin + lệnh** (`/start /help /status /presets /preset /get /set /reset /export /import /restore`).
4. **P4 · Gửi video → preview → duyệt → xuất trên Render** (≤ 20 MB).
5. **P5 · `/menu`** đủ các mục ở 6.2.
6. **P6 · Worker Mac:** long-poll, heartbeat, tải/gửi qua MTProto, chọn máy xử lý, file plist tự chạy.
7. **P7 · Web:** nút lưu thành preset, trang Preset, trạng thái bot.
8. **P8 · Kiểm thử và tài liệu:** bảng mục 12, README, DEPLOY (cách lấy API ID/HASH, tạo kênh lưu trữ, đặt webhook, chạy worker), CHANGELOG, `VERSION` = 1.7.0.

## 12. Kiểm thử bắt buộc
| # | Kiểm tra | Kỳ vọng |
|---|---|---|
| T1 | Spike P1 | Đạt 3 điều ở mục 2; có log kết quả |
| T2 | Người không phải admin nhắn bot | Nhận 1 câu từ chối lịch sự, sau đó bị bỏ qua |
| T3 | Gửi video 15 MB, Mac tắt | Render xử lý; preview → sửa caption nhiều dòng → Xuất → nhận video đúng caption và đúng chỗ xuống dòng |
| T4 | Gửi video 300 MB, Mac bật | Mac tải, xuất và gửi video về; tiến độ cập nhật trên Telegram |
| T5 | Gửi video 300 MB, Mac tắt | Bot báo chờ Mac; bật worker → tự xử lý |
| T6 | `/set nen.opacity 0.6` rồi `/get nen.opacity` | Trả về `0.6 (từ /menu)`; preview lần sau dùng giá trị mới |
| T7 | Tải lên preset JSON sai trường trên web | Bị từ chối, báo đúng trường sai |
| T8 | Lưu preset từ editor web → `/preset <tên>` trên bot | Ảnh preview của bot giống ảnh preview trên web (sai khác ≤ 2px) |
| T9 | Khởi động lại Render | Preset người dùng và cài đặt `/menu` vẫn còn (đọc lại từ kênh lưu trữ) |
| T10 | Gửi cùng một update 2 lần (giả lập Telegram gửi lại) | Chỉ xử lý 1 lần |
| T11 | Nhãn phiên bản | `v1.7.0 · ddmmyyhh` trên web; `/status` hiện cùng phiên bản |

## 13. Ngoài phạm vi v1.7 (để sau)
- Cho người dùng khác (không phải admin) dùng bot, kèm hạn mức.
- Xử lý hàng loạt nhiều video trong một tin (album).
- Tự đăng lên mạng xã hội qua Postiz sau khi duyệt.
- Chuyển kho lưu trữ sang cơ sở dữ liệu thật (đổi adapter).

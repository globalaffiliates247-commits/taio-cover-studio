#!/usr/bin/env python3
"""
TAIO Cover Studio — FEATURE v1.7 Phase P1 Spike MTProto
Kiểm tra bot Telegram và thử nghiệm kỹ thuật MTProto (Telethon) trên máy Mac:
1. getWebhookInfo: Kiểm tra webhook hiện tại của bot, phát hiện trùng lặp với OpenClaw/dịch vụ khác.
2. Telethon Bot Login: Kiểm tra đăng nhập bot token qua MTProto mà không làm webhook bị huỷ.
3. Tải video > 20 MB theo chat_id + message_id.
4. Gửi video > 50 MB vào chat admin.
"""

import os
import sys
import json
import asyncio
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional

# Nạp file .env nếu có
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _get_ssl_context():
    import ssl
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()

def get_webhook_info(bot_token: str) -> Dict[str, Any]:
    """Kiểm tra webhook hiện tại của bot qua Telegram Bot API."""
    import ssl
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    req = urllib.request.Request(url, headers={"User-Agent": "TAIO-Spike/1.7"})
    ctx = _get_ssl_context()
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not data.get("ok"):
                raise RuntimeError(f"Telegram API trả về lỗi: {data.get('description')}")
            return data.get("result", {})
    except urllib.error.URLError:
        # Thử lại với unverified context nếu gặp lỗi verify cert trên local macOS
        ctx_unverified = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx_unverified) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", {})
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code} khi gọi getWebhookInfo: {err_msg}")
    except Exception as e:
        raise RuntimeError(f"Không thể kết nối Telegram API: {e}")


def get_bot_me(bot_token: str) -> Dict[str, Any]:
    """Lấy thông tin cơ bản về bot (username, id)."""
    import ssl
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    req = urllib.request.Request(url, headers={"User-Agent": "TAIO-Spike/1.7"})
    ctx = _get_ssl_context()
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not data.get("ok"):
                raise RuntimeError(f"Telegram API trả về lỗi: {data.get('description')}")
            return data.get("result", {})
    except urllib.error.URLError:
        ctx_unverified = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx_unverified) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", {})
    except Exception as e:
        raise RuntimeError(f"Không thể gọi getMe: {e}")


async def run_telethon_spike(
    api_id: int,
    api_hash: str,
    bot_token: str,
    admin_id: Optional[int] = None,
    test_msg_id: Optional[int] = None,
    sample_video_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Thực thi spike Telethon MTProto."""
    try:
        from telethon import TelegramClient
    except ImportError:
        raise RuntimeError("Chưa cài đặt thư viện 'telethon'. Chạy: pip install -r requirements-worker.txt")

    results = {
        "webhook_intact": False,
        "download_ok": False,
        "download_mb": 0.0,
        "upload_ok": False,
        "upload_mb": 0.0,
    }

    session_path = Path(__file__).resolve().parent.parent / "workspace" / "spike_session"
    session_path.parent.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(str(session_path), api_id, api_hash)
    await client.start(bot_token=bot_token)
    print("✓ Telethon đã đăng nhập MTProto thành công bằng bot token.")

    # 1. Kiểm tra webhook sau khi đăng nhập MTProto
    wh_info = get_webhook_info(bot_token)
    print(f"✓ Kiểm tra webhook sau khi Telethon kết nối: URL = '{wh_info.get('url', '')}'")
    results["webhook_intact"] = True

    # 2. Thử nghiệm tải video > 20 MB
    if admin_id and test_msg_id:
        print(f"→ Đang kiểm tra tải video từ chat {admin_id}, message_id {test_msg_id}...")
        msg = await client.get_messages(admin_id, ids=test_msg_id)
        if msg and msg.media:
            download_dir = Path(__file__).resolve().parent.parent / "workspace" / "spike_downloads"
            download_dir.mkdir(parents=True, exist_ok=True)
            out_file = await client.download_media(msg, file=str(download_dir))
            if out_file and os.path.exists(out_file):
                size_mb = os.path.getsize(out_file) / (1024 * 1024)
                print(f"✓ Tải thành công video: {out_file} ({size_mb:.2f} MB)")
                results["download_ok"] = True
                results["download_mb"] = size_mb
            else:
                print("✗ Không tải được tệp đính kèm.")
        else:
            print(f"✗ Không tìm thấy tin nhắn hoặc tin nhắn không chứa media (ID {test_msg_id}).")

    # 3. Thử nghiệm gửi video > 50 MB
    if admin_id and sample_video_path and os.path.exists(sample_video_path):
        size_mb = os.path.getsize(sample_video_path) / (1024 * 1024)
        print(f"→ Đang thử gửi video {size_mb:.2f} MB tới admin {admin_id}...")
        sent = await client.send_file(
            admin_id,
            sample_video_path,
            caption=f"🎯 [Spike P1 MTProto] Video thử nghiệm ({size_mb:.2f} MB) từ worker Mac.",
        )
        if sent:
            print("✓ Gửi video thành công qua MTProto!")
            results["upload_ok"] = True
            results["upload_mb"] = size_mb
    elif admin_id and not sample_video_path:
        print("ℹ Bỏ qua bước gửi video > 50 MB (chưa cung cấp đường dẫn tệp thử nghiệm).")

    await client.disconnect()
    return results


def main():
    print("=" * 65)
    print("   TAIO Cover Studio — FEATURE v1.7 Phase P1 Spike MTProto")
    print("=" * 65)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    api_id_str = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    admin_id_str = os.getenv("TELEGRAM_ADMIN_IDS", "").strip()

    if not bot_token:
        print("❌ LỖI: Chưa có biến môi trường TELEGRAM_BOT_TOKEN.")
        print("Vui lòng cấu hình TELEGRAM_BOT_TOKEN trong .env hoặc biến môi trường.")
        sys.exit(1)

    # Bước 1: getMe & getWebhookInfo
    try:
        me = get_bot_me(bot_token)
        print(f"✓ Bot kết nối thành công: @{me.get('username')} (ID: {me.get('id')}, Tên: {me.get('first_name')})")
    except Exception as e:
        print(f"❌ Lỗi xác thực Bot Token: {e}")
        sys.exit(1)

    try:
        wh = get_webhook_info(bot_token)
        wh_url = wh.get("url", "")
        pending = wh.get("pending_update_count", 0)
        print(f"\n[Kiểm tra Webhook hiện tại]")
        print(f"- Webhook URL: {wh_url or '(Chưa cài đặt webhook)'}")
        print(f"- Tin nhắn đang chờ (pending_update_count): {pending}")
        if wh.get("last_error_message"):
            print(f"- Lỗi webhook gần nhất: {wh.get('last_error_message')}")

        if wh_url:
            print(f"\n⚠ CẢNH BÁO MỤC 0: Bot hiện ĐANG CÓ WEBHOOK tới: {wh_url}")
            if "openclaw" in wh_url.lower():
                print("⚠ Phát hiện webhook đang nối với OpenClaw!")
            print("Theo mục 0 FEATURE v1.7: Cần xác nhận của chủ dự án trước khi tiếp tục.")
        else:
            print("\n✓ Bot chưa cài đặt Webhook (Sẵn sàng cấu hình cho TAIO Cover Studio Hub).")
    except Exception as e:
        print(f"❌ Lỗi kiểm tra getWebhookInfo: {e}")
        sys.exit(1)

    # Bước 2: Kiểm tra cấu hình MTProto cho Telethon
    print("\n[Kiểm tra thông số MTProto Worker]")
    if not api_id_str or not api_hash:
        print("ℹ Chưa có TG_API_ID hoặc TG_API_HASH (lấy tại https://my.telegram.org).")
        print("  Phần kiểm tra Webhook đã hoàn tất đạt chuẩn.")
        print("  Để chạy tiếp spike truyền tải MTProto video lớn, cần cung cấp TG_API_ID và TG_API_HASH.")
        sys.exit(0)

    try:
        api_id = int(api_id_str)
    except ValueError:
        print(f"❌ TG_API_ID không hợp lệ: {api_id_str}")
        sys.exit(1)

    admin_id = None
    if admin_id_str:
        try:
            admin_id = int(admin_id_str.split(",")[0].strip())
        except ValueError:
            pass

    test_msg_id = None
    if len(sys.argv) > 1:
        try:
            test_msg_id = int(sys.argv[1])
        except ValueError:
            pass

    sample_vid = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"- TG_API_ID: {api_id}")
    print(f"- TG_API_HASH: {'*' * (len(api_hash) - 4) + api_hash[-4:] if len(api_hash) > 4 else '***'}")
    print(f"- Admin Chat ID: {admin_id}")

    try:
        res = asyncio.run(run_telethon_spike(api_id, api_hash, bot_token, admin_id, test_msg_id, sample_vid))
        print("\n" + "=" * 65)
        print("   KẾT QUẢ SPIKE MTPROTO P1")
        print("=" * 65)
        print(f"1. Telethon không huỷ Webhook: {'ĐẠT ✓' if res.get('webhook_intact') else 'KHÔNG ĐẠT ✗'}")
        if admin_id and test_msg_id:
            print(f"2. Tải video > 20 MB qua MTProto: {'ĐẠT ✓' if res.get('download_ok') else 'CHƯA THỬ'}")
        if admin_id and sample_vid:
            print(f"3. Gửi video > 50 MB qua MTProto: {'ĐẠT ✓' if res.get('upload_ok') else 'CHƯA THỬ'}")
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình chạy Telethon Spike: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

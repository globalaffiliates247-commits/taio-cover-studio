"""
web/server.py - Flask API Server phục vụ toàn bộ giao diện và endpoint của TAIO Cover Studio.
"""

import io
import os
import queue
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, send_file, Response

from core.brand import load_brand_kit, get_default_logo_path
from core.canvas import calculate_canvas_layout
from core.compositor import build_preview, render_video
from core.paths import BASE_DIR, BRAND_DIR, OUTPUTS_DIR, UPLOADS_DIR, WORKSPACE_DIR, generate_cover_clip_name
from core.templates import get_template, list_templates
from core.video_probe import probe_video

from ai.settings import get_default_provider_id, list_ui_providers
from ai.suggest import get_caption_suggestions

from web.auth import require_auth_if_configured
from web.cleanup import cleanup_old_files

# Mã định danh phiên chạy của máy chủ
boot_id = uuid.uuid4().hex[:8]

# Khởi tạo Flask App
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "web" / "static"),
    static_url_path="/static",
)

# Giới hạn dung lượng tải lên tối đa
max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "4096").strip())
app.config["MAX_CONTENT_LENGTH"] = max_upload_mb * 1024 * 1024

# Đăng ký kiểm tra xác thực trước mỗi request
app.before_request(require_auth_if_configured)

# ==================== HÀNG ĐỢI XUẤT VIDEO (RENDER QUEUE) ====================
render_queue = queue.Queue()
jobs_store: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()

max_parallel = int(os.getenv("MAX_PARALLEL_RENDERS", "1").strip())
current_active_renders = 0

# Giới hạn tối đa 2 preview chạy cùng lúc
preview_semaphore = threading.BoundedSemaphore(2)

# In log cấu hình hệ thống khi khởi động
ffmpeg_threads_val = os.getenv("FFMPEG_THREADS", "2").strip()
output_max_res_val = os.getenv("OUTPUT_MAX_RES", "720").strip()
print(
    f"[BOOT] boot_id={boot_id} cpu_count={os.cpu_count()} "
    f"FFMPEG_THREADS={ffmpeg_threads_val} MAX_PARALLEL_RENDERS={max_parallel} "
    f"OUTPUT_MAX_RES={output_max_res_val} WORKSPACE_DIR={WORKSPACE_DIR}",
    flush=True,
)


def render_worker():
    """Luồng nền xử lý tuần tự các tác vụ xuất video trong hàng đợi."""
    global current_active_renders
    while True:
        job_id = render_queue.get()
        if job_id is None:
            break

        with jobs_lock:
            job = jobs_store.get(job_id)
            if not job:
                render_queue.task_done()
                continue
            job["status"] = "running"
            job["progress"] = 0.0

        try:
            video_path = job["video_path"]
            template_id = job["template_id"]
            caption = job["caption"]
            logo_path = job.get("logo_path")
            out_path = job["out_path"]

            tpl = get_template(template_id)
            if not tpl:
                raise ValueError(f"Không tìm thấy template '{template_id}'")

            def on_progress(p: float):
                with jobs_lock:
                    if job_id in jobs_store:
                        jobs_store[job_id]["progress"] = round(p, 3)

            res = render_video(
                video_path=video_path,
                template=tpl,
                caption=caption,
                output_path=out_path,
                logo_path=logo_path,
                on_progress=on_progress,
            )

            with jobs_lock:
                job["status"] = "done"
                job["progress"] = 1.0
                job["warnings"] = res.get("warnings", [])

        except Exception as e:
            with jobs_lock:
                job["status"] = "error"
                job["error"] = str(e)

        finally:
            render_queue.task_done()


# Khởi động worker daemon
for _ in range(max_parallel):
    worker_t = threading.Thread(target=render_worker, daemon=True)
    worker_t.start()


# ==================== TRANG CHỦ & HEALTH CHECK ====================
@app.route("/")
def index():
    """Trả về giao diện HTML chính của ứng dụng."""
    index_path = BASE_DIR / "web" / "static" / "index.html"
    return send_file(str(index_path))


@app.route("/healthz")
def healthz():
    """Health check endpoint cho Docker / Render Blueprint."""
    return "ok", 200


@app.route("/static/brand-logo")
def brand_logo():
    """Trả về logo thương hiệu mặc định."""
    logo_path = get_default_logo_path()
    if logo_path and logo_path.exists():
        return send_file(str(logo_path), mimetype="image/png")
    return Response(status=404)


# ==================== CẤU HÌNH HỆ THỐNG ====================
@app.route("/api/config")
def api_config():
    """Cung cấp cấu hình template, AI providers và thông tin brand cho UI."""
    brand_data = load_brand_kit()
    tpls = list_templates(brand_data=brand_data)
    ai_providers = list_ui_providers()
    default_ai = get_default_provider_id()

    clean_brand = {
        "name": brand_data.get("name", "TAIO"),
        "handle": brand_data.get("handle", "taio.club"),
        "tagline": brand_data.get("tagline", ""),
        "colors": brand_data.get("colors", {}),
    }

    telegram_cfg = {
        "configured": bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip()),
        "default_chat_id": os.getenv("TELEGRAM_CHAT_ID", "").strip(),
    }

    return jsonify({
        "boot_id": boot_id,
        "templates": tpls,
        "ai": {
            "default": default_ai,
            "providers": ai_providers,
        },
        "brand": clean_brand,
        "telegram": telegram_cfg,
    })


# ==================== TẢI LÊN FILE ====================
@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Tiếp nhận video hoặc logo tải lên."""
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy tệp tải lên."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Tên tệp không hợp lệ."}), 400

    kind = request.form.get("kind", "video").lower()
    clean_name = secure_filename(file.filename) or "uploaded_file"
    file_ext = Path(clean_name).suffix.lower()

    # Dọn dẹp các file cũ trước khi lưu file mới
    cleanup_old_files()

    if kind == "logo":
        file_id = f"logo_{uuid.uuid4().hex[:10]}"
        dest_filename = f"{file_id}{file_ext or '.png'}"
        dest_path = UPLOADS_DIR / dest_filename
        file.save(str(dest_path))

        return jsonify({
            "id": file_id,
            "name": clean_name,
            "kind": "logo",
        })

    # Xử lý video
    temp_id = f"temp_{uuid.uuid4().hex[:10]}"
    temp_path = UPLOADS_DIR / f"{temp_id}{file_ext or '.mp4'}"
    file.save(str(temp_path))

    # Kiểm tra tính hợp lệ bằng ffprobe
    try:
        info = probe_video(str(temp_path))
    except Exception as e:
        # File không phải video hợp lệ -> Xoá file ngay lập tức và báo lỗi tiếng Việt
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({"error": f"Tệp tải lên không phải video hợp lệ: {e}"}), 400

    # Đổi tên sang ID chính thức và gán tên chuẩn theo quy ước TAIO.CoverClip_YYMMDDXX
    video_id = f"vid_{uuid.uuid4().hex[:10]}"
    final_filename = f"{video_id}{file_ext or '.mp4'}"
    final_path = UPLOADS_DIR / final_filename
    temp_path.rename(final_path)

    # Đặt tên chuẩn hóa: TAIO.CoverClip_DDMMXX.mp4
    standard_name = generate_cover_clip_name()

    return jsonify({
        "id": video_id,
        "name": standard_name,
        "raw_name": clean_name,
        "kind": "video",
        "info": {
            "width": info.width,
            "height": info.height,
            "duration": info.duration,
            "formatted_duration": info.formatted_duration,
            "fps": info.fps,
            "has_audio": info.has_audio,
            "summary": info.summary,
        },
    })


def _find_upload_file(file_id: str) -> Optional[Path]:
    """Tìm file trong thư mục uploads theo file_id an toàn."""
    if not file_id:
        return None
    for f in UPLOADS_DIR.glob(f"{file_id}.*"):
        if f.is_file():
            return f
    # Tìm trực tiếp nếu truyền kèm đuôi mở rộng
    direct = UPLOADS_DIR / file_id
    if direct.is_file():
        return direct
    return None


# ==================== XEM TRƯỚC (PREVIEW) ====================
@app.route("/api/preview", methods=["POST"])
def api_preview():
    """Tạo ảnh xem trước 1 khung hình, khớp 100% với video xuất."""
    acquired = preview_semaphore.acquire(blocking=False)
    if not acquired:
        return jsonify({"error": "Đang bận, thử lại sau giây lát"}), 429

    try:
        data = request.get_json(force=True, silent=True) or {}
        video_id = data.get("video_id", "")
        template_id = data.get("template", "footer_band")
        caption = data.get("caption", "")
        time_sec = float(data.get("t", 1.0))
        logo_id = data.get("logo_id")

        video_file = _find_upload_file(video_id)
        if not video_file or not video_file.exists():
            return jsonify({
                "error": "Không tìm thấy video tương ứng với ID đã cung cấp.",
                "code": "VIDEO_NOT_FOUND",
            }), 404

        tpl = get_template(template_id)
        if not tpl:
            return jsonify({"error": f"Không tìm thấy mẫu lớp phủ: '{template_id}'"}), 404

        logo_path = None
        if logo_id:
            custom_logo = _find_upload_file(logo_id)
            if custom_logo and custom_logo.exists():
                logo_path = str(custom_logo)

        preview_img, warnings = build_preview(
            video_path=str(video_file),
            template=tpl,
            caption=caption,
            time_sec=time_sec,
            logo_path=logo_path,
        )

        buf = io.BytesIO()
        preview_img.save(buf, format="JPEG", quality=90)
        buf.seek(0)

        # Đóng gói warnings vào header X-Warnings dạng UTF-8 hex
        resp = send_file(buf, mimetype="image/jpeg")
        if warnings:
            warn_str = " | ".join(warnings)
            resp.headers["X-Warnings"] = warn_str.encode("utf-8").hex()

        return resp
    except Exception as e:
        return jsonify({"error": f"Lỗi tạo ảnh xem trước: {e}"}), 500
    finally:
        preview_semaphore.release()


# ==================== GỢI Ý CAPTION BẰNG AI ====================
@app.route("/api/suggest", methods=["POST"])
def api_suggest():
    """Gợi ý các caption thu hút dựa trên nội dung video."""
    data = request.get_json(force=True, silent=True) or {}
    video_id = data.get("video_id", "")
    provider = data.get("provider")
    style = data.get("style", "tin_tuc")
    context = data.get("context", "")
    n = int(data.get("n", 5))

    video_file = _find_upload_file(video_id)
    if not video_file or not video_file.exists():
        return jsonify({
            "error": "Không tìm thấy video để phân tích.",
            "code": "VIDEO_NOT_FOUND",
        }), 404

    try:
        suggestions = get_caption_suggestions(
            video_path=str(video_file),
            context=context,
            style=style,
            provider=provider,
            n=n,
        )
        return jsonify(suggestions)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==================== XUẤT VIDEO (RENDER & JOBS) ====================
@app.route("/api/render", methods=["POST"])
def api_render():
    """Tiếp nhận yêu cầu xuất video và đưa vào hàng đợi xử lý."""
    data = request.get_json(force=True, silent=True) or {}
    video_id = data.get("video_id", "")
    video_name = data.get("video_name", "video")
    template_id = data.get("template", "footer_band")
    caption = data.get("caption", "")
    logo_id = data.get("logo_id")

    video_file = _find_upload_file(video_id)
    if not video_file or not video_file.exists():
        return jsonify({
            "error": "Không tìm thấy video để xuất.",
            "code": "VIDEO_NOT_FOUND",
        }), 404

    tpl = get_template(template_id)
    if not tpl:
        return jsonify({"error": f"Không tìm thấy mẫu lớp phủ: '{template_id}'"}), 404

    logo_path = None
    if logo_id:
        custom_logo = _find_upload_file(logo_id)
        if custom_logo and custom_logo.exists():
            logo_path = str(custom_logo)

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    out_path = str(OUTPUTS_DIR / f"{job_id}.mp4")

    job_info = {
        "id": job_id,
        "video_path": str(video_file),
        "video_name": video_name,
        "template_id": template_id,
        "caption": caption,
        "logo_path": logo_path,
        "out_path": out_path,
        "status": "queued",
        "progress": 0.0,
        "warnings": [],
        "error": None,
        "created_at": time.time(),
    }

    with jobs_lock:
        jobs_store[job_id] = job_info

    render_queue.put(job_id)
    return jsonify({"job_id": job_id})


@app.route("/api/job/<job_id>")
def api_job_status(job_id: str):
    """Truy vấn trạng thái và tiến độ xử lý của job."""
    with jobs_lock:
        job = jobs_store.get(job_id)
        if not job:
            return jsonify({
                "error": "Không tìm thấy mã tiến trình này.",
                "boot_id": boot_id,
            }), 404

        resp_data = {
            "boot_id": boot_id,
            "status": job["status"],
            "progress": job["progress"],
            "warnings": job.get("warnings", []),
            "error": job.get("error"),
        }
        if job["status"] == "done":
            resp_data["file"] = job_id

        return jsonify(resp_data)


@app.route("/api/download/<job_id>")
def api_download(job_id: str):
    """Tải file video đã hoàn thành."""
    with jobs_lock:
        job = jobs_store.get(job_id)
        if not job:
            return jsonify({"error": "Không tìm thấy tệp cần tải."}), 404
        if job["status"] != "done":
            return jsonify({"error": "Video chưa sẵn sàng để tải về."}), 400

        out_path = Path(job["out_path"])
        if not out_path.exists():
            return jsonify({"error": "Tệp video đã bị xoá hoặc không tồn tại."}), 404

        raw_name = job.get("video_name", "TAIO.CoverClip.mp4")
        if not raw_name.endswith(".mp4"):
            download_filename = f"{raw_name}.mp4"
        else:
            download_filename = raw_name

        return send_file(
            str(out_path),
            as_attachment=True,
            download_name=download_filename,
            mimetype="video/mp4",
        )


@app.route("/api/send-telegram", methods=["POST"])
def api_send_telegram():
    """Gửi video đã xuất qua Telegram Bot trung gian."""
    data = request.get_json(force=True, silent=True) or {}
    job_id = data.get("job_id", "")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = (data.get("chat_id") or os.getenv("TELEGRAM_CHAT_ID", "")).strip()

    if not bot_token:
        return jsonify({"error": "Vui lòng nhập Bot Token và Chat ID của bot Telegram (hoặc cấu hình TELEGRAM_BOT_TOKEN)."}), 400

    if not chat_id:
        return jsonify({"error": "Vui lòng nhập Chat ID của bot Telegram."}), 400

    with jobs_lock:
        job = jobs_store.get(job_id)
        if not job:
            return jsonify({"error": "Không tìm thấy video tương ứng."}), 404
        if job["status"] != "done":
            return jsonify({"error": "Video chưa xuất xong."}), 400

        out_path = Path(job["out_path"])
        if not out_path.exists():
            return jsonify({"error": "Tệp video không tồn tại."}), 404

    # Gửi qua Telegram Bot API sendVideo
    import json
    import urllib.request
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"

    with open(out_path, "rb") as vf:
        video_bytes = vf.read()

    video_filename = job.get("video_name", "TAIO.CoverClip.mp4")
    caption_text = f"🎬 {video_filename}\n{job.get('caption', '')}".strip()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{chat_id}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"{caption_text}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="video"; filename="{video_filename}"\r\n'
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode("utf-8") + video_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            if not resp_data.get("ok"):
                return jsonify({"error": f"Telegram trả về lỗi: {resp_data.get('description')}"}), 400
            return jsonify({"ok": True, "message": "Đã gửi video thành công vào Telegram của bạn!"})
    except Exception as e:
        return jsonify({"error": f"Lỗi gửi Telegram: {e}"}), 400


@app.errorhandler(413)
def request_entity_too_large(error):
    """Xử lý lỗi tải tệp vượt quá dung lượng cho phép."""
    return jsonify({"error": f"Dung lượng tệp vượt quá giới hạn {max_upload_mb} MB cho phép."}), 413

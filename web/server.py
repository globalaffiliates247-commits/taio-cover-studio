"""
web/server.py - Flask API Server phục vụ toàn bộ giao diện và endpoint của TAIO Cover Studio.
"""

import collections
import io
import json
import os
import queue
import re
import threading
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, send_file, Response

from core.brand import load_brand_kit, get_default_logo_path
from core.canvas import calculate_canvas_layout
from core.compositor import build_preview, render_video
from core.paths import BASE_DIR, BRAND_DIR, CONFIG_DIR, OUTPUTS_DIR, UPLOADS_DIR, WORKSPACE_DIR, generate_cover_clip_name
from core.templates import get_template, list_templates
from core.version import get_version_info
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

# Rate limit và kiểm soát gửi Telegram 1 chạm (FEATURE v1.5 P4)
_TELEGRAM_SENT_JOBS = set()
_TELEGRAM_IP_TIMESTAMPS: Dict[str, list] = collections.defaultdict(list)
_TELEGRAM_RATE_LOCK = threading.Lock()

# In log cấu hình hệ thống khi khởi động
version_info = get_version_info()
ffmpeg_threads_val = os.getenv("FFMPEG_THREADS", "2").strip()
output_max_res_val = os.getenv("OUTPUT_MAX_RES", "720").strip()
print(
    f"[BOOT] boot_id={boot_id} version={version_info['version']} build={version_info['build']} "
    f"label='{version_info['label']}' cpu_count={os.cpu_count()} "
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
                overrides=job.get("overrides"),
                quality=job.get("quality", "balanced"),
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
    """Trả về giao diện HTML chính của ứng dụng với nhãn phiên bản và chống cache ?v=<build>."""
    index_path = BASE_DIR / "web" / "static" / "index.html"
    if not index_path.exists():
        return "Index not found", 404

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    v_info = get_version_info()
    b_stamp = v_info.get("build", "")

    # Chống cache: gắn ?v=<build> cho các file CSS và JS
    if b_stamp:
        html = re.sub(r'href="(/static/[^"]+\.css)(?:\?v=[^"]*)?"', rf'href="\1?v={b_stamp}"', html)
        html = re.sub(r'src="(/static/[^"]+\.js)(?:\?v=[^"]*)?"', rf'src="\1?v={b_stamp}"', html)

    # Gắn trực tiếp nhãn phiên bản vào HTML
    html = re.sub(
        r'<div class="app-version"[^>]*>.*?</div>',
        f'<div class="app-version" id="appVersionBadge">{v_info.get("label", "")}</div>',
        html,
    )

    resp = Response(html, mimetype="text/html")
    resp.headers["X-App-Version"] = v_info.get("label", "")
    return resp


@app.route("/healthz")
def healthz():
    """Health check endpoint cho Docker / Render Blueprint."""
    v_info = get_version_info()
    resp = Response("ok", 200, mimetype="text/plain")
    resp.headers["X-App-Version"] = v_info.get("label", "")
    return resp


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

    telegram_configured = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip() and os.getenv("TELEGRAM_CHAT_ID", "").strip())
    telegram_cfg = {
        "configured": telegram_configured,
    }

    safe_zones = {}
    safe_zones_path = CONFIG_DIR / "safe_zones.json"
    if safe_zones_path.exists():
        try:
            with open(safe_zones_path, "r", encoding="utf-8") as sz_f:
                safe_zones = json.load(sz_f)
        except Exception:
            pass

    fonts = []
    fonts_path = BASE_DIR / "assets" / "fonts" / "fonts.json"
    if fonts_path.exists():
        try:
            with open(fonts_path, "r", encoding="utf-8") as f:
                fonts = json.load(f)
        except Exception:
            pass

    text_styles = []
    text_styles_path = BRAND_DIR / "text_styles.json"
    if text_styles_path.exists():
        try:
            with open(text_styles_path, "r", encoding="utf-8") as f:
                text_styles = json.load(f)
        except Exception:
            pass

    palettes = {}
    palettes_path = CONFIG_DIR / "palettes.json"
    if palettes_path.exists():
        try:
            with open(palettes_path, "r", encoding="utf-8") as f:
                palettes = json.load(f)
        except Exception:
            pass

    return jsonify({
        "boot_id": boot_id,
        "version_info": get_version_info(),
        "templates": tpls,
        "palettes": palettes,
        "ai": {
            "default": default_ai,
            "providers": ai_providers,
        },
        "brand": clean_brand,
        "telegram": telegram_cfg,
        "safe_zones": safe_zones,
        "fonts": fonts,
        "text_styles": text_styles,
    })


# ==================== TẢI LÊN FILE & URL ====================
@app.route("/api/upload-url", methods=["POST"])
def api_upload_url():
    """Tải video từ liên kết URL trên mạng về thư mục uploads."""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or request.form.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Vui lòng nhập đường dẫn URL video."}), 400

    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"error": "Đường dẫn URL phải bắt đầu bằng http:// hoặc https://"}), 400

    cleanup_old_files()

    temp_id = f"url_{uuid.uuid4().hex[:10]}"
    temp_path = UPLOADS_DIR / f"{temp_id}.tmp"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            cl = resp.headers.get("Content-Length")
            max_bytes = MAX_UPLOAD_MB * 1024 * 1024
            if cl and int(cl) > max_bytes:
                return jsonify({"error": f"Kích thước video ({int(cl) // (1024*1024)}MB) vượt quá giới hạn {MAX_UPLOAD_MB}MB."}), 413

            downloaded = 0
            with open(temp_path, "wb") as f:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > max_bytes:
                        if temp_path.exists():
                            temp_path.unlink()
                        return jsonify({"error": f"Tệp video vượt quá giới hạn {MAX_UPLOAD_MB}MB."}), 413
                    f.write(chunk)

            # Lấy tên file
            clean_name = "url_video.mp4"
            cd = resp.headers.get("Content-Disposition")
            if cd and "filename=" in cd:
                fname = cd.split("filename=")[-1].strip('"\'; ')
                if fname:
                    clean_name = secure_filename(fname)
            else:
                parsed_path = urllib.parse.urlparse(url).path
                base_name = Path(parsed_path).name
                if base_name:
                    clean_name = secure_filename(base_name)
    except urllib.error.HTTPError as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({"error": f"Không thể tải từ URL (Lỗi HTTP {e.code}: {e.reason})."}), 400
    except urllib.error.URLError as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({"error": f"Lỗi kết nối tới URL: {e.reason}"}), 400
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({"error": f"Lỗi khi tải video từ URL: {e}"}), 400

    # Kiểm tra tính hợp lệ bằng ffprobe
    try:
        info = probe_video(str(temp_path))
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({"error": f"Liên kết không chứa video hợp lệ hoặc định dạng không hỗ trợ ({e})."}), 400

    file_ext = Path(clean_name).suffix.lower()
    if not file_ext or file_ext not in [".mp4", ".mov", ".mkv", ".webm", ".m4v"]:
        file_ext = ".mp4"
    video_id = f"vid_{uuid.uuid4().hex[:10]}"
    final_filename = f"{video_id}{file_ext}"
    final_path = UPLOADS_DIR / final_filename
    temp_path.rename(final_path)

    standard_name = generate_cover_clip_name()

    return jsonify({
        "id": video_id,
        "name": standard_name,
        "raw_name": clean_name,
        "kind": "video",
        "url": url,
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


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Tiếp nhận video hoặc logo tải lên (hỗ trợ cả tệp file và URL)."""
    if "file" not in request.files:
        data = request.get_json(silent=True) or {}
        url = data.get("url") or request.form.get("url")
        if url:
            return api_upload_url()
        return jsonify({"error": "Không tìm thấy tệp tải lên hoặc liên kết URL."}), 400

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


@app.route("/api/video/<video_id>")
def api_stream_video(video_id: str):
    """Phục vụ phát video gốc trực tiếp với hỗ trợ HTTP Range để trình duyệt tua mượt (FEATURE v1.5 P7)."""
    video_path = _find_upload_file(video_id)
    if not video_path or not video_path.exists():
        return jsonify({"error": "Không tìm thấy video."}), 404

    mimetype = "video/mp4"
    ext = video_path.suffix.lower()
    if ext == ".mov":
        mimetype = "video/quicktime"
    elif ext == ".webm":
        mimetype = "video/webm"
    elif ext == ".mkv":
        mimetype = "video/x-matroska"

    return send_file(video_path, mimetype=mimetype, conditional=True)


# ==================== KHỐI ĐỒ HOẠ (LAYER IMAGE CHO STICKER) ====================
@app.route("/api/layer-image")
def api_layer_image():
    """Trả ảnh PNG nền trong suốt của khối logo (cạnh dài 512px) để client kéo thả sticker."""
    template_id = request.args.get("template", "lower_third_fade")
    layer_id = request.args.get("layer", "logo")
    logo_id = request.args.get("logo_id")
    pill_param = request.args.get("pill")

    tpl = get_template(template_id)
    if not tpl:
        return jsonify({"error": f"Không tìm thấy mẫu lớp phủ '{template_id}'"}), 404

    target_layer = None
    for l in tpl.get("layers", []):
        if l.get("id") == layer_id or l.get("type") == layer_id:
            target_layer = l
            break

    if not target_layer:
        target_layer = {"id": "logo", "type": "logo", "label": "TAIO.CLUB", "pill": True}

    logo_path = None
    if logo_id:
        custom_logo = _find_upload_file(logo_id)
        if custom_logo and custom_logo.exists():
            logo_path = str(custom_logo)

    pill_mode = request.args.get("pill_mode")
    pill_color = request.args.get("pill_color")
    pill_opacity = request.args.get("pill_opacity")

    pill_override = None
    if pill_mode or pill_color or pill_opacity:
        pill_override = {
            "mode": pill_mode or ("translucent" if pill_param != "0" else "none"),
            "color": pill_color,
            "opacity": float(pill_opacity) if pill_opacity else None,
            "enabled": pill_mode != "none" if pill_mode else (pill_param != "0"),
        }
    elif pill_param == "1":
        pill_override = {"mode": "translucent", "enabled": True}
    elif pill_param == "0":
        pill_override = {"mode": "none", "enabled": False}

    from core.layer_blocks import render_logo_block
    img = render_logo_block(target_layer, logo_path=logo_path, scale_px=512, pill_override=pill_override)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ==================== ĐỐI TƯỢNG SCENE (OBJECT IMAGE - FEATURE v1.4) ====================
@app.route("/api/object-image", methods=["POST"])
def api_object_image():
    """
    Kết xuất ảnh PNG transparent RGBA của 1 đối tượng scene (cạnh dài <= 1024px).
    Có bộ nhớ đệm LRU tối đa 50 ảnh.
    """
    acquired = preview_semaphore.acquire(blocking=False)
    if not acquired:
        return jsonify({"error": "Hệ thống đang bận, vui lòng thử lại sau"}), 429

    try:
        data = request.get_json(force=True, silent=True) or {}
        obj = data.get("object")
        if not obj or not isinstance(obj, dict):
            return jsonify({"error": "Thiếu dữ liệu 'object'"}), 400

        logo_id = data.get("logo_id")
        logo_path = None
        if logo_id:
            custom_logo = _find_upload_file(logo_id)
            if custom_logo and custom_logo.exists():
                logo_path = str(custom_logo)

        ctx = {"logo_path": logo_path}

        from core.scene import (
            render_single_object_image,
            _OBJECT_IMAGE_CACHE,
            _OBJECT_CACHE_KEYS,
            MAX_OBJECT_CACHE_SIZE,
        )

        img, cache_key = render_single_object_image(obj, max_edge=1024, ctx=ctx)

        if cache_key in _OBJECT_IMAGE_CACHE:
            png_bytes = _OBJECT_IMAGE_CACHE[cache_key]
        else:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

            if len(_OBJECT_CACHE_KEYS) >= MAX_OBJECT_CACHE_SIZE:
                oldest_key = _OBJECT_CACHE_KEYS.pop(0)
                _OBJECT_IMAGE_CACHE.pop(oldest_key, None)
            _OBJECT_IMAGE_CACHE[cache_key] = png_bytes
            _OBJECT_CACHE_KEYS.append(cache_key)

        return Response(png_bytes, mimetype="image/png")
    except Exception as e:
        return jsonify({"error": f"Lỗi render object image: {str(e)}"}), 500
    finally:
        preview_semaphore.release()


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
        template_id = data.get("template", "lower_third_fade")
        caption = data.get("caption", "")
        time_sec = float(data.get("t", 1.0))
        logo_id = data.get("logo_id")
        overrides = data.get("overrides")
        exclude_layers = data.get("exclude_layers")
        exclude_objects = bool(data.get("exclude_objects", False))

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
            overrides=overrides,
            exclude_layers=exclude_layers,
            exclude_objects=exclude_objects,
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
    template_id = data.get("template", "lower_third_fade")
    caption = data.get("caption", "")
    logo_id = data.get("logo_id")
    overrides = data.get("overrides")
    quality = data.get("quality", "balanced")
    if quality not in ("light", "balanced", "high"):
        quality = "balanced"

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
        "overrides": overrides,
        "quality": quality,
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
    """Gửi video đã xuất 1 chạm về bot admin của TAIO.CLUB (FEATURE v1.5 P4)."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    admin_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not admin_chat_id:
        return jsonify({"error": "Máy chủ chưa cấu hình bot Telegram của admin."}), 503

    data = request.get_json(force=True, silent=True) or {}
    job_id = data.get("job_id", "")
    user_note = data.get("note", "").strip()

    if not job_id:
        return jsonify({"error": "Thiếu mã xuất video (job_id)."}), 400

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
    now_ts = time.time()

    with _TELEGRAM_RATE_LOCK:
        # 1. Chống gửi lặp: mỗi job chỉ gửi 1 lần
        if job_id in _TELEGRAM_SENT_JOBS:
            return jsonify({"error": "Video này đã được gửi về TAIO.CLUB trước đó."}), 400

        # 2. Giới hạn 20 lần/giờ cho mỗi IP
        history = [t for t in _TELEGRAM_IP_TIMESTAMPS[ip] if now_ts - t < 3600]
        if len(history) >= 20:
            return jsonify({"error": "Bạn đã gửi quá 20 lần trong 1 giờ. Vui lòng thử lại sau."}), 429
        _TELEGRAM_IP_TIMESTAMPS[ip] = history

    with jobs_lock:
        job = jobs_store.get(job_id)
        if not job:
            return jsonify({"error": "Không tìm thấy video tương ứng."}), 404
        if job["status"] != "done":
            return jsonify({"error": "Video chưa xuất xong."}), 400

        out_path = Path(job["out_path"])
        if not out_path.exists():
            return jsonify({"error": "Tệp video không tồn tại."}), 404

    # 3. Giới hạn dung lượng bot Telegram (~50 MB)
    file_size_bytes = out_path.stat().st_size
    if file_size_bytes > 50 * 1024 * 1024:
        return jsonify({
            "error": "Video quá lớn để gửi Telegram — hãy xuất lại ở mức Nhẹ",
            "code": "FILE_TOO_LARGE",
        }), 400

    # 4. Nội dung tin nhắn kèm video theo đặc tả
    from datetime import datetime, timezone, timedelta
    vn_time = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S %d/%m/%Y")
    ver_info = get_version_info()
    app_ver = ver_info.get("label", f"v{ver_info.get('version', '1.5.0')}")

    size_mb = file_size_bytes / (1024 * 1024)
    video_filename = job.get("video_name", "TAIO.CoverClip.mp4")
    tpl_id = job.get("template_id", "Mặc định")
    quality_label = job.get("quality", "balanced")
    caption = job.get("caption", "").strip()

    caption_lines = [
        f"🎬 *{video_filename}*",
        f"📝 *Caption:* {caption}" if caption else "",
        f"🎨 *Mẫu:* `{tpl_id}` · *Mức nén:* `{quality_label}`",
        f"📦 *Dung lượng:* {size_mb:.1f} MB",
        f"🕒 *Thời gian:* {vn_time} (UTC+7)",
        f"🏷 *Phiên bản:* `{app_ver}`",
    ]
    if user_note:
        caption_lines.append(f"💬 *Ghi chú:* {user_note}")

    caption_text = "\n".join([line for line in caption_lines if line])

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"

    with open(out_path, "rb") as vf:
        video_bytes = vf.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{admin_chat_id}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"{caption_text}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="parse_mode"\r\n\r\n'
        f"Markdown\r\n"
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

            with _TELEGRAM_RATE_LOCK:
                _TELEGRAM_SENT_JOBS.add(job_id)
                _TELEGRAM_IP_TIMESTAMPS[ip].append(now_ts)

            return jsonify({"ok": True, "message": "Đã gửi video thành công về TAIO.CLUB!"})
    except Exception as e:
        return jsonify({"error": f"Lỗi gửi Telegram: {e}"}), 400


@app.errorhandler(413)
def request_entity_too_large(error):
    """Xử lý lỗi tải tệp vượt quá dung lượng cho phép."""
    return jsonify({"error": f"Dung lượng tệp vượt quá giới hạn {max_upload_mb} MB cho phép."}), 413

#!/usr/bin/env python3
"""
studio_cli.py - Giao diện dòng lệnh (CLI) cho TAIO Cover Studio.
Hỗ trợ: templates, render, batch, preview, suggest.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Thêm đường dẫn gốc vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.paths import BASE_DIR, OUTPUTS_DIR
from core.templates import list_templates, get_template
from core.compositor import build_preview, render_video
from core.video_probe import probe_video

SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}


def cmd_templates(args):
    """Liệt kê danh sách các mẫu lớp phủ."""
    tpls = list_templates()
    print("=" * 60)
    print("Danh sách các mẫu lớp phủ (Templates) khả dụng:")
    print("=" * 60)
    for tpl in tpls:
        t_id = tpl.get("id", "")
        t_name = tpl.get("name", "")
        t_desc = tpl.get("description", "")
        print(f"• [{t_id}] {t_name}")
        print(f"  {t_desc}")
    print("=" * 60)


def _print_progress_bar(current_file: str, progress: float):
    """Hiển thị thanh tiến độ xử lý video."""
    pct = int(round(progress * 100))
    bar_len = 30
    filled = int(round(bar_len * progress))
    bar = "=" * filled + "-" * (bar_len - filled)
    sys.stdout.write(f"\r  [{bar}] {pct}% - {current_file}")
    sys.stdout.flush()
    if progress >= 1.0:
        sys.stdout.write("\n")


def cmd_render(args):
    """Xuất một video với lớp phủ."""
    video_path = args.video
    if not os.path.exists(video_path):
        print(f"Lỗi: Không tìm thấy file video: {video_path}", file=sys.stderr)
        sys.exit(1)

    template_id = args.template or "footer_band"
    tpl = get_template(template_id)
    if not tpl:
        print(f"Lỗi: Không tìm thấy template '{template_id}'", file=sys.stderr)
        sys.exit(1)

    caption = args.caption or ""
    if args.auto_caption and not caption:
        try:
            from ai.suggest import get_caption_suggestions
            print("Đang phân tích khung hình và gợi ý caption bằng AI...")
            suggestions = get_caption_suggestions(
                video_path=video_path,
                context=args.context or "",
                style=args.style or "tin_tuc",
                n=1,
            )
            captions_list = suggestions.get("captions", [])
            if captions_list:
                caption = captions_list[0].get("text", "")
                print(f"Caption AI gợi ý: {caption}")
        except Exception as e:
            print(f"Cảnh báo: Không thể gợi ý caption bằng AI ({e}). Tiếp tục với caption mặc định.")

    out_path = args.output
    print(f"Bắt đầu xuất video: {video_path}")
    print(f"Template: {template_id}")
    print(f"Caption: {caption}")

    def on_prog(p):
        _print_progress_bar(Path(video_path).name, p)

    try:
        res = render_video(
            video_path=video_path,
            template=tpl,
            caption=caption,
            output_path=out_path,
            logo_path=args.logo,
            on_progress=on_prog,
        )
        print(f"\n Xuất video thành công: {res['output']}")
        if res.get("warnings"):
            for w in res["warnings"]:
                print(f"  Cảnh báo: {w}")
    except Exception as e:
        print(f"\n Lỗi khi xuất video: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_preview(args):
    """Xuất 1 ảnh xem trước tại thời điểm cụ thể."""
    video_path = args.video
    if not os.path.exists(video_path):
        print(f"Lỗi: Không tìm thấy file video: {video_path}", file=sys.stderr)
        sys.exit(1)

    template_id = args.template or "footer_band"
    tpl = get_template(template_id)
    if not tpl:
        print(f"Lỗi: Không tìm thấy template '{template_id}'", file=sys.stderr)
        sys.exit(1)

    caption = args.caption or ""
    time_sec = float(args.at or 1.0)
    out_path = args.output or "preview.jpg"

    try:
        img, warnings = build_preview(
            video_path=video_path,
            template=tpl,
            caption=caption,
            time_sec=time_sec,
            logo_path=args.logo,
        )
        img.save(out_path, quality=95)
        print(f" Đã lưu ảnh xem trước tại t={time_sec}s vào: {out_path}")
        if warnings:
            for w in warnings:
                print(f"  Cảnh báo: {w}")
    except Exception as e:
        print(f" Lỗi khi tạo xem trước: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_batch(args):
    """Xử lý hàng loạt video trong một thư mục."""
    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        print(f"Lỗi: Thư mục không tồn tại: {folder}", file=sys.stderr)
        sys.exit(1)

    template_id = args.template or "footer_band"
    tpl = get_template(template_id)
    if not tpl:
        print(f"Lỗi: Không tìm thấy template '{template_id}'", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir) if args.out_dir else folder / "taio_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Tìm tất cả video
    video_files = sorted([f for f in folder.iterdir() if f.suffix.lower() in SUPPORTED_VIDEO_EXTS])
    if not video_files:
        print(f"Không tìm thấy video nào trong {folder}")
        return

    total = len(video_files)
    print(f"Tìm thấy {total} video cần xử lý. Bắt đầu xử lý hàng loạt...")

    for idx, v_file in enumerate(video_files, start=1):
        v_name = v_file.name
        print(f"\n[{idx}/{total}] Đang xử lý: {v_name}")
        out_file = str(out_dir / f"{v_file.stem}_taio.mp4")

        caption = args.caption or ""
        if args.auto_caption and not caption:
            try:
                from ai.suggest import get_caption_suggestions
                sug = get_caption_suggestions(
                    video_path=str(v_file),
                    context=args.context or "",
                    style=args.style or "tin_tuc",
                    n=1,
                )
                captions_list = sug.get("captions", [])
                if captions_list:
                    caption = captions_list[0].get("text", "")
            except Exception:
                caption = v_file.stem

        def on_prog(p):
            _print_progress_bar(f"[{idx}/{total}] {v_name}", p)

        try:
            render_video(
                video_path=str(v_file),
                template=tpl,
                caption=caption,
                output_path=out_file,
                logo_path=args.logo,
                on_progress=on_prog,
            )
            print(f" Hoàn tất: {out_file}")
        except Exception as e:
            print(f" Lỗi khi xử lý {v_name}: {e}")

    print("\n Xử lý hàng loạt hoàn tất!")


def cmd_suggest(args):
    """Gợi ý caption bằng AI qua CLI."""
    video_path = args.video
    if not os.path.exists(video_path):
        print(f"Lỗi: Không tìm thấy video: {video_path}", file=sys.stderr)
        sys.exit(1)

    try:
        from ai.suggest import get_caption_suggestions
        res = get_caption_suggestions(
            video_path=video_path,
            context=args.context or "",
            style=args.style or "tin_tuc",
            provider=args.provider,
            n=int(args.n or 5),
        )
        print("=" * 60)
        print(f"Tóm tắt video: {res.get('summary', '')}")
        print("=" * 60)
        captions = res.get("captions", [])
        for i, c in enumerate(captions, 1):
            print(f"\n{i}. {c.get('text', '')}")
            print(f"   [Góc: {c.get('angle', '')}] - {c.get('why', '')}")
        print("=" * 60)
    except Exception as e:
        print(f" Lỗi gợi ý caption: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="TAIO Cover Studio CLI - Công cụ gắn bìa thương hiệu và tạo caption tự động cho video ngắn.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Lệnh cần thực thi")

    # 1. templates
    subparsers.add_parser("templates", help="Liệt kê danh sách các mẫu lớp phủ")

    # 2. render
    p_render = subparsers.add_parser("render", help="Xuất video có gắn lớp phủ")
    p_render.add_argument("video", help="Đường dẫn file video đầu vào")
    p_render.add_argument("-t", "--template", default="footer_band", help="ID mẫu lớp phủ (mặc định: footer_band)")
    p_render.add_argument("-c", "--caption", default="", help="Nội dung caption (hỗ trợ **từ nhấn**)")
    p_render.add_argument("--logo", default=None, help="Đường dẫn file logo tuỳ chọn")
    p_render.add_argument("--auto-caption", action="store_true", help="Tự động gợi ý caption bằng AI")
    p_render.add_argument("--context", default="", help="Ngữ cảnh / kịch bản video để AI viết caption")
    p_render.add_argument("--style", default="tin_tuc", choices=["tin_tuc", "giao_duc", "ban_hang", "giai_tri"], help="Phong cách caption")
    p_render.add_argument("-o", "--output", default=None, help="Đường dẫn file xuất ra")

    # 3. preview
    p_prev = subparsers.add_parser("preview", help="Tạo ảnh xem trước tại một mốc thời gian")
    p_prev.add_argument("video", help="Đường dẫn file video")
    p_prev.add_argument("-t", "--template", default="footer_band", help="ID mẫu lớp phủ")
    p_prev.add_argument("-c", "--caption", default="", help="Nội dung caption")
    p_prev.add_argument("--at", default=1.0, type=float, help="Thời điểm lấy khung hình (giây, mặc định: 1.0)")
    p_prev.add_argument("--logo", default=None, help="Đường dẫn file logo tuỳ chọn")
    p_prev.add_argument("-o", "--output", default="preview.jpg", help="File ảnh xuất ra (mặc định: preview.jpg)")

    # 4. batch
    p_batch = subparsers.add_parser("batch", help="Xử lý hàng loạt video trong một thư mục")
    p_batch.add_argument("folder", help="Thư mục chứa các file video")
    p_batch.add_argument("-t", "--template", default="footer_band", help="ID mẫu lớp phủ")
    p_batch.add_argument("-c", "--caption", default="", help="Caption cố định (nếu không dùng auto-caption)")
    p_batch.add_argument("--auto-caption", action="store_true", help="Tự động sinh caption AI cho từng video")
    p_batch.add_argument("--context", default="", help="Ngữ cảnh chung")
    p_batch.add_argument("--style", default="tin_tuc", help="Phong cách caption")
    p_batch.add_argument("--logo", default=None, help="Đường dẫn logo")
    p_batch.add_argument("--out-dir", default=None, help="Thư mục lưu video đã xuất")

    # 5. suggest
    p_sug = subparsers.add_parser("suggest", help="Gợi ý caption bằng AI")
    p_sug.add_argument("video", help="Đường dẫn file video")
    p_sug.add_argument("--context", default="", help="Ngữ cảnh / kịch bản / từ khoá")
    p_sug.add_argument("--style", default="tin_tuc", choices=["tin_tuc", "giao_duc", "ban_hang", "giai_tri"])
    p_sug.add_argument("--provider", default=None, help="Nhà cung cấp AI")
    p_sug.add_argument("-n", default=5, type=int, help="Số lượng caption cần gợi ý (mặc định: 5)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "templates":
        cmd_templates(args)
    elif args.command == "render":
        cmd_render(args)
    elif args.command == "preview":
        cmd_preview(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "suggest":
        cmd_suggest(args)


if __name__ == "__main__":
    main()

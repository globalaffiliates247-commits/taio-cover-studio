"""
core/text_layout.py - Xử lý bố cục chữ, tự động co cỡ chữ, cú pháp **nhấn** / ==nhấn 2== và chuẩn hoá tiếng Việt.
Bộ nhớ đệm font LRU tối đa 32 đối tượng theo yêu cầu hiệu năng Render Free.
"""

import json
from functools import lru_cache
from pathlib import Path
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from PIL import ImageDraw, ImageFont
from core.paths import FONTS_DIR


@dataclass
class TextSpan:
    text: str
    is_accent: bool = False
    accent_type: Optional[str] = None  # None, "accent1" (**), "accent2" (==)


@dataclass
class LayoutLine:
    spans: List[TextSpan]
    width: float
    height: float


@dataclass
class LayoutResult:
    lines: List[LayoutLine]
    font: ImageFont.FreeTypeFont
    font_size: int
    total_w: float
    total_h: float
    line_height: float
    warning: Optional[str] = None


FONT_WEIGHT_MAP = {
    "black": "BeVietnamPro-Black.ttf",
    "extrabold": "BeVietnamPro-ExtraBold.ttf",
    "bold": "BeVietnamPro-Bold.ttf",
    "semibold": "BeVietnamPro-SemiBold.ttf",
}


@lru_cache(maxsize=32)
def get_font(
    weight: str = "Bold",
    size: int = 32,
    family: Optional[str] = None,
) -> ImageFont.FreeTypeFont:
    """
    Tải font từ assets/fonts theo family, độ đậm (weight) và kích thước.
    Sử dụng bộ nhớ đệm LRU tối đa 32 font object.
    """
    # 1. Tra cứu file trong fonts.json nếu có
    fonts_cfg_path = FONTS_DIR / "fonts.json"
    target_file = None

    if fonts_cfg_path.exists():
        try:
            with open(fonts_cfg_path, "r", encoding="utf-8") as f:
                font_list = json.load(f)
                for item in font_list:
                    if family and (item.get("id") == family or item.get("name") == family):
                        weights = item.get("weights", [])
                        for w in weights:
                            if w.get("weight", "").lower() == weight.lower():
                                target_file = w.get("file")
                                break
                        if not target_file and weights:
                            target_file = weights[0].get("file")
                        break
        except Exception:
            pass

    if not target_file:
        target_file = FONT_WEIGHT_MAP.get(weight.lower(), "BeVietnamPro-Bold.ttf")

    font_path = FONTS_DIR / target_file
    if font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except Exception:
            pass

    # Fallback tìm kiếm ttf trong FONTS_DIR
    for cand in FONTS_DIR.glob("*.ttf"):
        try:
            return ImageFont.truetype(str(cand), size=size)
        except Exception:
            pass

    return ImageFont.load_default()


def normalize_accent_syntax(text: str) -> str:
    """Chuẩn hoá mọi biến thể dấu sao (unicode, fullwidth) về chuẩn ASCII *."""
    if not text:
        return ""
    for ch in ("＊", "∗", "٭", "★", "☆"):
        text = text.replace(ch, "*")
    return text


def parse_accent_spans(text: str) -> List[TextSpan]:
    """
    Phân tích cú pháp:
    - **từ nhấn 1**, *từ nhấn 1*, <b>từ nhấn 1</b> -> accent_type = "accent1"
    - ==từ nhấn 2== -> accent_type = "accent2"
    """
    spans: List[TextSpan] = []
    text = normalize_accent_syntax(text)

    # Khớp ==...== HOẶC **...**, *...*, <b>...</b>
    pattern = re.compile(
        r"==([^=]+?)==|(?:\*\*|<b>|<B>)(.*?)(?:\*\*|</b>|</B>)|(?<!\*)\*([^\*]+?)\*(?!\*)"
    )
    last_end = 0

    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_end:
            normal_text = text[last_end:start]
            if normal_text:
                spans.append(TextSpan(text=normal_text, is_accent=False, accent_type=None))

        # Nhánh 1: ==từ nhấn 2==
        if match.group(1) is not None:
            accent_content = match.group(1)
            accent_type = "accent2"
        else:
            accent_content = match.group(2) if match.group(2) is not None else match.group(3)
            accent_type = "accent1"

        if accent_content:
            l_spaces = len(accent_content) - len(accent_content.lstrip())
            r_spaces = len(accent_content) - len(accent_content.rstrip())
            if l_spaces > 0:
                spans.append(TextSpan(text=accent_content[:l_spaces], is_accent=False, accent_type=None))

            core_content = accent_content.strip()
            if core_content:
                spans.append(TextSpan(text=core_content, is_accent=True, accent_type=accent_type))

            if r_spaces > 0:
                spans.append(TextSpan(text=accent_content[-r_spaces:], is_accent=False, accent_type=None))

        last_end = end

    if last_end < len(text):
        spans.append(TextSpan(text=text[last_end:], is_accent=False, accent_type=None))

    return spans


def prepare_caption_text(
    raw_text: str,
    uppercase: bool = True,
    case_mode: Optional[str] = None,
) -> str:
    """Chuẩn hoá Unicode sang NFC và áp dụng kiểu chữ hoa (preserve, uppercase, title)."""
    if not raw_text:
        return ""
    norm = unicodedata.normalize("NFC", raw_text)

    if case_mode == "title":
        # Viết hoa chữ cái đầu mỗi từ
        def _cap(m):
            w = m.group(0)
            return w[0].upper() + w[1:].lower() if len(w) > 1 else w.upper()
        norm = re.sub(r"[^\W\d_]+", _cap, norm)
    elif case_mode == "preserve":
        pass
    elif case_mode == "uppercase" or uppercase:
        norm = norm.upper()
    return norm


def measure_span(
    span_text: str,
    font: ImageFont.FreeTypeFont,
    letter_spacing: float = 0.0,
) -> float:
    """Đo chiều rộng của một đoạn văn bản chính xác (có tính letter-spacing)."""
    if not span_text:
        return 0.0
    try:
        base_w = float(font.getlength(span_text))
    except Exception:
        bbox = font.getbbox(span_text)
        base_w = float(bbox[2] - bbox[0]) if bbox else 0.0

    if letter_spacing > 0.0 and len(span_text) > 1:
        f_size = getattr(font, "size", 32)
        base_w += (len(span_text) - 1) * (letter_spacing * f_size)

    return base_w


def wrap_text_into_lines(
    text: str,
    font: ImageFont.FreeTypeFont,
    box_w: float,
    letter_spacing: float = 0.0,
    wrap: bool = True,
) -> List[LayoutLine]:
    """
    Chia văn bản có cú pháp **nhấn** và xuống dòng thủ công thành các dòng vừa vặn box_w.
    Nếu wrap=False, chỉ ngắt dòng tại ký tự \n thủ công.
    """
    paragraphs = text.split("\n")
    all_lines: List[LayoutLine] = []

    sample_bbox = font.getbbox("ÁyTgHqj")
    base_line_h = float(sample_bbox[3] - sample_bbox[1]) if sample_bbox else 20.0

    for para in paragraphs:
        if not para.strip():
            all_lines.append(LayoutLine(spans=[TextSpan("", False, None)], width=0.0, height=base_line_h))
            continue

        spans = parse_accent_spans(para)

        if not wrap:
            line_w = sum(measure_span(s.text, font, letter_spacing=letter_spacing) for s in spans)
            all_lines.append(LayoutLine(spans=spans, width=line_w, height=base_line_h))
            continue

        words_with_attr: List[Tuple[str, bool, Optional[str]]] = []
        for s in spans:
            parts = re.split(r"(\s+)", s.text)
            for p in parts:
                if p:
                    words_with_attr.append((p, s.is_accent, s.accent_type))

        cur_spans: List[TextSpan] = []
        cur_w = 0.0

        for token, is_accent, acc_type in words_with_attr:
            token_w = measure_span(token, font, letter_spacing=letter_spacing)

            if token.isspace():
                if cur_spans:
                    cur_spans.append(TextSpan(token, is_accent, acc_type))
                    cur_w += token_w
                continue

            if cur_spans and (cur_w + token_w > box_w):
                all_lines.append(LayoutLine(spans=cur_spans, width=cur_w, height=base_line_h))
                cur_spans = [TextSpan(token, is_accent, acc_type)]
                cur_w = token_w
            else:
                cur_spans.append(TextSpan(token, is_accent, acc_type))
                cur_w += token_w

        if cur_spans:
            all_lines.append(LayoutLine(spans=cur_spans, width=cur_w, height=base_line_h))

    return all_lines


def compute_text_layout(
    raw_text: str,
    box_w: float,
    box_h: float,
    unit: int,
    weight: str = "Black",
    uppercase: bool = True,
    case_mode: Optional[str] = None,
    max_size_ratio: float = 0.075,
    min_size_ratio: float = 0.032,
    line_spacing: float = 1.18,
    max_lines: int = 4,
    fixed_size: Optional[int] = None,
    family: Optional[str] = None,
    letter_spacing: float = 0.0,
    wrap: bool = True,
) -> LayoutResult:
    """
    Tính toán cỡ chữ tự co hoặc cố định sao cho vừa vặn box_w, box_h và max_lines.
    Nếu vượt quá giới hạn, trả về cảnh báo theo đặc tả.
    """
    text = prepare_caption_text(raw_text, uppercase=uppercase, case_mode=case_mode)

    warning = None

    # Nếu có cỡ chữ cố định (fixed size)
    if fixed_size is not None and fixed_size > 0:
        best_size = int(fixed_size)
        font = get_font(weight=weight, size=best_size, family=family)
        best_lines = wrap_text_into_lines(text, font, box_w, letter_spacing=letter_spacing, wrap=wrap)
        line_h = float(best_size) * line_spacing
        total_h = len(best_lines) * line_h

        if not wrap:
            for idx, l in enumerate(best_lines):
                if l.width > box_w:
                    warning = f"Dòng {idx + 1} vượt khung — rút ngắn hoặc bật Tự xuống dòng."
                    break

        if not warning and (len(best_lines) > max_lines or total_h > box_h):
            warning = "Caption dài quá khung — nên rút gọn hoặc giảm cỡ chữ."
    else:
        # Chế độ tự co cỡ chữ (Auto shrink)
        max_px = max(int(round(max_size_ratio * unit)), 12)
        min_px = max(int(round(min_size_ratio * unit)), 10)
        if min_px > max_px:
            min_px = max_px

        low = min_px
        high = max_px
        best_size = min_px
        best_lines = []
        best_fits = False

        while low <= high:
            mid = (low + high) // 2
            font = get_font(weight=weight, size=mid, family=family)
            lines = wrap_text_into_lines(text, font, box_w, letter_spacing=letter_spacing, wrap=wrap)
            line_h = float(mid) * line_spacing
            total_h = len(lines) * line_h

            fits_lines = len(lines) <= max_lines
            fits_height = total_h <= box_h
            fits_width = all(l.width <= box_w for l in lines) if not wrap else True

            if fits_lines and fits_height and fits_width:
                best_size = mid
                best_lines = lines
                best_fits = True
                low = mid + 1
            else:
                high = mid - 1

        if not best_fits:
            best_size = min_px
            font = get_font(weight=weight, size=best_size, family=family)
            best_lines = wrap_text_into_lines(text, font, box_w, letter_spacing=letter_spacing, wrap=wrap)
            warning = "Caption dài quá khung — nên rút gọn."

    font = get_font(weight=weight, size=best_size, family=family)
    line_h = float(best_size) * line_spacing
    total_h = len(best_lines) * line_h
    max_w = max((line.width for line in best_lines), default=0.0)

    # Kiểm tra hiệu ứng Von Restorff: cảnh báo nếu nhấn quá 3 cụm từ
    total_accents = len(
        re.findall(r"==[^=]+?==|(?:\*\*|<b>|<B>).*?(?:\*\*|</b>|</B>)|(?<!\*)\*[^\*]+?\*(?!\*)", raw_text)
    )
    if total_accents > 3 and not warning:
        warning = "Nhấn quá 3 cụm từ có thể làm giảm hiệu quả thu hút thị giác."

    return LayoutResult(
        lines=best_lines,
        font=font,
        font_size=best_size,
        total_w=max_w,
        total_h=total_h,
        line_height=line_h,
        warning=warning,
    )

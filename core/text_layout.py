"""
core/text_layout.py - Xử lý bố cục chữ, tự động co cỡ chữ, cú pháp **nhấn** và chuẩn hoá tiếng Việt.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import ImageDraw, ImageFont
from core.paths import FONTS_DIR


@dataclass
class TextSpan:
    text: str
    is_accent: bool


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


def get_font(weight: str = "Bold", size: int = 32) -> ImageFont.FreeTypeFont:
    """Tải font Be Vietnam Pro theo độ đậm (weight) và kích thước."""
    filename = FONT_WEIGHT_MAP.get(weight.lower(), "BeVietnamPro-Bold.ttf")
    font_path = FONTS_DIR / filename

    if font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except Exception:
            pass

    # Fallback font khác nếu có
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
    # Chuyển fullwidth asterisk ＊ (U+FF0A), operator ∗ (U+2217), star ٭ (U+066D) về *
    for ch in ("＊", "∗", "٭", "★", "☆"):
        text = text.replace(ch, "*")
    return text


def parse_accent_spans(text: str) -> List[TextSpan]:
    """
    Phân tích cú pháp **từ nhấn**, *từ nhấn* hoặc <b>từ nhấn</b> thành danh sách các TextSpan.
    Tự động xử lý khoảng trắng trong/ngoài để luôn đổi màu từ khóa chuẩn xác.
    """
    spans: List[TextSpan] = []
    text = normalize_accent_syntax(text)

    # Khớp **...**, *...*, <b>...</b>
    pattern = re.compile(r"(?:\*\*|<b>|<B>)(.*?)(?:\*\*|</b>|</B>)|(?<!\*)\*([^\*]+?)\*(?!\*)")
    last_end = 0

    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_end:
            normal_text = text[last_end:start]
            if normal_text:
                spans.append(TextSpan(text=normal_text, is_accent=False))

        accent_content = match.group(1) if match.group(1) is not None else match.group(2)
        if accent_content:
            # Tách khoảng trắng ở đầu và cuối nếu có để chỉ tô màu chữ
            l_spaces = len(accent_content) - len(accent_content.lstrip())
            r_spaces = len(accent_content) - len(accent_content.rstrip())
            if l_spaces > 0:
                spans.append(TextSpan(text=accent_content[:l_spaces], is_accent=False))

            core_content = accent_content.strip()
            if core_content:
                spans.append(TextSpan(text=core_content, is_accent=True))

            if r_spaces > 0:
                spans.append(TextSpan(text=accent_content[-r_spaces:], is_accent=False))

        last_end = end

    if last_end < len(text):
        spans.append(TextSpan(text=text[last_end:], is_accent=False))

    return spans


def prepare_caption_text(raw_text: str, uppercase: bool = False) -> str:
    """Chuẩn hoá Unicode sang NFC và in hoa nếu có yêu cầu."""
    if not raw_text:
        return ""
    norm = unicodedata.normalize("NFC", raw_text)
    if uppercase:
        norm = norm.upper()
    return norm


def _measure_span(span_text: str, font: ImageFont.FreeTypeFont) -> float:
    """Đo chiều rộng của một đoạn văn bản chính xác."""
    if not span_text:
        return 0.0
    try:
        return float(font.getlength(span_text))
    except Exception:
        bbox = font.getbbox(span_text)
        return float(bbox[2] - bbox[0]) if bbox else 0.0


def wrap_text_into_lines(
    text: str,
    font: ImageFont.FreeTypeFont,
    box_w: float,
) -> List[LayoutLine]:
    """
    Chia văn bản có cú pháp **nhấn** và xuống dòng thủ công thành các dòng vừa vặn box_w.
    Không ngắt giữa từ.
    """
    paragraphs = text.split("\n")
    all_lines: List[LayoutLine] = []

    space_w = _measure_span(" ", font)
    # Lấy chiều cao chuẩn của dòng theo font
    sample_bbox = font.getbbox("ÁyTgHqj")
    base_line_h = float(sample_bbox[3] - sample_bbox[1]) if sample_bbox else 20.0

    for para in paragraphs:
        if not para.strip():
            # Dòng trống
            all_lines.append(LayoutLine(spans=[TextSpan("", False)], width=0.0, height=base_line_h))
            continue

        spans = parse_accent_spans(para)

        # Tách từng span thành các token từ để gói dòng
        words_with_attr: List[Tuple[str, bool]] = []
        for s in spans:
            # Tách từ giữ dấu cách
            parts = re.split(r"(\s+)", s.text)
            for p in parts:
                if p:
                    words_with_attr.append((p, s.is_accent))

        cur_spans: List[TextSpan] = []
        cur_w = 0.0

        for token, is_accent in words_with_attr:
            # Nếu là khoảng trắng
            if token.isspace():
                if cur_spans:
                    cur_spans.append(TextSpan(token, is_accent))
                    cur_w += _measure_span(token, font)
                continue

            token_w = _measure_span(token, font)

            # Kiểm tra nếu từ này đưa vào có vượt quá box_w không
            if cur_spans and (cur_w + token_w > box_w):
                # Ngắt dòng hiện tại
                all_lines.append(LayoutLine(spans=cur_spans, width=cur_w, height=base_line_h))
                cur_spans = [TextSpan(token, is_accent)]
                cur_w = token_w
            else:
                cur_spans.append(TextSpan(token, is_accent))
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
    max_size_ratio: float = 0.075,
    min_size_ratio: float = 0.032,
    line_spacing: float = 1.18,
    max_lines: int = 4,
) -> LayoutResult:
    """
    Tính toán cỡ chữ tự co (từ max_size xuống min_size) sao cho vừa vặn box_w, box_h và max_lines.
    Nếu vẫn không vừa ở min_size, sử dụng min_size và trả về cảnh báo.
    """
    text = prepare_caption_text(raw_text, uppercase=uppercase)

    max_px = max(int(round(max_size_ratio * unit)), 12)
    min_px = max(int(round(min_size_ratio * unit)), 10)
    if min_px > max_px:
        min_px = max_px

    # Tìm kiếm nhị phân cỡ chữ lớn nhất vừa khung
    low = min_px
    high = max_px
    best_size = min_px
    best_lines: List[LayoutLine] = []
    best_fits = False

    while low <= high:
        mid = (low + high) // 2
        font = get_font(weight, mid)
        lines = wrap_text_into_lines(text, font, box_w)
        line_h = float(mid) * line_spacing
        total_h = len(lines) * line_h

        fits_lines = len(lines) <= max_lines
        fits_height = total_h <= box_h

        if fits_lines and fits_height:
            best_size = mid
            best_lines = lines
            best_fits = True
            low = mid + 1  # Thử tìm cỡ to hơn
        else:
            high = mid - 1  # Co nhỏ lại

    warning = None
    if not best_fits:
        # Dùng min_px và tạo cảnh báo theo đặc tả
        best_size = min_px
        font = get_font(weight, best_size)
        best_lines = wrap_text_into_lines(text, font, box_w)
        warning = "Caption dài quá khung — nên rút gọn."

    font = get_font(weight, best_size)
    line_h = float(best_size) * line_spacing
    total_h = len(best_lines) * line_h
    max_w = max((line.width for line in best_lines), default=0.0)

    return LayoutResult(
        lines=best_lines,
        font=font,
        font_size=best_size,
        total_w=max_w,
        total_h=total_h,
        line_height=line_h,
        warning=warning,
    )

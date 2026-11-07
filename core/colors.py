"""
core/colors.py - Xử lý và phân tích cú pháp mã màu hex thành tuple RGBA (0-255).
Bổ sung các hàm helper: with_alpha, darken, contrast_ratio chuẩn WCAG 2.1 (v1.3.0).
"""

from typing import Tuple, Union


def parse_hex_color(
    hex_str: Union[str, Tuple[int, int, int, int], None],
    default_alpha: int = 255,
) -> Tuple[int, int, int, int]:
    """
    Phân tích chuỗi màu hex (#RGB, #RGBA, #RRGGBB, #RRGGBBAA) thành RGBA (0-255).
    Nếu truyền vào đã là tuple RGBA, trả về tuple chuẩn.
    """
    if not hex_str:
        return (0, 0, 0, default_alpha)

    if isinstance(hex_str, (tuple, list)):
        if len(hex_str) == 3:
            return (int(hex_str[0]), int(hex_str[1]), int(hex_str[2]), default_alpha)
        elif len(hex_str) >= 4:
            return (int(hex_str[0]), int(hex_str[1]), int(hex_str[2]), int(hex_str[3]))

    s = str(hex_str).strip()
    if s.startswith("#"):
        s = s[1:]

    # #RGB
    if len(s) == 3:
        r = int(s[0] * 2, 16)
        g = int(s[1] * 2, 16)
        b = int(s[2] * 2, 16)
        return (r, g, b, default_alpha)

    # #RGBA
    if len(s) == 4:
        r = int(s[0] * 2, 16)
        g = int(s[1] * 2, 16)
        b = int(s[2] * 2, 16)
        a = int(s[3] * 2, 16)
        return (r, g, b, a)

    # #RRGGBB
    if len(s) == 6:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        return (r, g, b, default_alpha)

    # #RRGGBBAA
    if len(s) == 8:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        a = int(s[6:8], 16)
        return (r, g, b, a)

    # Fallback màu chuẩn thông dụng
    named = {
        "white": (255, 255, 255, default_alpha),
        "black": (0, 0, 0, default_alpha),
        "transparent": (0, 0, 0, 0),
        "yellow": (255, 211, 77, default_alpha),
        "gold": (255, 211, 77, default_alpha),
        "accent": (255, 211, 77, default_alpha),
        "$accent": (255, 211, 77, default_alpha),
    }
    if s.lower() in named:
        return named[s.lower()]

    return (0, 0, 0, default_alpha)


def with_alpha(
    color_val: Union[str, Tuple[int, ...], None],
    alpha: Union[int, float],
) -> Tuple[int, int, int, int]:
    """
    Gán kênh alpha mới cho màu (alpha có thể là float 0..1 hoặc int 0..255).
    """
    c = parse_hex_color(color_val)
    if isinstance(alpha, float) and alpha <= 1.0:
        a = max(0, min(255, int(round(alpha * 255))))
    else:
        a = max(0, min(255, int(round(alpha))))
    return (c[0], c[1], c[2], a)


def darken(
    color_val: Union[str, Tuple[int, ...], None],
    factor: float,
) -> Tuple[int, int, int, int]:
    """
    Làm tối màu đi theo tỉ lệ factor (0.0 đến 1.0). Ví dụ 0.25 = tối đi 25%.
    Giữ nguyên kênh alpha.
    """
    c = parse_hex_color(color_val)
    f = max(0.0, min(1.0, float(factor)))
    mult = 1.0 - f
    r = max(0, min(255, int(round(c[0] * mult))))
    g = max(0, min(255, int(round(c[1] * mult))))
    b = max(0, min(255, int(round(c[2] * mult))))
    return (r, g, b, c[3])


def _relative_luminance(c: Tuple[int, int, int, int]) -> float:
    """Tính độ chói tương đối (relative luminance) theo WCAG 2.1."""
    def _lin(channel: int) -> float:
        v = channel / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r_lin = _lin(c[0])
    g_lin = _lin(c[1])
    b_lin = _lin(c[2])
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(
    c1: Union[str, Tuple[int, ...], None],
    c2: Union[str, Tuple[int, ...], None],
) -> float:
    """
    Tính tỉ lệ tương phản (contrast ratio) giữa 2 màu theo chuẩn WCAG 2.1.
    Trả về giá trị từ 1.0 đến 21.0.
    """
    col1 = parse_hex_color(c1)
    col2 = parse_hex_color(c2)

    l1 = _relative_luminance(col1)
    l2 = _relative_luminance(col2)

    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def rgba_to_hex(c: Tuple[int, int, int, int], include_alpha: bool = False) -> str:
    """Chuyển tuple RGBA thành mã hex string #RRGGBB hoặc #RRGGBBAA."""
    if include_alpha:
        return f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}{c[3]:02X}"
    return f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}"

"""
core/colors.py - Xử lý và phân tích cú pháp mã màu hex thành tuple RGBA (0-255).
"""

from typing import Tuple, Union


def parse_hex_color(hex_str: Union[str, Tuple[int, int, int, int], None], default_alpha: int = 255) -> Tuple[int, int, int, int]:
    """
    Phân tích chuỗi màu hex (#RGB, #RGBA, #RRGGBB, #RRGGBBAA) thành RGBA (0-255).
    Nếu truyền vào đã là tuple RGBA, trả về chính nó.
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
    }
    if s.lower() in named:
        return named[s.lower()]

    return (0, 0, 0, default_alpha)

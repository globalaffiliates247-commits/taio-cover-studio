"""
ai/prompt.py - Xây dựng prompt gợi ý caption theo tâm lý học hành vi và phân tích JSON phản hồi.
"""

import json
import re
from typing import Any, Dict, List

STYLE_DESCRIPTIONS = {
    "tin_tuc": "Thời sự / Tin tức: Khách quan, nhịp điệu nhanh, giật gân có cơ sở, thôi thúc bấm xem ngay lập tức.",
    "giao_duc": "Giáo dục / Chia sẻ: Gợi mở bài học, làm sáng tỏ bí quyết, giúp người xem nhận ra giải pháp cho vấn đề.",
    "ban_hang": "Bán hàng / Chuyển đổi: Nêu bật giá trị thực tế, kích thích ham muốn, giải quyết nỗi đau khách hàng.",
    "giai_tri": "Giải trí / Viral: Tò mò cao độ, bắt trend, hài hước, tạo cảm giác bất ngờ thú vị.",
}


def build_system_prompt(brand_voice: str = "") -> str:
    """Tạo lời nhắc hệ thống (System Prompt) cho AI."""
    voice_part = f"\nGiọng văn thương hiệu yêu cầu: {brand_voice}" if brand_voice else ""
    return (
        "Bạn là chuyên gia biên tập video ngắn và sáng tạo tiêu đề (caption/hook) hàng đầu cho TikTok, Reels và Shorts. "
        "Nhiệm vụ của bạn là xem các khung hình trích từ video kèm ngữ cảnh để viết các caption bìa video cực kỳ hấp dẫn, "
        "kích thích người xem dừng lại theo các nguyên lý tâm lý học hành vi: "
        "Khoảng trống thông tin (Loewenstein), Nguyên lý tương phản (Cialdini), và Tâm lý sợ mất mát (Kahneman & Tversky)."
        f"{voice_part}\n"
        "BẠN PHẢI TRẢ VỀ DUY NHẤT MỘT KHỐI JSON HỢP LỆ, KHÔNG KÈM BẤT KỲ VĂN BẢN NÀO BÊN NGOÀI."
    )


def build_user_prompt(
    context: str = "",
    style: str = "tin_tuc",
    n: int = 5,
) -> str:
    """Tạo prompt chi tiết cho từng video cụ thể."""
    style_desc = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["tin_tuc"])
    ctx_desc = f"Ngữ cảnh / kịch bản / ghi chú từ người dùng: '{context}'" if context else "Không có ngữ cảnh bổ sung, hãy quan sát kỹ nội dung trong 3 khung hình."

    return (
        f"Hãy quan sát 3 khung hình đính kèm và phân tích nội dung video.\n"
        f"{ctx_desc}\n"
        f"Phong cách biên tập: {style_desc}\n\n"
        f"Yêu cầu:\n"
        f"1. Tóm tắt nội dung video trong 1 câu ngắn gọn (summary).\n"
        f"2. Đề xuất đúng {n} caption bìa video bằng tiếng Việt có dấu, đáp ứng nghiêm ngặt các quy tắc sau:\n"
        f"   - Độ dài: Mỗi caption KHÔNG QUÁ 80 ký tự.\n"
        f"   - Cú pháp nhấn: Phải có từ 1 đến 3 cụm từ được bao bọc bởi cú pháp **từ nhấn** (ví dụ: Bí quyết **tăng doanh thu** chỉ sau **3 ngày**).\n"
        f"   - Mỗi caption theo một góc tiếp cận tâm lý khác nhau thuộc nhóm: 'curiosity_gap' (khoảng trống tò mò), 'number' (con số cụ thể), 'contrast' (nghịch lý / tương phản), 'question' (câu hỏi trăn trở), 'stakes' (hệ quả / cảnh báo).\n"
        f"   - Tuyệt đối trung thực, không bịa đặt dữ liệu không có trong ảnh hoặc ngữ cảnh.\n\n"
        f"Định dạng phản hồi BẮT BUỘC là JSON theo cấu trúc sau:\n"
        f"{{\n"
        f'  "summary": "Tóm tắt ngắn gọn nội dung video...",\n'
        f'  "captions": [\n'
        f'    {{"text": "Bí mật về **cách làm giàu** ít ai biết", "angle": "curiosity_gap", "why": "Gợi sự tò mò mạnh mẽ"}},\n'
        f'    {{"text": "**3 bước** để tối ưu chi phí ngay hôm nay", "angle": "number", "why": "Rõ ràng, dễ tiếp thu"}}\n'
        f"  ]\n"
        f"}}"
    )


def parse_ai_response(raw_text: str) -> Dict[str, Any]:
    """
    Phân tích JSON từ phản hồi của model, chịu được định dạng markdown ```json ... ``` hoặc chữ thừa.
    """
    if not raw_text:
        raise ValueError("Phản hồi từ AI rỗng.")

    text = raw_text.strip()

    # Bỏ markdown code fences nếu có
    if "```" in text:
        # Tìm khối ```json ... ``` hoặc ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()

    # Tìm vị trí { đầu tiên và } cuối cùng
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = text[first_brace : last_brace + 1]
    else:
        json_str = text

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Không thể phân tích định dạng JSON từ phản hồi AI: {e}\nNội dung gốc: {raw_text[:200]}")

    if not isinstance(data, dict):
        raise ValueError("Dữ liệu phản hồi AI không phải đối tượng JSON.")

    summary = data.get("summary", "")
    captions = data.get("captions", [])

    if not isinstance(captions, list) or len(captions) == 0:
        raise ValueError("Phản hồi AI không chứa danh sách caption hợp lệ.")

    # Làm sạch từng caption
    clean_captions = []
    for c in captions:
        if isinstance(c, dict):
            c_text = str(c.get("text", "")).strip()
            if c_text:
                clean_captions.append({
                    "text": c_text,
                    "angle": str(c.get("angle", "curiosity_gap")),
                    "why": str(c.get("why", "")),
                })

    return {
        "summary": summary,
        "captions": clean_captions,
    }

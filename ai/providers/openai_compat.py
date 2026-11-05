"""
ai/providers/openai_compat.py - Tích hợp các API tương thích chuẩn OpenAI Chat Completions:
(OpenAI GPT-4o, Google Gemini, OpenRouter, DeepSeek, Ollama, LM Studio).
"""

import base64
import io
import json
from typing import Any, Dict, List
from PIL import Image

from ai.prompt import parse_ai_response
from ai.providers.http import post_json


def _image_to_base64_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def call_openai_compat(
    config: Dict[str, Any],
    frames: List[Image.Image],
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, Any]:
    """Gọi OpenAI-compatible Chat Completions API với các ảnh khung hình."""
    api_key = config.get("resolved_api_key", "")
    endpoint = config.get("endpoint", "https://api.openai.com/v1/chat/completions")
    model = config.get("model", "gpt-4o")

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # OpenRouter headers bổ sung nếu có
    if "openrouter" in endpoint:
        headers["HTTP-Referer"] = "https://taio.club"
        headers["X-Title"] = "TAIO Cover Studio"

    user_contents: List[Dict[str, Any]] = [
        {"type": "text", "text": user_prompt}
    ]

    for frame in frames:
        url_data = _image_to_base64_url(frame)
        user_contents.append({
            "type": "image_url",
            "image_url": {"url": url_data},
        })

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_contents},
        ],
        "temperature": 0.7,
    }

    status, resp_body = post_json(endpoint, headers, payload, timeout=60)
    if status != 200:
        raise RuntimeError(f"API AI ({config.get('label', 'OpenAI-compat')}) trả về lỗi {status}: {resp_body}")

    try:
        data = json.loads(resp_body)
        raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        raise RuntimeError(f"Không thể đọc kết quả từ phản hồi AI: {e}\n{resp_body}")

    return parse_ai_response(raw_text)

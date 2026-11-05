"""
ai/providers/anthropic_provider.py - Tích hợp Anthropic Claude Messages API (Claude 3.5 Sonnet).
"""

import base64
import io
import json
from typing import Any, Dict, List
from PIL import Image

from ai.prompt import parse_ai_response
from ai.providers.http import post_json


def _image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def call_anthropic(
    config: Dict[str, Any],
    frames: List[Image.Image],
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, Any]:
    """Gọi Claude Messages API với các ảnh đính kèm."""
    api_key = config.get("resolved_api_key", "")
    endpoint = config.get("endpoint", "https://api.anthropic.com/v1/messages")
    model = config.get("model", "claude-3-5-sonnet-20241022")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    content_blocks: List[Dict[str, Any]] = []

    # Đính kèm ảnh base64
    for frame in frames:
        b64_data = _image_to_base64(frame)
        content_blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": b64_data,
            },
        })

    # Đính kèm lời nhắc
    content_blocks.append({
        "type": "text",
        "text": user_prompt,
    })

    payload = {
        "model": model,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": content_blocks,
            }
        ],
    }

    status, resp_body = post_json(endpoint, headers, payload, timeout=60)
    if status != 200:
        raise RuntimeError(f"Anthropic API trả về mã lỗi {status}: {resp_body}")

    try:
        data = json.loads(resp_body)
        raw_text = data.get("content", [{}])[0].get("text", "")
    except Exception as e:
        raise RuntimeError(f"Không thể đọc phản hồi từ Claude: {e}\n{resp_body}")

    return parse_ai_response(raw_text)

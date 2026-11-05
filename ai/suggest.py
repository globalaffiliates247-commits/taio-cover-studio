"""
ai/suggest.py - Điều phối quy trình phân tích video và gợi ý caption bằng AI.
"""

from typing import Any, Callable, Dict, List, Optional

from core.brand import load_brand_kit
from core.frames import extract_ai_frames
from core.video_probe import probe_video

from ai.prompt import build_system_prompt, build_user_prompt
from ai.providers.anthropic_provider import call_anthropic
from ai.providers.openai_compat import call_openai_compat
from ai.settings import get_provider_config

# Bảng đăng ký các loại adapter nhà cung cấp AI
PROVIDER_TYPES: Dict[str, Callable] = {
    "anthropic": call_anthropic,
    "openai_compat": call_openai_compat,
}


def get_caption_suggestions(
    video_path: str,
    context: str = "",
    style: str = "tin_tuc",
    provider: Optional[str] = None,
    n: int = 5,
) -> Dict[str, Any]:
    """
    Trích xuất 3 khung hình từ video và gửi đến nhà cung cấp AI để nhận các gợi ý caption.
    """
    info = probe_video(video_path)
    frames = extract_ai_frames(video_path, duration=info.duration, n_frames=3, max_edge=768)

    brand = load_brand_kit()
    brand_voice = brand.get("voice", "")

    system_prompt = build_system_prompt(brand_voice=brand_voice)
    user_prompt = build_user_prompt(context=context, style=style, n=n)

    cfg = get_provider_config(provider)
    p_type = cfg.get("type", "openai_compat")

    adapter = PROVIDER_TYPES.get(p_type)
    if not adapter:
        raise ValueError(f"Loại nhà cung cấp AI không được hỗ trợ: '{p_type}'")

    res = adapter(
        config=cfg,
        frames=frames,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    return {
        "summary": res.get("summary", ""),
        "captions": res.get("captions", []),
        "provider": cfg.get("id"),
        "model": cfg.get("model"),
    }

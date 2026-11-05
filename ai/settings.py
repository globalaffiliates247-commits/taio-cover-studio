"""
ai/settings.py - Đọc và quản lý cấu hình các nhà cung cấp AI.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.paths import CONFIG_DIR


def load_raw_settings() -> Dict[str, Any]:
    """Đọc tệp cấu hình settings.json (hoặc settings.example.json)."""
    user_settings = CONFIG_DIR / "settings.json"
    example_settings = CONFIG_DIR / "settings.example.json"

    target_file = user_settings if user_settings.exists() else example_settings
    if not target_file.exists():
        return {"default_provider": "gemini", "providers": {}}

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Cảnh báo: Không thể đọc cấu hình {target_file}: {e}")
        return {"default_provider": "gemini", "providers": {}}


def get_default_provider_id() -> str:
    """Lấy ID nhà cung cấp mặc định (biến môi trường DEFAULT_AI_PROVIDER được ưu tiên)."""
    env_default = os.getenv("DEFAULT_AI_PROVIDER", "").strip()
    if env_default:
        return env_default
    settings = load_raw_settings()
    return settings.get("default_provider", "gemini")


def get_provider_config(provider_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Lấy thông tin cấu hình chi tiết và API key của một nhà cung cấp.
    Ném lỗi tiếng Việt nếu thiếu API key hoặc nhà cung cấp không tồn tại.
    """
    if not provider_id:
        provider_id = get_default_provider_id()

    settings = load_raw_settings()
    providers = settings.get("providers", {})
    if provider_id not in providers:
        raise ValueError(f"Không tìm thấy nhà cung cấp AI: '{provider_id}'")

    cfg = dict(providers[provider_id])
    cfg["id"] = provider_id

    # Tìm API Key
    api_key = cfg.get("api_key", "").strip()
    api_key_env = cfg.get("api_key_env", "").strip()

    if not api_key and api_key_env:
        api_key = os.getenv(api_key_env, "").strip()

    if not api_key:
        # Nếu endpoint là local ollama thì không bắt buộc key
        if "localhost" not in cfg.get("endpoint", "") and "127.0.0.1" not in cfg.get("endpoint", ""):
            env_hint = f"biến môi trường '{api_key_env}'" if api_key_env else "trường 'api_key'"
            raise ValueError(
                f"Chưa cấu hình API Key cho nhà cung cấp AI '{cfg.get('label', provider_id)}'. "
                f"Vui lòng thiết lập {env_hint} trước khi sử dụng."
            )

    cfg["resolved_api_key"] = api_key
    return cfg


def list_ui_providers() -> List[Dict[str, Any]]:
    """Trả về danh sách nhà cung cấp đã được làm sạch để gửi cho giao diện Web/API."""
    settings = load_raw_settings()
    providers = settings.get("providers", {})
    result = []

    for pid, pdata in providers.items():
        api_key = pdata.get("api_key", "").strip()
        api_key_env = pdata.get("api_key_env", "").strip()
        is_ready = bool(api_key or (api_key_env and os.getenv(api_key_env, "").strip()))
        if "localhost" in pdata.get("endpoint", "") or "127.0.0.1" in pdata.get("endpoint", ""):
            is_ready = True

        result.append({
            "id": pid,
            "label": pdata.get("label", pid),
            "model": pdata.get("model", ""),
            "ready": is_ready,
        })

    return result

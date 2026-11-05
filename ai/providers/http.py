"""
ai/providers/http.py - Bộ gửi HTTP request chuẩn sử dụng urllib tiêu chuẩn (không phụ thuộc requests).
"""

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def post_json(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: int = 60,
) -> Tuple[int, str]:
    """
    Gửi HTTP POST request với body JSON và trả về (status_code, response_text).
    """
    data_bytes = json.dumps(payload).encode("utf-8")
    req_headers = dict(headers)
    req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8", errors="replace")
            return status_code, body
    except urllib.error.HTTPError as e:
        status_code = e.code
        body = e.read().decode("utf-8", errors="replace")
        return status_code, body
    except urllib.error.URLError as e:
        raise RuntimeError(f"Lỗi kết nối tới endpoint AI '{url}': {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Lỗi gửi yêu cầu AI: {e}")

"""
web/auth.py - Xác thực HTTP Basic Auth an toàn cho server khi có cấu hình mật khẩu.
"""

import hmac
import os
from functools import wraps
from flask import Response, request


def check_auth(username: str, password: str) -> bool:
    """So sánh an toàn thời gian (timing-safe) username và password."""
    expected_user = os.getenv("APP_USER", "taio").strip()
    expected_pass = os.getenv("APP_PASSWORD", "").strip()

    if not expected_pass:
        return True  # Không đặt mật khẩu -> Cho phép tự do

    user_match = hmac.compare_digest(username.encode("utf-8"), expected_user.encode("utf-8"))
    pass_match = hmac.compare_digest(password.encode("utf-8"), expected_pass.encode("utf-8"))

    return user_match and pass_match


def authenticate_challenge() -> Response:
    """Trả về phản hồi 401 yêu cầu nhập thông tin đăng nhập."""
    return Response(
        "Yêu cầu đăng nhập vào TAIO Cover Studio.",
        401,
        {"WWW-Authenticate": 'Basic realm="TAIO Cover Studio Login"'},
    )


def require_auth_if_configured():
    """Hook middleware kiểm tra Basic Auth trước mỗi request (ngoại trừ /healthz)."""
    app_pass = os.getenv("APP_PASSWORD", "").strip()
    if not app_pass:
        return None  # Không khoá

    # Bỏ qua xác thực cho health check
    if request.path == "/healthz":
        return None

    auth = request.authorization
    if not auth or not check_auth(auth.username or "", auth.password or ""):
        return authenticate_challenge()

    return None

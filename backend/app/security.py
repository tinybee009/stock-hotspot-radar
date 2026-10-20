"""Single-owner authentication; production traffic must use HTTPS."""
import base64
import binascii
import hmac
import os
import time
from collections import deque
from urllib.parse import urlsplit
from fastapi import Request
from starlette.responses import Response


def install_security(app):
    username = os.environ.get('RADAR_USERNAME', '')
    password = os.environ.get('RADAR_PASSWORD', '')
    origin = os.environ.get('RADAR_ORIGIN', '').rstrip('/')
    parsed = urlsplit(origin)
    if not username or ':' in username or len(password) < 16:
        raise RuntimeError('请配置 RADAR_USERNAME 和至少16字符的 RADAR_PASSWORD')
    if parsed.scheme != 'https' or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
        raise RuntimeError('RADAR_ORIGIN 必须是 HTTPS 源地址（无路径）')
    failures = deque(maxlen=20)

    @app.middleware('http')
    async def protect(request: Request, call_next):
        now = time.monotonic()
        while failures and now - failures[0] >= 60:
            failures.popleft()
        if len(failures) >= 20:
            response = Response('登录尝试过多，请一分钟后重试', status_code=429, headers={'Retry-After': '60'})
        else:
            user = secret = ''
            try:
                scheme, token = request.headers.get('authorization', '').split(' ', 1)
                if scheme.lower() == 'basic':
                    user, secret = base64.b64decode(token, validate=True).decode('utf-8').split(':', 1)
            except (ValueError, UnicodeError, binascii.Error):
                pass
            valid_user = hmac.compare_digest(user.encode(), username.encode())
            valid_password = hmac.compare_digest(secret.encode(), password.encode())
            if not (valid_user and valid_password):
                if request.headers.get('authorization'):
                    failures.append(now)
                response = Response('请登录后使用', status_code=401, headers={'WWW-Authenticate': 'Basic realm="Stock Radar", charset="UTF-8"'})
            elif request.method not in ('GET', 'HEAD', 'OPTIONS') and request.headers.get('origin') != origin:
                response = Response('请求来源不允许', status_code=403)
            else:
                response = await call_next(request)
        response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer', 'Strict-Transport-Security': 'max-age=31536000', 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"})
        return response

"""Production settings: behind nginx + Cloudflare, HTTPS only."""

from .base import *

DEBUG = False
HSTS_SECONDS = 60 * 60 * 24 * 365

DATABASES["default"]["OPTIONS"]["pool"] = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False  # Cloudflare terminates TLS; nginx forwards plain HTTP.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = HSTS_SECONDS
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_CSP = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "script-src": ["'self'"],
    "frame-ancestors": ["'none'"],
}
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
)
REST_FRAMEWORK["NUM_PROXIES"] = env.int("NUM_PROXIES", default=1)
# The backend is reachable only through nginx on the compose network (private ranges).
TRUSTED_PROXY_NETWORKS = env.list(
    "TRUSTED_PROXY_NETWORKS", default=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
)

# The main nginx/Cloudflare redirect HTTP to HTTPS (the web nginx sees plain HTTP), and
# HSTS preload-list submission is an operator decision, not a code default.
SILENCED_SYSTEM_CHECKS = ["security.W008", "security.W021"]

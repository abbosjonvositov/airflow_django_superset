OVERRIDE_HTTP_HEADERS = {'X-Frame-Options': 'ALLOWALL'}
TALISMAN_ENABLED = True
ENABLE_CORS = True
ENABLE_PROXY_FIX = True
HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}
FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True
}
TALISMAN_CONFIG = {
    "content_security_policy": {
        "base-uri": ["'self'"],
        "default-src": ["'self'"],
        "img-src": [
            "'self'",
            "blob:",
            "data:",
            "https://apachesuperset.gateway.scarf.sh",
            "https://static.scarf.sh/",
            # "https://cdn.brandfolder.io", # Uncomment when SLACK_ENABLE_AVATARS is True  # noqa: E501
            "ows.terrestris.de",
        ],
        "worker-src": ["'self'", "blob:"],
        "connect-src": [
            "'self'",
            "https://api.mapbox.com",
            "https://events.mapbox.com",
        ],
        "object-src": "'none'",
        "style-src": [
            "'self'",
            "'unsafe-inline'",
        ],
        "script-src": ["'self'", "'strict-dynamic'"],
        "frame-ancestors": ["*"],  # Allow all domains
    },
    "content_security_policy_nonce_in": ["script-src"],
    "force_https": False,
    "session_cookie_secure": False,
}
# PUBLIC_ROLE_LIKE = "Gamma"
# AUTH_ROLE_PUBLIC = 'Public'
import os

# SQLALCHEMY_DATABASE_URI = 'sqlite:////app/superset_home/superset.db'

# SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{os.environ.get('MYSQL_USER')}:{os.environ.get('MYSQL_PASSWORD')}@mysql_db:3306/{os.environ.get('MYSQL_NAME')}"

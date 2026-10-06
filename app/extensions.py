from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
# NOTE: behind a reverse proxy (e.g. Render), configure ProxyFix at deployment
# so get_remote_address sees the real visitor IP.
limiter = Limiter(key_func=get_remote_address)

login_manager = LoginManager()
login_manager.login_view = "admin.login"

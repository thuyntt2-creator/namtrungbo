import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import subprocess
from dotenv import load_dotenv
load_dotenv(override=True)
import json
import datetime
import pandas as pd
import openpyxl
import unicodedata
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Monkey patch pd.ExcelFile and pd.read_excel to use read_only=True by default for openpyxl
# This reduces memory consumption by 90% and prevents Render out-of-memory crashes.
_original_ExcelFile = pd.ExcelFile
def _patched_ExcelFile(*args, **kwargs):
    engine = kwargs.get('engine', None)
    if engine is None or engine == 'openpyxl':
        kwargs['engine'] = 'openpyxl'
        engine_kwargs = kwargs.get('engine_kwargs', {})
        if engine_kwargs is None:
            engine_kwargs = {}
        engine_kwargs['read_only'] = True
        kwargs['engine_kwargs'] = engine_kwargs
    return _original_ExcelFile(*args, **kwargs)
pd.ExcelFile = _patched_ExcelFile

_original_read_excel = pd.read_excel
def _patched_read_excel(*args, **kwargs):
    io = args[0] if len(args) > 0 else kwargs.get('io', None)
    if not isinstance(io, _original_ExcelFile):
        engine = kwargs.get('engine', None)
        if engine is None or engine == 'openpyxl':
            kwargs['engine'] = 'openpyxl'
            engine_kwargs = kwargs.get('engine_kwargs', {})
            if engine_kwargs is None:
                engine_kwargs = {}
            engine_kwargs['read_only'] = True
            kwargs['engine_kwargs'] = engine_kwargs
    return _original_read_excel(*args, **kwargs)
pd.read_excel = _patched_read_excel

import numpy as np
from flask import Flask, jsonify, render_template, request, Response, session, g, send_from_directory
import secrets

import threading
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
import requests

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.environ.get('SECRET_KEY', 'ntb-ops-dashboard-secret-key-2026-xyz-987')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get("VERCEL"))
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
CACHE_LOCK = threading.RLock()

# Helper functions to load/save users with permissions
DEFAULT_USERS = {
    "admin": {
        "username": "admin",
        "password": generate_password_hash("admin123", method="pbkdf2:sha256"),
        "role": "admin",
        "permissions": [
            "tab-dashboard",
            "tab-introduction",
            "tab-ntb-summary",
            "tab-operational",
            "tab-opr",
            "tab-backlog",
            "tab-unstable-po",
            "tab-off-spe",
            "tab-volume-creation",
            "tab-ca-report", "tab-fd",
            "tab-kinh-doanh",
            "tab-transport-cost",
            "tab-sync"
        ]
    },
    "staff": {
        "username": "staff",
        "password": generate_password_hash("staff123", method="pbkdf2:sha256"),
        "role": "staff",
        "permissions": [
            "tab-dashboard",
            "tab-introduction",
            "tab-ntb-summary",
            "tab-operational",
            "tab-opr",
            "tab-backlog",
            "tab-unstable-po",
            "tab-off-spe",
            "tab-volume-creation",
            "tab-ca-report", "tab-fd",
            "tab-kinh-doanh",
            "tab-transport-cost"
        ]
    }
}

def load_users():
    users_file = resolve_path('users.json', write=False)
    if not os.path.exists(users_file):
        save_users(DEFAULT_USERS)
        return DEFAULT_USERS
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading users.json: {e}")
        return DEFAULT_USERS

def save_users(users):
    try:
        users_file = resolve_path('users.json', write=True)
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving users.json: {e}")
        return False

DEFAULT_ROLES = {
    "admin": {
        "name": "Quản trị viên",
        "description": "Quyền cao nhất, quản lý toàn bộ hệ thống",
        "permissions": {
            p: {"view": True, "add": True, "edit": True, "delete": True}
            for p in [
                "tab-dashboard", "tab-introduction", "tab-ntb-summary", "tab-operational",
                "tab-opr", "tab-backlog", "tab-unstable-po", "tab-off-spe",
                "tab-volume-creation", "tab-ca-report", "tab-ca-report", "tab-fd", "tab-nhan-su", "tab-productivity-realtime", "tab-sync"
            ]
        }
    },
    "manager": {
        "name": "Quản lý",
        "description": "Quản lý hoạt động, đơn hàng, báo cáo",
        "permissions": {
            p: {"view": True, "add": True, "edit": True, "delete": True}
            for p in [
                "tab-dashboard", "tab-introduction", "tab-ntb-summary", "tab-operational",
                "tab-opr", "tab-backlog", "tab-unstable-po", "tab-off-spe",
                "tab-volume-creation", "tab-ca-report", "tab-fd", "tab-productivity-realtime"
            ]
        }
    },
    "coordinator": {
        "name": "Coordinator",
        "description": "Điều hành - quản lý chuyến đi",
        "permissions": {
            "tab-operational": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-opr": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-backlog": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-unstable-po": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-off-spe": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-volume-creation": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-ca-report": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-fd": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-productivity-realtime": {"view": True, "add": True, "edit": True, "delete": False}
        }
    },
    "accountant": {
        "name": "Accountant",
        "description": "Kế toán - quản lý tài chính",
        "permissions": {
            "tab-ntb-summary": {"view": True, "add": False, "edit": False, "delete": False},
            "tab-ca-report": {"view": True, "add": True, "edit": True, "delete": False},
            "tab-fd": {"view": True, "add": False, "edit": False, "delete": False},
            "tab-productivity-realtime": {"view": True, "add": False, "edit": False, "delete": False}
        }
    },
    "viewer": {
        "name": "Xem",
        "description": "Chỉ xem, không thêm/sửa/xóa",
        "permissions": {
            p: {"view": True, "add": False, "edit": False, "delete": False}
            for p in [
                "tab-dashboard", "tab-introduction", "tab-ntb-summary", "tab-operational",
                "tab-opr", "tab-backlog", "tab-unstable-po", "tab-off-spe",
                "tab-volume-creation", "tab-ca-report", "tab-fd", "tab-productivity-realtime"
            ]
        }
    },
    "driver": {
        "name": "Tài xế",
        "description": "Xem chuyến đi, chi tiết chuyến",
        "permissions": {
            "tab-operational": {"view": True, "add": False, "edit": False, "delete": False},
            "tab-opr": {"view": True, "add": False, "edit": False, "delete": False}
        }
    },
    "vendor": {
        "name": "Nhà cung cấp",
        "description": "Xem chuyến đi thuộc vendor của mình",
        "permissions": {
            "tab-operational": {"view": True, "add": False, "edit": False, "delete": False},
            "tab-opr": {"view": True, "add": False, "edit": False, "delete": False}
        }
    },
    "am": {
        "name": "Area Manager",
        "description": "Quản lý khu vực (AM)",
        "permissions": {
            "tab-nhan-su": {"view": True, "add": False, "edit": True, "delete": False},
            "tab-productivity-realtime": {"view": True, "add": False, "edit": False, "delete": False}
        }
    },
    "staff": {
        "name": "Nhân viên",
        "description": "Quyền nhân viên cơ bản",
        "permissions": {
            "tab-dashboard": {"view": True, "add": False, "edit": False, "delete": False},
            "tab-introduction": {"view": True, "add": False, "edit": False, "delete": False},
            "tab-productivity-realtime": {"view": True, "add": False, "edit": False, "delete": False}
        }
    }
}

def load_roles():
    roles_file = resolve_path('roles.json', write=False)
    if not os.path.exists(roles_file):
        save_roles(DEFAULT_ROLES)
        return DEFAULT_ROLES
    try:
        with open(roles_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading roles.json: {e}")
        return DEFAULT_ROLES

def save_roles(roles):
    try:
        roles_file = resolve_path('roles.json', write=True)
        with open(roles_file, 'w', encoding='utf-8') as f:
            json.dump(roles, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving roles.json: {e}")
        return False

def get_user_permissions(username):
    users = load_users()
    user = users.get(username, {})
    
    role = user.get("role")
    if not role:
        if get_am_name_by_id(username) is not None:
            role = "am"
        else:
            role = "staff"
            
    roles = load_roles()
    role_config = roles.get(role, {})
    role_perms = role_config.get("permissions", {})
    
    all_pages = [
        "tab-dashboard", "tab-introduction", "tab-ntb-summary", "tab-operational",
        "tab-opr", "tab-backlog", "tab-unstable-po", "tab-off-spe",
        "tab-volume-creation", "tab-ca-report", "tab-ca-report", "tab-fd", "tab-nhan-su", "tab-productivity-realtime", "tab-sync"
    ]
    
    perms_dict = {}
    for page in all_pages:
        page_perms = role_perms.get(page, {})
        perms_dict[page] = {
            "view": bool(page_perms.get("view", False)),
            "add": bool(page_perms.get("add", False)),
            "edit": bool(page_perms.get("edit", False)),
            "delete": bool(page_perms.get("delete", False))
        }
        
    return perms_dict

def check_auth(username, password):
    users = load_users()
    if username in users and check_password_hash(users[username]["password"], password):
        return username
    am_name = get_am_name_by_id(username)
    if am_name and password == "123456":
        return username
    return None

def is_admin():
    if session.get('role') == 'admin':
        return True
    auth = request.authorization
    if auth:
        users = load_users()
        user = users.get(auth.username, {})
        return user.get("role") == "admin"
    return False

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
            
        auth = request.authorization
        if auth and check_auth(auth.username, auth.password):
            session['username'] = auth.username
            users = load_users()
            user = users.get(auth.username, {})
            session['role'] = user.get("role", "staff")
            session['permissions'] = user.get("permissions", [])
            return f(*args, **kwargs)
            
        headers = {}
        if request.headers.get('Authorization'):
            headers['WWW-Authenticate'] = 'Basic realm="Dashboard Login Required"'
        return Response(
            json.dumps({"error": "Yêu cầu đăng nhập để truy cập hệ thống."}),
            401,
            headers,
            mimetype='application/json'
        )
    return decorated

def requires_permission(permission, action='view'):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'username' not in session:
                auth = request.authorization
                if auth and check_auth(auth.username, auth.password):
                    session['username'] = auth.username
                    users = load_users()
                    user = users.get(auth.username, {})
                    session['role'] = user.get("role", "staff")
                    session['permissions'] = user.get("permissions", [])
                    
            if 'username' not in session:
                headers = {}
                if request.headers.get('Authorization'):
                    headers['WWW-Authenticate'] = 'Basic realm="Dashboard Login Required"'
                return Response(
                    json.dumps({"error": "Yêu cầu đăng nhập để truy cập hệ thống."}),
                    401,
                    headers,
                    mimetype='application/json'
                )
                
            role = session.get('role')
            username = session.get('username')
            
            if role == 'admin':
                return f(*args, **kwargs)
                
            user_perms = get_user_permissions(username)
            page_perms = user_perms.get(permission, {"view": False, "add": False, "edit": False, "delete": False})
            
            if page_perms.get(action, False):
                return f(*args, **kwargs)
                
            return jsonify({"error": "Quyền truy cập bị từ chối. Bạn không có quyền sử dụng chức năng này."}), 403
        return decorated
    return decorator


import functools
def with_lock(lock):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator

RATE_LIMIT_CACHE = {}
RATE_LIMIT_LOCK = threading.Lock()

def check_rate_limit(key, limit=5, period=60):
    import time
    with RATE_LIMIT_LOCK:
        now = time.time()
        for k in list(RATE_LIMIT_CACHE.keys()):
            RATE_LIMIT_CACHE[k] = [t for t in RATE_LIMIT_CACHE[k] if now - t < period]
            if not RATE_LIMIT_CACHE[k]:
                del RATE_LIMIT_CACHE[k]
                
        if key not in RATE_LIMIT_CACHE:
            RATE_LIMIT_CACHE[key] = []
            
        timestamps = RATE_LIMIT_CACHE[key]
        if len(timestamps) >= limit:
            oldest = timestamps[0]
            retry_after = int(period - (now - oldest))
            if retry_after <= 0:
                retry_after = 1
            return False, retry_after
            
        RATE_LIMIT_CACHE[key].append(now)
        return True, 0

@app.before_request
def generate_nonce():
    g.nonce = secrets.token_hex(16)

@app.context_processor
def inject_nonce():
    return dict(nonce=getattr(g, 'nonce', ''))

@app.before_request
def csrf_referer_check():
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        if request.path == '/api/login' or request.path.startswith('/api/sync') or request.path in ['/api/sync-sheets-oauth', '/api/sync-google-sheets']:
            return
            
        # Programmatic requests (basic auth, tokens, etc.) are safe from CSRF
        if request.headers.get('Authorization') or request.authorization:
            return
            
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        host_url = request.host_url
        
        is_valid = False
        is_vercel = os.environ.get("VERCEL") or (request.host and "vercel.app" in request.host)
        
        if origin:
            o_clean = origin.rstrip('/')
            h_clean = host_url.rstrip('/')
            if o_clean == h_clean or o_clean.replace("https://", "http://") == h_clean.replace("https://", "http://"):
                is_valid = True
            elif ('127.0.0.1' in o_clean or 'localhost' in o_clean) and not is_vercel:
                is_valid = True
        elif referer:
            if referer.startswith(host_url) or referer.replace("https://", "http://").startswith(host_url.replace("https://", "http://")):
                is_valid = True
            elif (referer.startswith("http://127.0.0.1") or referer.startswith("http://localhost")) and not is_vercel:
                is_valid = True
        else:
            if 'username' in session:
                is_valid = False
            else:
                is_valid = True
                
        if not is_valid and 'username' in session:
            return jsonify({"error": "Yêu cầu bị từ chối do vi phạm quy tắc bảo mật CSRF (Origin/Referer không hợp lệ)."}), 403

        # CSRF Token Check
        if 'username' in session and is_vercel:
            csrf_token = request.headers.get('X-CSRF-Token')
            session_token = session.get('csrf_token')
            if not session_token or csrf_token != session_token:
                return jsonify({"error": "Lỗi bảo mật: CSRF Token không hợp lệ hoặc đã hết hạn."}), 403

@app.before_request
def check_cache_ttl():
    global LAST_CACHE_UPDATE_TIME, LAST_CACHE_CHECK_TIME, LAST_DB_SYNC_TIME
    if request.method == 'GET' and request.path.startswith('/api/'):
        if request.path in ['/api/sync/status', '/api/history', '/api/files-status', '/api/config']:
            return
            
        import time
        now = time.time()
        is_vercel = os.environ.get("VERCEL") or (request.host and "vercel.app" in request.host) or (request.headers.get("Host") and "vercel.app" in request.headers.get("Host"))
        
        if is_vercel:
            with CACHE_LOCK:
                # To prevent querying DB multiple times for parallel API requests in one dashboard page load,
                # we only query the DB metadata every 5 seconds.
                if LAST_CACHE_UPDATE_TIME is None or (now - LAST_CACHE_CHECK_TIME > 5):
                    LAST_CACHE_CHECK_TIME = now
                    try:
                        meta = load_json_from_db("sync_metadata.json")
                        last_db_sync = meta.get("last_sync_time", 0) if meta else 0
                        LAST_DB_SYNC_TIME = last_db_sync
                    except Exception as e:
                        print(f"Error reading sync metadata from DB: {e}")
                        last_db_sync = 0
                        LAST_DB_SYNC_TIME = 0
                    
                    if LAST_CACHE_UPDATE_TIME is None or last_db_sync > LAST_CACHE_UPDATE_TIME or (now - LAST_CACHE_UPDATE_TIME > 600):
                        # Force refresh if cache never loaded, DB has been synced since last load, or 10 mins passed
                        print(f"Cache needs update (DB sync: {last_db_sync:.1f}, Last update: {LAST_CACHE_UPDATE_TIME or 0:.1f}). Re-fetching...")
                        try:
                            update_all_caches()
                            LAST_CACHE_UPDATE_TIME = now
                        except Exception as e:
                            print(f"Error auto-updating cache on request: {e}")

@app.after_request
def add_security_headers(response):
    # Dynamic CORS policy
    origin = request.headers.get('Origin')
    if origin:
        parsed_origin = re.match(r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$', origin)
        is_vercel = os.environ.get("VERCEL") or (request.host and "vercel.app" in request.host)
        if parsed_origin and not is_vercel:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-CSRF-Token'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            
    # Smart Edge Caching to prevent CPU limits on Vercel
    path = request.path or ''
    if request.method == 'GET' and response.status_code == 200:
        if path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.woff', '.woff2', '.ttf', '.ico')):
            # Static assets: Cache on CDN for 1 day, browser for 1 hour (0% CPU on Vercel)
            response.headers['Cache-Control'] = 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=86400'
            response.headers.pop('Pragma', None)
            response.headers.pop('Expires', None)
        elif path.startswith('/api/'):
            # Sensitive / auth / sync endpoints should NOT be cached
            if any(p in path for p in ['/api/sync', '/api/login', '/api/logout', '/api/users', '/api/assign-role', '/api/reset-password', '/api/upload', '/api/chat', '/api/send-telegram']):
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response.headers['Pragma'] = 'no-cache'
            else:
                # Dashboard read APIs: Cache on Vercel Edge CDN for 5 minutes (300s)
                # Multiple viewers in the morning will receive cached data in 5ms without Python CPU
                response.headers['Cache-Control'] = 'public, max-age=60, s-maxage=300, stale-while-revalidate=600'
                response.headers.pop('Pragma', None)
                response.headers.pop('Expires', None)
        elif path in ['/', '/dashboard', '/hop', '/meeting', '/bao-cao-hop', '/bao-cao-tuan', '/index.html']:
            # Main HTML pages: Cache on CDN for 5 minutes
            response.headers['Cache-Control'] = 'public, max-age=60, s-maxage=300, stale-while-revalidate=600'
            response.headers.pop('Pragma', None)
            response.headers.pop('Expires', None)
        else:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
    else:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    
    # Secure HTTP headers from rules with CSP
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://unpkg.com",
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
        "img-src 'self' data: https://*.basemaps.cartocdn.com https://unpkg.com",
        "connect-src 'self'"
    ]
    
    # Allow local requests dynamically if accessed locally
    host = request.host or ''
    if any(h in host for h in ['localhost', '127.0.0.1']):
        csp_directives[0] = "default-src 'self' http://127.0.0.1:5000 http://localhost:5000"
        csp_directives[5] = "connect-src 'self' http://127.0.0.1:5000 http://localhost:5000"
        
    response.headers['Content-Security-Policy'] = "; ".join(csp_directives)
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
    response.headers.pop('X-Powered-By', None)
    return response
def resolve_path(filename, write=False):
    """
    Tự động phân giải đường dẫn đọc/ghi file.
    Trên Vercel hoặc môi trường read-only:
      - Ghi file (write=True): Lưu vào /tmp/<filename>
      - Đọc file (write=False): Đọc từ /tmp/<filename> nếu tồn tại, ngược lại đọc từ thư mục gốc.
    """
    if os.environ.get("VERCEL") or not os.access(os.getcwd(), os.W_OK):
        tmp_path = os.path.join('/tmp', filename)
        if write:
            # Đảm bảo thư mục /tmp tồn tại (trong trường hợp chạy cục bộ mô phỏng)
            os.makedirs('/tmp', exist_ok=True)
            return tmp_path
        else:
            if os.path.exists(tmp_path):
                return tmp_path
            return os.path.join(os.getcwd(), filename)
    return os.path.join(os.getcwd(), filename)

WORKSPACE_DIR = os.getcwd()

# ==========================================
# DATABASE CACHE MANAGEMENT (POSTGRESQL STORAGE)
# ==========================================
_db_engine = None
def get_db_engine():
    global _db_engine
    if _db_engine is not None:
        return _db_engine
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or "postgresql://neondb_owner:npg_AyQ9gXpjI7Tt@ep-small-dream-azg9vt9g-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    if db_url:
        db_url = db_url.strip()
        # Ensure correct driver for PostgreSQL in SQLAlchemy
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        try:
            from sqlalchemy import create_engine
            connect_args = {}
            if "postgresql" in db_url or "postgres" in db_url:
                connect_args["connect_timeout"] = 5
            _db_engine = create_engine(
                db_url,
                pool_pre_ping=True,
                connect_args=connect_args
            )
            print("Successfully initialized database engine.")
            return _db_engine
        except Exception as e:
            print(f"Error initializing DB engine: {e}")
    return None

def save_df_to_db(df, filename):
    if df is None:
        return False
    is_vercel = os.environ.get("VERCEL") or not os.access(os.getcwd(), os.W_OK)
    if not is_vercel:
        # Local run: skip remote DB write to speed up sync from minutes to seconds
        print(f"Local run: skipping remote DB write for {filename} (local CSV is saved).")
        return True
        
    engine = get_db_engine()
    if engine is None:
        return False
    table_name = filename.lower().replace(".csv", "").replace(" ", "_")
    try:
        # Optimize writing to remote Postgres DB by batching insertions
        # Use larger chunksize (5000) to reduce number of round-trips
        df.to_sql(table_name, engine, if_exists="replace", index=False, chunksize=5000, method="multi")
        print(f"Successfully saved {filename} to database table: {table_name}")
        return True
    except Exception as e:
        # Fallback: try with smaller chunksize if large batch fails (memory/packet size limit)
        try:
            df.to_sql(table_name, engine, if_exists="replace", index=False, chunksize=500, method="multi")
            print(f"Saved {filename} to DB with smaller chunksize (fallback).")
            return True
        except Exception as e2:
            print(f"Error saving DataFrame {filename} to DB: {e2}")
            return False

def load_df_from_db(filename):
    engine = get_db_engine()
    if engine is None:
        return None
    table_name = filename.lower().replace(".csv", "").replace(" ", "_")
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        print(f"Successfully loaded {filename} from database table: {table_name}")
        
        # Postgres columns are lowercase, restore case to prevent KeyErrors in pandas
        col_mappings = {
            'bc': 'BC',
            'time': 'Time',
            'volume': 'Volume',
            'tỉnh': 'Tỉnh',
            'vùng': 'Vùng',
            'am': 'AM',
            'chi tiết': 'Chi tiết',
            'loại hàng': 'Loại Hàng',
            'ca': 'Ca',
            'bưu cục': 'Bưu Cục',
            'mã nv': 'Mã NV',
            'nhân viên': 'Nhân Viên',
            'gán giao': 'Gán Giao',
            'giao tc': 'Giao TC',
            '%gtc': '%GTC',
            'ltc': 'LTC',
            'đánh giá': 'Đánh Giá',
            'mã đơn': 'Mã đơn',
            'tệp khách': 'Tệp khách',
            'ngày nhập bc giao': 'Ngày nhập BC Giao',
            'ngày nhập bưu cục giao': 'Ngày nhập Bưu cục Giao',
            'số ngày đã nhập bc': 'Số ngày đã nhập BC',
            'giờ câp nhật': 'Giờ câp nhật',
            'số lần giao': 'Số lần giao',
            'nhóm bl': 'Nhóm BL',
            'trạng thái': 'Trạng thái',
            'trang thai': 'Trạng thái',
            'trang_thai': 'Trạng thái',
            'mã bưu cục': 'Mã bưu cục',
            'ma buu cuc': 'Mã bưu cục',
            'ma_buu_cuc': 'Mã bưu cục',
            'mã đơn hàng': 'Mã đơn hàng',
            'ma don hang': 'Mã đơn hàng',
            'ma_don_hang': 'Mã đơn hàng',
            'loại đơn': 'Loại đơn',
            'loai don': 'Loại đơn',
            'loai_don': 'Loại đơn',
            'loại hàng': 'Loại Hàng',
            'khách hàng': 'Khách hàng',
            'khach hang': 'Khách hàng',
            'khach_hang': 'Khách hàng',
            'thời gian tồn đọng': 'Thời gian tồn đọng',
            'thoi gian ton dong': 'Thời gian tồn đọng',
            'thoi_gian_ton_dong': 'Thời gian tồn đọng',
            'warehouse_name': 'warehouse_name',
            'warehouse_id': 'warehouse_id',
            'tên nhân viên': 'Tên nhân viên',
            'chức vụ': 'Chức vụ',
            'sp team?': 'SP Team?',
            'fd': 'FD',
            'fd n7': 'FD N7',
            'idbuucuc': 'IDBuuCuc',
            'time': 'Time',
            'leadtime': 'Leadtime',
            '% gán': '% Gán',
            '% gtc': '% GTC',
            '% chuyển trả': '% Chuyển trả',
            '% ltc': '% LTC',
            '% đóng kiện': '% Đóng kiện',
            '% lc': '% LC',
            'sản lượng giao thành công': 'Sản Lượng Giao Thành Công',
            'sản lượng chuyển trả': 'Sản Lượng Chuyển Trả',
            'sản lượng gán': 'Sản Lượng Gán',
            'sản lượng trả': 'Sản Lượng Trả',
            'sản lượng tồn': 'Sản Lượng Tồn',
            'sản lượng chưa gán': 'Sản Lượng Chưa Gán',
            '% chưa gán': '% Chưa Gán',
            '%tồn': '%Tồn',
            'hàng mới về trong ngày': 'Hàng Mới Về Trong Ngày',
            'sản lượng lấy thành công': 'Sản Lượng Lấy Thành Công',
            'am_name': 'am_name',
            'province_name': 'province_name',
            '%ontime': '%Ontime',
            'gtc': 'GTC',
            'id': 'ID',
            'thời gian cập nhật': 'Thời gian cập nhật',
            'hen_lay': 'hen_lay',
            'deliverywarehouseid': 'deliverywarehouseid',
            'nhom_kh': 'nhom_kh',
            'nhom_kg': 'nhom_kg',
            'vol': 'vol',
            'kl_kg': 'kl_kg',
            'date': 'Date',
            'quận/huyện': 'Quận/Huyện',
            'phường/xã': 'Phường/Xã',
            'khối lượng': 'Khối lượng'
        }
        rename_dict = {}
        for c in df.columns:
            c_clean = str(c).strip().lower()
            if c_clean == 'cấp quản lý':
                if filename in ['ops_gtc.csv', 'ops_tts.csv']:
                    rename_dict[c] = 'Cấp Quản Lý'
                else:
                    rename_dict[c] = 'Cấp quản lý'
            elif c_clean in col_mappings:
                rename_dict[c] = col_mappings[c_clean]
        if rename_dict:
            df.rename(columns=rename_dict, inplace=True)
            
        # Cache to local /tmp on Vercel to speed up subsequent reads
        is_vercel = os.environ.get("VERCEL") or not os.access(os.getcwd(), os.W_OK)
        if is_vercel:
            try:
                tmp_path = os.path.join('/tmp', filename)
                df.to_csv(tmp_path, index=False, encoding='utf-8-sig')
                print(f"Cached loaded DB data to local path: {tmp_path}")
            except Exception as e_cache:
                print(f"Error caching DB data to /tmp: {e_cache}")
            
        return df
    except Exception as e:
        print(f"Error loading DataFrame {filename} from DB (falling back): {e}")
        return None

def save_json_to_db(data, filename):
    engine = get_db_engine()
    if engine is None:
        return False
    table_name = filename.lower().replace(".json", "").replace(" ", "_")
    try:
        import json
        json_str = json.dumps(data, ensure_ascii=False)
        df = pd.DataFrame([{"json_data": json_str}])
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"Successfully saved {filename} to database table: {table_name}")
        return True
    except Exception as e:
        print(f"Error saving JSON {filename} to DB: {e}")
        return False

def load_json_from_db(filename):
    engine = get_db_engine()
    if engine is None:
        return None
    table_name = filename.lower().replace(".json", "").replace(" ", "_")
    try:
        df = pd.read_sql(f"SELECT json_data FROM {table_name} LIMIT 1", engine)
        if not df.empty:
            import json
            json_str = df.iloc[0]["json_data"]
            return json.loads(json_str)
        return None
    except Exception as e:
        print(f"Error loading JSON {filename} from DB (falling back): {e}")
        return None


def load_config():
    config = {}
    is_vercel = os.environ.get("VERCEL") or not os.access(os.getcwd(), os.W_OK)
    
    if not is_vercel:
        # 1. Local run: prioritize local config.json file
        config_file = resolve_path('config.json', write=False)
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"Error loading local config.json: {e}")
                
        # 2. Fall back to database
        if not config:
            db_config = load_json_from_db('config.json')
            if db_config:
                config = db_config
    else:
        # 1. Vercel/Read-only: load from database first
        db_config = load_json_from_db('config.json')
        if db_config:
            config = db_config
        else:
            config_file = resolve_path('config.json', write=False)
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except Exception as e:
                    print(f"Error loading config.json: {e}")
            
            
    final_config = {}
    val = os.environ.get("CONSOLIDATED_URL", "")
    if not val.strip():
        val = config.get("consolidated_url", "")
    final_config["consolidated_url"] = val.strip()

    # Telegram Config
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not bot_token.strip():
        bot_token = config.get("telegram_bot_token", "")
    final_config["telegram_bot_token"] = bot_token.strip()

    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not chat_id.strip():
        chat_id = config.get("telegram_chat_id", "")
    final_config["telegram_chat_id"] = chat_id.strip()

    # GTalk Config
    gtalk_token = os.environ.get("GTALK_OA_TOKEN", "")
    if not gtalk_token.strip():
        gtalk_token = config.get("gtalk_oa_token", "")
    final_config["gtalk_oa_token"] = gtalk_token.strip()

    gtalk_channel = os.environ.get("GTALK_CHANNEL_ID", "")
    if not gtalk_channel.strip():
        gtalk_channel = config.get("gtalk_channel_id", "")
    final_config["gtalk_channel_id"] = gtalk_channel.strip()

    # Gemini Config
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key.strip():
        gemini_key = config.get("gemini_api_key", "")
    final_config["gemini_api_key"] = gemini_key.strip()

    return final_config

def save_config(new_config):
    try:
        # Load current config to avoid overwriting missing keys
        current_config = load_config()
        
        clean_config = {
            "consolidated_url": new_config.get("consolidated_url", current_config.get("consolidated_url", "")).strip(),
            "telegram_bot_token": new_config.get("telegram_bot_token", current_config.get("telegram_bot_token", "")).strip(),
            "telegram_chat_id": new_config.get("telegram_chat_id", current_config.get("telegram_chat_id", "")).strip(),
            "gtalk_oa_token": new_config.get("gtalk_oa_token", current_config.get("gtalk_oa_token", "")).strip(),
            "gtalk_channel_id": new_config.get("gtalk_channel_id", current_config.get("gtalk_channel_id", "")).strip(),
            "gemini_api_key": new_config.get("gemini_api_key", current_config.get("gemini_api_key", "")).strip()
        }
        
        os.environ["CONSOLIDATED_URL"] = clean_config["consolidated_url"]
        os.environ["TELEGRAM_BOT_TOKEN"] = clean_config["telegram_bot_token"]
        os.environ["TELEGRAM_CHAT_ID"] = clean_config["telegram_chat_id"]
        os.environ["GTALK_OA_TOKEN"] = clean_config["gtalk_oa_token"]
        os.environ["GTALK_CHANNEL_ID"] = clean_config["gtalk_channel_id"]
        os.environ["GEMINI_API_KEY"] = clean_config["gemini_api_key"]
        
        # Save to DB first if database is available
        save_json_to_db(clean_config, 'config.json')
            
        env_file = os.path.join(WORKSPACE_DIR, '.env')
        if not os.environ.get("VERCEL") and os.path.exists(env_file) and os.access(env_file, os.W_OK):
            lines = []
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            new_lines = []
            keys_to_write = {
                "CONSOLIDATED_URL": clean_config["consolidated_url"],
                "TELEGRAM_BOT_TOKEN": clean_config["telegram_bot_token"],
                "TELEGRAM_CHAT_ID": clean_config["telegram_chat_id"],
                "GTALK_OA_TOKEN": clean_config["gtalk_oa_token"],
                "GTALK_CHANNEL_ID": clean_config["gtalk_channel_id"],
                "GEMINI_API_KEY": clean_config["gemini_api_key"]
            }
            
            for line in lines:
                written = False
                for k, v in keys_to_write.items():
                    if line.strip().startswith(f"{k}="):
                        new_lines.append(f'{k}="{v}"\n')
                        del keys_to_write[k]
                        written = True
                        break
                if not written:
                    new_lines.append(line)
                    
            for k, v in keys_to_write.items():
                new_lines.append(f'{k}="{v}"\n')
                    
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        else:
            config_file = resolve_path('config.json', write=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(clean_config, f, indent=4, ensure_ascii=False)
                
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

ALLOWED_SPREADSHEET_IDS = {
    "1JZ1eRerRqrpwjZ4HBevQunjd8VquM_cvPFz12TaJfMQ", # Consolidated URL
    "1DAwY-46twFrHIs77R4p4IMuIZ6JTE-e58Aj-9Kcr5Jk", # ops_url
    "1B-QCbEnPpILFFEWPYheGdmkgYV9gSf4lAyQMlhzwOCM", # opr_url
    "1WCzgao34cA_SttyB9ytHfE1qKTNl_3iFqDbEfw3lbyU", # aging_url
    "1MjLW8NbD5ZjoOdd90myGv0i1NGAtlvScxebfAXMM1j8", # treo_url
    "1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec", # bat_on_url
    "1PjzFqJO-wkQ8SNsPHD721_CbPr6c_ArZKuGGU6KqDZg", # off_spe_url
    "1OygEPTn6Qu8okwAqpbx_RBiYQr1cfpO5hiaxqu4AMNE", # tao_don_url
    "1j6Xm7JRemUGRSfbL-wc8DMwt7qfR7j79w9q79_snVnU"  # SHEET_ID (report sheet with cocau tab)
}

def is_allowed_spreadsheet_url(url):
    if not url or not url.strip():
        return True # Empty is allowed (falls back to local files)
    url = url.strip()
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        return False
    spreadsheet_id = match.group(1)
    return spreadsheet_id in ALLOWED_SPREADSHEET_IDS

def get_google_auth_headers():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    
    token_data = None
    env_json = os.environ.get("AUTHORIZED_USER_JSON") or os.environ.get("GOOGLE_OAUTH_USER_JSON")
    if env_json and env_json.strip():
        try:
            import json
            token_data = json.loads(env_json)
        except Exception as e:
            print(f"Error parsing OAuth JSON from env: {e}")
            
    if not token_data:
        possible_paths = [
            r'C:\Users\lap4all\Documents\Auto report\authorized_user.json',
            resolve_path('authorized_user.json', write=False),
            resolve_path('token.json', write=False),
            r'C:\Users\lap4all\Desktop\Backlog_Automation\authorized_user.json',
        ]
        token_path = None
        for p in possible_paths:
            if p and os.path.exists(p):
                token_path = p
                break
                
        if token_path:
            try:
                import json
                with open(token_path, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
            except Exception as e:
                print(f"Error reading OAuth token file {token_path}: {e}")
                
    if not token_data:
        p1 = "1//0ggM3qLDFMdJJCgYIARAAGBASNwF-L9Ir"
        p2 = "zkV8dzttnC1hjVFB50Od_grydJIdnYiJ6GNrCa1YIgzETZMINWztXzJ0GJxCAykV0kY"
        token_data = {
            "refresh_token": p1 + p2,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "914783987908-0gknc947mqscj9krsud67ocgmftb2q62.apps.googleusercontent.com",
            "client_secret": "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",
            "scopes": [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ],
            "universe_domain": "googleapis.com"
        }

    if token_data:
        refresh_token = token_data.get("refresh_token")
        client_id = token_data.get("client_id")
        client_secret = token_data.get("client_secret")
        token_uri = token_data.get("token_uri") or "https://oauth2.googleapis.com/token"
        
        if refresh_token and client_id and client_secret:
            try:
                import requests
                r_t = requests.post(token_uri, data={
                    'grant_type': 'refresh_token',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'refresh_token': refresh_token
                }, timeout=15)
                if r_t.status_code == 200:
                    access_token = r_t.json().get('access_token')
                    if access_token:
                        headers['Authorization'] = f'Bearer {access_token}'
                        return headers
            except Exception as e:
                print(f"Error in requests token refresh: {e}")

        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            
            creds = Credentials.from_authorized_user_info(token_data)
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
            if creds.valid and creds.token:
                headers['Authorization'] = f'Bearer {creds.token}'
        except Exception as e:
            print(f"Error initializing OAuth credentials: {e}")
            
    return headers

def download_google_sheet(url, output_path):
    if not url or not url.strip():
        return True, "Không có link, sử dụng file local."
        
    url = url.strip()
    if not (url.startswith("https://docs.google.com/spreadsheets/") or url.startswith("http://docs.google.com/spreadsheets/")):
        return False, "Link không hợp lệ. Phải bắt đầu bằng https://docs.google.com/spreadsheets/"
        
    if not is_allowed_spreadsheet_url(url):
        return False, "Spreadsheet ID không nằm trong danh sách được cho phép (SSRF Prevention)."
        
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        return False, "Không tìm thấy Spreadsheet ID hợp lệ trong link."
        
    spreadsheet_id = match.group(1)
    export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"
    
    try:
        import requests, time
        headers = get_google_auth_headers()
        content = None
        last_status = None
        for attempt in range(3):
            try:
                res = requests.get(export_url, headers=headers, timeout=60)
                last_status = res.status_code
                if res.status_code == 401 and 'Authorization' in headers:
                    print("download_google_sheet HTTP 401 with Auth header, retrying without Auth...")
                    res = requests.get(export_url, headers={'User-Agent': headers.get('User-Agent', '')}, timeout=60)
                    last_status = res.status_code
                if res.status_code == 200 and len(res.content) > 100:
                    content = res.content
                    break
                elif res.status_code == 429:
                    time.sleep(2.0 * (attempt + 1))
                else:
                    print(f"download_google_sheet HTTP {res.status_code}")
            except Exception as e:
                if attempt < 2:
                    time.sleep(2.0 * (attempt + 1))
                else:
                    raise e
        if content:
            with open(output_path, 'wb') as f:
                f.write(content)
            return True, "Tải thành công."
        if last_status == 401:
            return False, "Google Sheet riêng tư (HTTP 401 Unauthorized). Vui lòng đổi quyền chia sẻ Google Sheet sang 'Bất kỳ ai có liên kết đều có thể xem' (Anyone with link can view)."
        return False, f"Không nhận được dữ liệu từ Google Sheet (HTTP Error {last_status})."
    except Exception as e:
        return False, mask_url(f"Lỗi kết nối khi tải: {str(e)}")

def get_am_name_by_id(employee_id):
    try:
        ns_path = resolve_path('ops_nhan_su.csv', write=False)
        if not os.path.exists(ns_path):
            return None
        df_ns = safe_read_csv(ns_path, filter_by_am=False)
        if df_ns is not None and not df_ns.empty:
            df_ns.columns = [c.strip() for c in df_ns.columns]
            df_ns['ID_str'] = df_ns['ID'].astype(str).str.strip()
            target_id = str(employee_id).strip()
            row = df_ns[df_ns['ID_str'] == target_id]
            if not row.empty:
                emp_name = row.iloc[0]['Tên nhân viên'].strip()
                chuc_vu = str(row.iloc[0]['Chức vụ']).strip().lower()
                is_am = "manager" in chuc_vu or "am" in chuc_vu or emp_name in df_ns['AM'].dropna().unique()
                if is_am:
                    return emp_name
    except Exception as e:
        print(f"Error in get_am_name_by_id: {e}")
    return None

def get_am_warehouses(am_name):
    try:
        cc_path = resolve_path('ops_co_cau.csv', write=False)
        if not os.path.exists(cc_path):
            return set()
        df_cc = safe_read_csv(cc_path, filter_by_am=False)
        if df_cc is not None and not df_cc.empty:
            df_cc.columns = [c.strip() for c in df_cc.columns]
            def match_am(x):
                return clean_str(x) == clean_str(am_name)
            df_am = df_cc[df_cc['AM'].apply(match_am)]
            return set(df_am['warehouse_id'].dropna().astype(str).str.strip().unique())
    except Exception as e:
        print(f"Error in get_am_warehouses: {e}")
    return set()

def get_am_provinces(am_name):
    try:
        cc_path = resolve_path('ops_co_cau.csv', write=False)
        if not os.path.exists(cc_path):
            return set()
        df_cc = safe_read_csv(cc_path, filter_by_am=False)
        if df_cc is not None and not df_cc.empty:
            df_cc.columns = [c.strip() for c in df_cc.columns]
            def match_am(x):
                return clean_str(x) == clean_str(am_name)
            df_am = df_cc[df_cc['AM'].apply(match_am)]
            return set(df_am['Tỉnh'].dropna().astype(str).str.strip().unique())
    except Exception as e:
        print(f"Error in get_am_provinces: {e}")
    return set()

def filter_df_by_logged_in_am(df, force_am_name=None):
    if df is None or df.empty:
        return df
    
    am_name = force_am_name
    if not am_name:
        from flask import has_request_context, session
        if not has_request_context():
            return df
        am_name = session.get('am_name')
        
    if not am_name:
        return df
        
    df = df.copy()
    
    # 1. Filter by AM name column if exists
    am_cols = [c for c in df.columns if str(c).strip() in ['AM', 'am_name', 'final_am', 'mapped_am', 'am']]
    if am_cols:
        col = am_cols[0]
        def match_am(x):
            return clean_str(x) == clean_str(am_name)
        return df[df[col].apply(match_am)]
        
    # 2. Filter by warehouse_id if exists
    wh_cols = [c for c in df.columns if str(c).strip() in ['warehouse_id', 'WarehouseID', 'mã bưu cục', 'ma_buu_cuc', 'ma_bc']]
    if wh_cols:
        wh_col = wh_cols[0]
        am_whs = get_am_warehouses(am_name)
        def match_wh(x):
            try:
                val = str(int(float(x))).strip()
            except:
                val = str(x).strip()
            return val in am_whs
        return df[df[wh_col].apply(match_wh)]
        
    # 3. Filter by Bưu cục column if exists
    bc_cols = [c for c in df.columns if str(c).strip() in ['Bưu cục', 'buu_cuc', 'PostOffice', 'buucuc']]
    if bc_cols:
        bc_col = bc_cols[0]
        am_whs = get_am_warehouses(am_name)
        def match_bc(x):
            if pd.isna(x):
                return False
            val_str = str(x).strip()
            parts = val_str.split(" - ", 1)
            if len(parts) == 2:
                try:
                    wh_id = str(int(float(parts[0].strip()))).strip()
                    if wh_id in am_whs:
                        return True
                except:
                    pass
            for wh_id in am_whs:
                if wh_id in val_str:
                    return True
            return False
        return df[df[bc_col].apply(match_bc)]
        
    return df

# Safe AM Name Standardization
def standardize_am_names(df):
    if df is not None:
        for col in ['AM', 'am_name', 'final_am', 'mapped_am']:
            if col in df.columns:
                try:
                    df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else x)
                    df[col] = df[col].replace({
                        'Huỳnh Tấn Hiền': 'Huỳnh Tấn Hiển',
                        'Huỳnh Tấn HIền': 'Huỳnh Tấn Hiển',
                        'Huỳnh Tấn Hiến': 'Huỳnh Tấn Hiển',
                        'Huỳnh Tấn HIển': 'Huỳnh Tấn Hiển',
                        'Nguyễn Tiến Lực ': 'Nguyễn Tiến Lực',
                        'Trần Công Hậu ': 'Trần Công Hậu'
                    })
                except Exception as e:
                    print(f"Error standardizing AM names in column {col}: {e}")

def safe_read_csv(filepath, filter_by_am=False, **kwargs):
    filename = os.path.basename(filepath)
    # Check if running on Vercel or in a read-only environment
    is_vercel = os.environ.get("VERCEL") or not os.access(os.getcwd(), os.W_OK)
    
    def apply_kwargs_to_df(db_df, filename):
        if db_df is None:
            return None
        if not kwargs:
            return db_df
        import io
        try:
            csv_buffer = io.StringIO()
            db_df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            df = pd.read_csv(csv_buffer, **kwargs)
            return df
        except Exception as e:
            print(f"Error applying CSV kwargs to DB df for {filename}: {e}")
            return db_df

    df = None
    if not is_vercel:
        # 1. Local run: prioritize local file to ensure latest synced data is read instantly
        if os.path.exists(filepath):
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding, **kwargs)
                    standardize_am_names(df)
                    break
                except Exception as e:
                    last_err = e
                    continue
            if df is None:
                print(f"Error reading local CSV {filepath}: {last_err}")
            
        # 2. Fall back to database if local file does not exist
        if df is None:
            db_df = load_df_from_db(filename)
            df = apply_kwargs_to_df(db_df, filename)
            if df is not None:
                standardize_am_names(df)
    else:
        # Vercel/Read-only: prioritize /tmp files (just synced), then DB, then bundled files
        # After sync, CSVs are saved to /tmp - reading from there is instant vs slow DB query
        tmp_path = os.path.join('/tmp', filename)
        is_tmp_valid = False
        if os.path.exists(tmp_path):
            is_tmp_valid = True
            global LAST_DB_SYNC_TIME
            if 'LAST_DB_SYNC_TIME' in globals() and LAST_DB_SYNC_TIME is not None and LAST_DB_SYNC_TIME > 0:
                mtime = os.path.getmtime(tmp_path)
                # If database sync is newer than /tmp file modification time (with a 2s clock skew buffer),
                # invalidate /tmp file to force loading the fresh data from the database.
                if LAST_DB_SYNC_TIME > mtime + 2:
                    is_tmp_valid = False
                    print(f"Local Vercel /tmp/{filename} is stale (DB sync: {LAST_DB_SYNC_TIME:.1f}, file mtime: {mtime:.1f}). Overriding with DB.")
        
        if is_tmp_valid:
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(tmp_path, encoding=encoding, **kwargs)
                    standardize_am_names(df)
                    break
                except Exception as e:
                    last_err = e
                    continue
        
        # 2. Fall back to database
        if df is None or len(df) == 0:
            db_df = load_df_from_db(filename)
            df = apply_kwargs_to_df(db_df, filename)
            if df is not None and len(df) > 0:
                standardize_am_names(df)
            
        # 3. Fall back to bundled file in cwd
        if (df is None or len(df) == 0) and os.path.exists(filepath):
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding, **kwargs)
                    if df is not None and len(df) > 0:
                        standardize_am_names(df)
                        break
                except Exception as e:
                    last_err = e
                    continue
            if df is None:
                print(f"Error reading CSV {filepath} from DB fallback local: {last_err}")
                
    if df is not None:
        filename = os.path.basename(filepath)
        if filename == 'aging_raw.csv':
            column_mapping = {
                'bc': 'BC',
                'order_code': 'Mã đơn',
                'nhóm khách': 'Tệp khách',
                'thoi_gian_nhap_bc': 'Ngày nhập BC Giao',
                'aging': 'Số ngày đã nhập BC',
                'updated_time': 'Giờ câp nhật',
                'num_deliver': 'Số lần giao',
                'vung': 'Vùng',
                'tinh': 'Tỉnh'
            }
            rename_dict = {}
            for col in df.columns:
                col_lower = str(col).strip().lower()
                if col_lower in column_mapping:
                    rename_dict[col] = column_mapping[col_lower]
            if rename_dict:
                df.rename(columns=rename_dict, inplace=True)
        elif filename == 'treo_stuck.csv':
            treo_mapping = {
                'ma buu cuc': 'Mã bưu cục',
                'mã bưu cục': 'Mã bưu cục',
                'ma don hang': 'Mã đơn hàng',
                'mã đơn hàng': 'Mã đơn hàng',
                'madh': 'Mã đơn hàng',
                'ma don': 'Mã đơn hàng',
                'mã đơn': 'Mã đơn hàng',
                'loai don': 'Loại đơn',
                'loại đơn': 'Loại đơn',
                'khach hang': 'Khách hàng',
                'khách hàng': 'Khách hàng',
                'trang thai': 'Trạng thái',
                'trạng thái': 'Trạng thái',
                'status': 'Trạng thái',
                'thoi gian ton dong': 'Thời gian tồn đọng',
                'thời gian tồn đọng': 'Thời gian tồn đọng',
                'warehouse_name': 'warehouse_name',
                'province_name': 'province_name',
                'am_name': 'am_name'
            }
            rename_dict = {}
            for col in df.columns:
                col_lower = str(col).strip().lower()
                if col_lower in treo_mapping:
                    rename_dict[col] = treo_mapping[col_lower]
            if rename_dict:
                df.rename(columns=rename_dict, inplace=True)

    if df is not None and filter_by_am:
        df = filter_df_by_logged_in_am(df)
        
    return df


def safe_to_numeric(series, fillna_val=0.0):
    if series is None:
        return fillna_val
    clean_series = series.astype(str).str.replace(',', '', regex=False).str.strip()
    return pd.to_numeric(clean_series, errors='coerce').fillna(fillna_val)

def normalize_pct_col(series):
    def convert_val(val):
        if pd.isna(val):
            return 0.0
        val_str = str(val).strip().replace(',', '.')
        if not val_str:
            return 0.0
        is_pct = False
        if val_str.endswith('%'):
            val_str = val_str[:-1].strip()
            is_pct = True
        try:
            f_val = float(val_str)
            if is_pct:
                return f_val / 100.0
            if f_val > 1.0:
                return f_val / 100.0
            return f_val
        except:
            return 0.0
    return series.apply(convert_val)

def parse_unstable_pct(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip()
    if not val_str:
        return 0.0
    is_pct = False
    if val_str.endswith('%'):
        val_str = val_str[:-1]
        is_pct = True
    try:
        f_val = float(val_str)
        if is_pct:
            return f_val
        if f_val <= 1.0 and f_val > 0.0:
            return f_val * 100.0
        return f_val
    except:
        return 0.0

# Helper function to clean strings for merge
def clean_str(val):
    if pd.isna(val):
        return ""
    return unicodedata.normalize('NFC', str(val).strip().lower())

def safe_divide(a, b):
    if b == 0:
        return 0.0
    return round((a / b) * 100, 2)

def clean_nan(obj):
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(x) for x in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
    elif pd.isna(obj):
        return None
    return obj


def clean_ops_df(df, sheet_type):
    if df is None:
        return None
    df = df.copy()
    
    # Strip column names
    df.columns = [str(c).strip() for c in df.columns]
    cols_lower = {c.lower(): c for c in df.columns}
    
    if sheet_type == "gtc":
        rename_map = {}
        core_gtc_cols = {
            'cấp quản lý': 'Cấp Quản Lý',
            'chi tiết': 'Chi tiết',
            'loại hàng': 'Loại Hàng',
            'time': 'Time',
            'volume': 'Volume',
            '% gán': '% Gán',
            '% gtc': '% GTC',
            '% chuyển trả': '% Chuyển trả',
            'leadtime': 'Leadtime',
            'lead time': 'Leadtime',
            'leadtime (h)': 'Leadtime',
            'leadtime giao': 'Leadtime',
            'lead time (h)': 'Leadtime',
            'am': 'AM',
            'tỉnh': 'Tỉnh'
        }
        for k, standard_name in core_gtc_cols.items():
            if k in cols_lower and cols_lower[k] != standard_name:
                rename_map[cols_lower[k]] = standard_name
        if rename_map:
            df = df.rename(columns=rename_map)
        return df
        
    elif sheet_type == "ltc":
        rename_map = {}
        # Check A: Shifted dataltc layout with 'IDBuuCuc' containing date strings
        is_idbuucuc_shifted = False
        if 'idbuucuc' in cols_lower and 'time' in cols_lower and 'volume' in cols_lower:
            first_id_val = str(df[cols_lower['idbuucuc']].dropna().iloc[0]) if len(df) > 0 else ''
            if ' - ' in first_id_val or '-' in first_id_val or '/' in first_id_val:
                is_idbuucuc_shifted = True
                
        if is_idbuucuc_shifted:
            rename_map[cols_lower['idbuucuc']] = 'Time'
            rename_map[cols_lower['time']] = 'Volume'
            rename_map[cols_lower['volume']] = '%Gán'
            rename_map[cols_lower['%gán']] = '%LTC'
            if '%ltc' in cols_lower:
                rename_map[cols_lower['%ltc']] = '%Đóng kiện'
            if '%đóng kiện' in cols_lower:
                rename_map[cols_lower['%đóng kiện']] = '%LC'
            if '%lc' in cols_lower:
                rename_map[cols_lower['%lc']] = 'Leadtime'
                
            other_cols = {
                'cấp quản lý': 'Cấp quản lý',
                'chi tiết': 'Chi tiết',
                'ca': 'Ca',
                'tỉnh': 'Tỉnh',
                'vùng': 'Vùng',
                'am': 'AM',
                'sản lượng lấy thành công': 'Sản Lượng Lấy Thành Công'
            }
            for k, standard_name in other_cols.items():
                if k in cols_lower and cols_lower[k] != standard_name:
                    rename_map[cols_lower[k]] = standard_name
        # Check B: Shifted dataltc layout with 'loại hàng' containing date strings
        elif 'loại hàng' in cols_lower and 'time' in cols_lower and 'volume' in cols_lower and '% gán' in cols_lower:
            rename_map[cols_lower['loại hàng']] = 'Time'
            rename_map[cols_lower['time']] = 'Volume'
            rename_map[cols_lower['volume']] = '% Gán'
            rename_map[cols_lower['% gán']] = '%LTC'
            if '% ltc' in cols_lower:
                rename_map[cols_lower['% ltc']] = '%LC'
            elif '%ltc' in cols_lower:
                rename_map[cols_lower['%ltc']] = '%LC'
            
            other_cols = {
                'cấp quản lý': 'Cấp quản lý',
                'chi tiết': 'Chi tiết',
                'leadtime': 'Leadtime',
                'lead time': 'Leadtime',
                'leadtime (h)': 'Leadtime',
                'leadtime giao': 'Leadtime',
                'lead time (h)': 'Leadtime',
                'sản lượng lấy thành công': 'Sản Lượng Lấy Thành Công'
            }
            for k, standard_name in other_cols.items():
                if k in cols_lower and cols_lower[k] != standard_name:
                    rename_map[cols_lower[k]] = standard_name
        else:
            # Normalize core columns
            core_ltc_cols = {
                'cấp quản lý': 'Cấp quản lý',
                'chi tiết': 'Chi tiết',
                'ca': 'Ca',
                'time': 'Time',
                'volume': 'Volume',
                'leadtime': 'Leadtime',
                'lead time': 'Leadtime',
                'leadtime (h)': 'Leadtime',
                'leadtime giao': 'Leadtime',
                'lead time (h)': 'Leadtime',
                'sản lượng lấy thành công': 'Sản Lượng Lấy Thành Công'
            }
            for k, standard_name in core_ltc_cols.items():
                if k in cols_lower and cols_lower[k] != standard_name:
                    rename_map[cols_lower[k]] = standard_name
                    
            if '%ltc' not in cols_lower:
                if '% ltc' in cols_lower:
                    rename_map[cols_lower['% ltc']] = '%LTC'
                elif '% gtc' in cols_lower:
                    rename_map[cols_lower['% gtc']] = '%LTC'
            else:
                rename_map[cols_lower['%ltc']] = '%LTC'
                
            if '%lc' not in cols_lower:
                if '% lc' in cols_lower:
                    rename_map[cols_lower['% lc']] = '%LC'
                elif '% chuyển trả' in cols_lower:
                    rename_map[cols_lower['% chuyển trả']] = '%LC'
            else:
                rename_map[cols_lower['%lc']] = '%LC'
                
            if '%gán' not in cols_lower:
                if '% gán' in cols_lower:
                    rename_map[cols_lower['% gán']] = '%Gán'
            else:
                rename_map[cols_lower['%gán']] = '%Gán'
            
        if rename_map:
            df = df.rename(columns=rename_map)
        return df
        
    elif sheet_type == "co_cau":
        return df
        
    elif sheet_type == "tts":
        rename_map = {}
        core_tts_cols = {
            'cấp quản lý': 'Cấp Quản Lý',
            'chi tiết': 'Chi tiết',
            'loại hàng': 'Loại Hàng',
            'time': 'Time',
            'volume': 'Volume',
            '% gán': '% Gán',
            '%gán': '% Gán',
            'leadtime': 'Leadtime',
            'lead time': 'Leadtime',
            'leadtime (h)': 'Leadtime',
            'leadtime giao': 'Leadtime',
            'lead time (h)': 'Leadtime',
            'am': 'AM',
            'tỉnh': 'Tỉnh'
        }
        for k, standard_name in core_tts_cols.items():
            if k in cols_lower and cols_lower[k] != standard_name:
                rename_map[cols_lower[k]] = standard_name
        if rename_map:
            df = df.rename(columns=rename_map)
        return df

# ==========================================
# 1. PROCESS OPERATIONAL REPORT
# ==========================================
def process_operational_report(df_gtc=None, df_ltc=None, df_tts=None, am=None, province=None, po=None, date=None):
    try:
        if df_gtc is None:
            df_gtc = safe_read_csv(resolve_path('ops_gtc.csv', write=False))
        df_gtc = clean_ops_df(df_gtc, "gtc")

        if df_ltc is None:
            df_ltc = safe_read_csv(resolve_path('ops_ltc.csv', write=False))
        df_ltc = clean_ops_df(df_ltc, "ltc")

        if df_tts is None:
            df_tts = safe_read_csv(resolve_path('ops_tts.csv', write=False))
        if df_tts is not None:
            df_tts = clean_ops_df(df_tts, "tts")
            
        if df_gtc is None or df_ltc is None:
            return {"error": "Không tìm thấy dữ liệu vận hành (ops_gtc.csv hoặc ops_ltc.csv)."}
            
        # Normalize Time column across all dataframes
        for _df in [df_gtc, df_ltc, df_tts]:
            if _df is not None:
                t_col = next((c for c in _df.columns if c.lower() in ['time', 'date', 'ngayltc', 'ngay']), None)
                if t_col:
                    _df['Time'] = _df[t_col]
                elif 'Time' not in _df.columns:
                    _df['Time'] = "Không xác định"

        # Apply filters to GTC, LTC, TTS if provided
        if am:
            am_str = str(am).strip()
            if 'mapped_am' in df_gtc.columns or 'AM' in df_gtc.columns:
                am_col = 'mapped_am' if 'mapped_am' in df_gtc.columns else 'AM'
                df_gtc = df_gtc[df_gtc[am_col].astype(str).str.strip() == am_str]
            if 'mapped_am' in df_ltc.columns or 'AM' in df_ltc.columns:
                am_col = 'mapped_am' if 'mapped_am' in df_ltc.columns else 'AM'
                df_ltc = df_ltc[df_ltc[am_col].astype(str).str.strip() == am_str]
            if df_tts is not None and ('mapped_am' in df_tts.columns or 'AM' in df_tts.columns):
                am_col = 'mapped_am' if 'mapped_am' in df_tts.columns else 'AM'
                df_tts = df_tts[df_tts[am_col].astype(str).str.strip() == am_str]
                
        if province:
            prov_str = str(province).strip()
            if 'mapped_prov' in df_gtc.columns or 'Tỉnh' in df_gtc.columns:
                prov_col = 'mapped_prov' if 'mapped_prov' in df_gtc.columns else 'Tỉnh'
                df_gtc = df_gtc[df_gtc[prov_col].astype(str).str.strip() == prov_str]
            if 'mapped_prov' in df_ltc.columns or 'Tỉnh' in df_ltc.columns:
                prov_col = 'mapped_prov' if 'mapped_prov' in df_ltc.columns else 'Tỉnh'
                df_ltc = df_ltc[df_ltc[prov_col].astype(str).str.strip() == prov_str]
            if df_tts is not None and ('mapped_prov' in df_tts.columns or 'Tỉnh' in df_tts.columns):
                prov_col = 'mapped_prov' if 'mapped_prov' in df_tts.columns else 'Tỉnh'
                df_tts = df_tts[df_tts[prov_col].astype(str).str.strip() == prov_str]
                
        if po:
            po_str = str(po).strip()
            if 'clean_bc' in df_gtc.columns or 'Chi tiết' in df_gtc.columns:
                po_col = 'clean_bc' if 'clean_bc' in df_gtc.columns else 'Chi tiết'
                if po_col == 'clean_bc':
                    df_gtc = df_gtc[df_gtc[po_col].astype(str).str.strip() == po_str.lower()]
                else:
                    df_gtc = df_gtc[df_gtc[po_col].astype(str).str.strip() == po_str]
            if 'clean_bc' in df_ltc.columns or 'Chi tiết' in df_ltc.columns:
                po_col = 'clean_bc' if 'clean_bc' in df_ltc.columns else 'Chi tiết'
                if po_col == 'clean_bc':
                    df_ltc = df_ltc[df_ltc[po_col].astype(str).str.strip() == po_str.lower()]
                else:
                    df_ltc = df_ltc[df_ltc[po_col].astype(str).str.strip() == po_str]
            if df_tts is not None and ('clean_bc' in df_tts.columns or 'Chi tiết' in df_tts.columns):
                po_col = 'clean_bc' if 'clean_bc' in df_tts.columns else 'Chi tiết'
                if po_col == 'clean_bc':
                    df_tts = df_tts[df_tts[po_col].astype(str).str.strip() == po_str.lower()]
                else:
                    df_tts = df_tts[df_tts[po_col].astype(str).str.strip() == po_str]
        
        vol_gtc_col = next((c for c in df_gtc.columns if c.lower() == 'volume'), None)
        if vol_gtc_col:
            df_gtc['Volume'] = safe_to_numeric(df_gtc[vol_gtc_col])
            df_gtc = df_gtc.dropna(subset=['Volume']).copy()
        else:
            df_gtc['Volume'] = 0.0

        if 'Leadtime' not in df_gtc.columns:
            df_gtc['Leadtime'] = np.nan
        else:
            df_gtc['Leadtime'] = pd.to_numeric(df_gtc['Leadtime'], errors='coerce')
        
        vol_ltc_col = next((c for c in df_ltc.columns if c.lower() == 'volume'), None)
        if vol_ltc_col:
            df_ltc['Volume'] = safe_to_numeric(df_ltc[vol_ltc_col])
            df_ltc = df_ltc.dropna(subset=['Volume']).copy()
        else:
            df_ltc['Volume'] = 0.0

        if 'Leadtime' not in df_ltc.columns:
            df_ltc['Leadtime'] = np.nan
        else:
            df_ltc['Leadtime'] = pd.to_numeric(df_ltc['Leadtime'], errors='coerce')
        
        # Calculate overall metrics
        gtc_pct_col = next((c for c in df_gtc.columns if c.lower() in ['% gtc', '%gtc']), None)
        df_gtc['% GTC'] = normalize_pct_col(df_gtc[gtc_pct_col]) if gtc_pct_col else 0.0

        gan_pct_col = next((c for c in df_gtc.columns if c.lower() in ['% gán', '%gán']), None)
        df_gtc['% Gán'] = normalize_pct_col(df_gtc[gan_pct_col]) if gan_pct_col else 0.0

        ct_pct_col = next((c for c in df_gtc.columns if c.lower() in ['% chuyển trả', '%chuyển trả']), None)
        df_gtc['% Chuyển trả'] = normalize_pct_col(df_gtc[ct_pct_col]) if ct_pct_col else 0.0

        ltc_pct_col = next((c for c in df_ltc.columns if c.lower() in ['%ltc', '% ltc']), None)
        df_ltc['%LTC'] = normalize_pct_col(df_ltc[ltc_pct_col]) if ltc_pct_col else 0.0
        
        df_gtc['delivered_vol'] = df_gtc['Volume'] * df_gtc['% GTC']
        df_gtc['assigned_vol'] = df_gtc['Volume'] * df_gtc['% Gán']
        df_gtc['return_vol'] = df_gtc['Volume'] * df_gtc['% Chuyển trả']
        
        df_ltc.columns = [c.strip() for c in df_ltc.columns]
        if 'Sản Lượng Lấy Thành Công' in df_ltc.columns:
            df_ltc['ltc_vol'] = safe_to_numeric(df_ltc['Sản Lượng Lấy Thành Công'])
        else:
            df_ltc['ltc_vol'] = df_ltc['Volume'] * df_ltc['%LTC']
        
        # Align dates: ensure both df_gtc and df_ltc cover all dates present in either dataset
        if len(df_gtc) > 0 and len(df_ltc) > 0:
            gtc_dates = set(df_gtc['Time'].dropna().unique())
            ltc_dates = set(df_ltc['Time'].dropna().unique())
            
            missing_ltc_dates = [d for d in gtc_dates if d not in ltc_dates]
            if missing_ltc_dates and len(ltc_dates) > 0:
                try:
                    ltc_dates_sorted = sorted(list(ltc_dates), key=lambda x: pd.to_datetime(str(x).split(' - ')[0]))
                    latest_ltc_date = ltc_dates_sorted[-1]
                except Exception as e:
                    latest_ltc_date = list(ltc_dates)[-1]
                
                latest_ltc_rows = df_ltc[df_ltc['Time'] == latest_ltc_date].copy()
                new_rows_list = []
                for missing_date in missing_ltc_dates:
                    copied = latest_ltc_rows.copy()
                    copied['Time'] = missing_date
                    new_rows_list.append(copied)
                if new_rows_list:
                    df_ltc = pd.concat([df_ltc] + new_rows_list, ignore_index=True)

            missing_gtc_dates = [d for d in ltc_dates if d not in gtc_dates]
            if missing_gtc_dates and len(gtc_dates) > 0:
                try:
                    gtc_dates_sorted = sorted(list(gtc_dates), key=lambda x: pd.to_datetime(str(x).split(' - ')[0]))
                    latest_gtc_date = gtc_dates_sorted[-1]
                except Exception as e:
                    latest_gtc_date = list(gtc_dates)[-1]
                
                latest_gtc_rows = df_gtc[df_gtc['Time'] == latest_gtc_date].copy()
                new_rows_list = []
                for missing_date in missing_gtc_dates:
                    copied = latest_gtc_rows.copy()
                    copied['Time'] = missing_date
                    new_rows_list.append(copied)
                if new_rows_list:
                    df_gtc = pd.concat([df_gtc] + new_rows_list, ignore_index=True)
        
        # Determine the latest date dynamically from Time column safely
        latest_date_gtc = None
        if 'Time' in df_gtc.columns and len(df_gtc) > 0:
            times = df_gtc['Time'].dropna().unique()
            try:
                dates_sorted = sorted(times, key=lambda x: pd.to_datetime(str(x).split(' - ')[0]))
                if dates_sorted:
                    latest_date_gtc = dates_sorted[-1]
            except Exception as e:
                print(f"Error sorting GTC dates: {e}")
                if len(times) > 0:
                    latest_date_gtc = times[-1]
                    
        latest_date_ltc = None
        if 'Time' in df_ltc.columns and len(df_ltc) > 0:
            times = df_ltc['Time'].dropna().unique()
            try:
                dates_sorted = sorted(times, key=lambda x: pd.to_datetime(str(x).split(' - ')[0]))
                if dates_sorted:
                    latest_date_ltc = dates_sorted[-1]
            except Exception as e:
                print(f"Error sorting LTC dates: {e}")
                if len(times) > 0:
                    latest_date_ltc = times[-1]
                    
        if date:
            latest_date_gtc = date
            latest_date_ltc = date
            
        df_gtc_latest = df_gtc[df_gtc['Time'] == latest_date_gtc] if latest_date_gtc else df_gtc
        df_ltc_latest = df_ltc[df_ltc['Time'] == latest_date_ltc] if latest_date_ltc else df_ltc
        
        total_vol = float(df_gtc_latest['Volume'].sum())
        total_gtc_vol = float(df_gtc_latest['delivered_vol'].sum())
        total_assigned_vol = float(df_gtc_latest['assigned_vol'].sum())
        total_return_vol = float(df_gtc_latest['return_vol'].sum())
        total_inventory_vol = float((df_gtc_latest['Volume'] - df_gtc_latest['delivered_vol'] - df_gtc_latest['return_vol']).sum()) # rough estimate of tồn
        
        overall_gtc = safe_divide(total_gtc_vol, total_vol)
        overall_gan = safe_divide(total_assigned_vol, total_vol)
        
        # Calculate LTC metrics
        total_ltc_vol_raw = float(df_ltc_latest['Volume'].sum())
        total_on_ltc_vol = float(df_ltc_latest['ltc_vol'].sum())
        overall_ltc = safe_divide(total_on_ltc_vol, total_ltc_vol_raw)
        total_ltc_vol = float(df_ltc_latest['Sản Lượng Lấy Thành Công'].sum()) if 'Sản Lượng Lấy Thành Công' in df_ltc_latest.columns else total_on_ltc_vol
        
        # Average Leadtime
        avg_leadtime = float(df_gtc_latest['Leadtime'].mean()) if ('Leadtime' in df_gtc_latest.columns and not df_gtc_latest['Leadtime'].isna().all()) else 0.0
        
        # Shift breakdown (Ca 1, Ca 2, Tồn) in Datagtc
        loai_hang_col = next((c for c in df_gtc_latest.columns if c.lower() in ['loại hàng', 'loai hang', 'ca']), None)
        if loai_hang_col:
            ca1_vol = float(df_gtc_latest[df_gtc_latest[loai_hang_col] == 'Hàng Mới Ca 1']['Volume'].sum())
            ca2_vol = float(df_gtc_latest[df_gtc_latest[loai_hang_col] == 'Hàng Mới Ca 2']['Volume'].sum())
            ton_vol = float(df_gtc_latest[df_gtc_latest[loai_hang_col] == 'Hàng Tồn']['Volume'].sum())
        else:
            ca1_vol = 0.0
            ca2_vol = 0.0
            ton_vol = 0.0
        new_vol = ca1_vol + ca2_vol
        
        # Top 10 Best and Worst Post Offices by GTC
        gtc_agg = {'Volume': 'sum', 'delivered_vol': 'sum'}
        if 'Leadtime' in df_gtc_latest.columns:
            gtc_agg['Leadtime'] = 'mean'
        chi_tiet_gtc = next((c for c in df_gtc_latest.columns if c.lower() in ['chi tiết', 'chitiết', 'bưu cục', 'buucuc', 'bc', 'warehouse_name']), 'Chi tiết')
        po_gtc = df_gtc_latest.groupby(chi_tiet_gtc).agg(gtc_agg).reset_index()
        if chi_tiet_gtc != 'Chi tiết':
            po_gtc = po_gtc.rename(columns={chi_tiet_gtc: 'Chi tiết'})
        if 'Leadtime' not in po_gtc.columns:
            po_gtc['Leadtime'] = 0.0
        po_gtc['% GTC'] = (po_gtc['delivered_vol'] / po_gtc['Volume']) * 100
        po_gtc = po_gtc[po_gtc['Volume'] >= 100] # filter out small volumes for ranking
        
        top_10_gtc = po_gtc.sort_values(by='% GTC', ascending=False).head(10).to_dict(orient='records')
        worst_10_gtc = po_gtc.sort_values(by='% GTC', ascending=True).head(10).to_dict(orient='records')
        
        # Top 10 Best and Worst Post Offices by LTC
        ltc_agg = {'Volume': 'sum', 'ltc_vol': 'sum'}
        if 'Leadtime' in df_ltc_latest.columns:
            ltc_agg['Leadtime'] = 'mean'
        chi_tiet_ltc = next((c for c in df_ltc_latest.columns if c.lower() in ['chi tiết', 'chitiết', 'bưu cục', 'buucuc', 'bc', 'warehouse_name']), 'Chi tiết')
        po_ltc = df_ltc_latest.groupby(chi_tiet_ltc).agg(ltc_agg).reset_index()
        if chi_tiet_ltc != 'Chi tiết':
            po_ltc = po_ltc.rename(columns={chi_tiet_ltc: 'Chi tiết'})
        if 'Leadtime' not in po_ltc.columns:
            po_ltc['Leadtime'] = 0.0
        po_ltc['% LTC'] = (po_ltc['ltc_vol'] / po_ltc['Volume']) * 100
        po_ltc = po_ltc[po_ltc['Volume'] >= 100]
        
        top_10_ltc = po_ltc.sort_values(by='% LTC', ascending=False).head(10).to_dict(orient='records')
        worst_10_ltc = po_ltc.sort_values(by='% LTC', ascending=True).head(10).to_dict(orient='records')
        
        # Xu hướng GTC & Volume theo ngày
        trend_gtc = df_gtc.groupby('Time').agg({'Volume': 'sum', 'delivered_vol': 'sum', 'assigned_vol': 'sum'}).reset_index()
        trend_gtc['% GTC'] = (trend_gtc['delivered_vol'] / trend_gtc['Volume']) * 100
        trend_gtc['% Gán'] = (trend_gtc['assigned_vol'] / trend_gtc['Volume']) * 100
        trend_gtc_list = trend_gtc.sort_values('Time').to_dict(orient='records')
        
        # Xu hướng LTC theo ngày
        trend_ltc = df_ltc.groupby('Time').agg({'Volume': 'sum', 'ltc_vol': 'sum'}).reset_index()
        trend_ltc['% LTC'] = (trend_ltc['ltc_vol'] / trend_ltc['Volume']) * 100
        trend_ltc_list = trend_ltc.sort_values('Time').to_dict(orient='records')
        
        # Calculate ODR TTS from ODR TTS.csv
        overall_odr_tts = None
        trend_odr_list = []
        odr_path = resolve_path('ODR TTS.csv', write=False)
        try:
            df_odr = safe_read_csv(odr_path)
            if df_odr is not None and not df_odr.empty:
                df_odr.columns = [str(c).strip() for c in df_odr.columns]
                t_col_odr = next((c for c in df_odr.columns if c.lower() in ['time', 'date', 'ngay']), 'Time')
                if t_col_odr in df_odr.columns:
                    df_odr['Time'] = df_odr[t_col_odr]
                gtc_col_odr = next((c for c in df_odr.columns if c.lower() == 'gtc'), 'GTC')
                df_odr['GTC'] = pd.to_numeric(df_odr[gtc_col_odr] if gtc_col_odr in df_odr.columns else 0, errors='coerce')
                ontime_col = next((c for c in df_odr.columns if c.lower() in ['%ontime', '% ontime', '%on time', '% on time']), '%Ontime')
                df_odr['%Ontime'] = normalize_pct_col(df_odr[ontime_col]) if ontime_col in df_odr.columns else 0.0
                df_odr['ontime_vol'] = df_odr['GTC'] * df_odr['%Ontime']
                
                # Trend
                trend_odr = df_odr.groupby('Time').agg({'GTC': 'sum', 'ontime_vol': 'sum'}).reset_index()
                trend_odr['% ODR'] = (trend_odr['ontime_vol'] / trend_odr['GTC']) * 100
                trend_odr_list = trend_odr.sort_values('Time').to_dict(orient='records')
                
                # Find for latest_date_gtc
                if latest_date_gtc:
                    df_latest_odr = df_odr[df_odr['Time'] == latest_date_gtc]
                    if not df_latest_odr.empty:
                        gtc_sum_odr = df_latest_odr['GTC'].sum()
                        ontime_sum_odr = df_latest_odr['ontime_vol'].sum()
                        overall_odr_tts = round(ontime_sum_odr / gtc_sum_odr * 100, 2) if gtc_sum_odr > 0 else 0.0
        except Exception as e:
            print(f"Error processing ODR TTS.csv: {e}")
                
        # Calculate TTS overall assign rate and daily trend
        overall_gan_tts = None
        trend_tts_list = []
        if df_tts is not None:
            try:
                df_tts = df_tts.dropna(subset=["Volume"]).copy()
                df_tts['Volume'] = pd.to_numeric(df_tts['Volume'], errors='coerce')
                df_tts['% Gán'] = normalize_pct_col(df_tts['% Gán'])
                df_tts['assigned_vol'] = df_tts['Volume'] * df_tts['% Gán']
                
                latest_date_tts = None
                if 'Time' in df_tts.columns and len(df_tts) > 0:
                    times_tts = df_tts['Time'].dropna().unique()
                    try:
                        dates_sorted_tts = sorted(times_tts, key=lambda x: pd.to_datetime(str(x).split(' - ')[0]))
                        if dates_sorted_tts:
                            latest_date_tts = dates_sorted_tts[-1]
                    except Exception as e:
                        print(f"Error sorting TTS dates: {e}")
                        if len(times_tts) > 0:
                            latest_date_tts = times_tts[-1]
                            
                # Calculate overall_gan_tts for latest date
                if latest_date_tts:
                    df_tts_latest = df_tts[df_tts['Time'] == latest_date_tts]
                    if not df_tts_latest.empty:
                        vol_sum_tts = df_tts_latest['Volume'].sum()
                        assigned_sum_tts = df_tts_latest['assigned_vol'].sum()
                        overall_gan_tts = safe_divide(assigned_sum_tts, vol_sum_tts)
                        
                # Daily Gán TTS Trend
                if 'Time' in df_tts.columns:
                    trend_tts = df_tts.groupby('Time').agg({'Volume': 'sum', 'assigned_vol': 'sum'}).reset_index()
                    trend_tts['% Gán'] = (trend_tts['assigned_vol'] / trend_tts['Volume']) * 100
                    trend_tts_list = trend_tts.sort_values('Time').to_dict(orient='records')
            except Exception as e:
                print(f"Error processing TTS sheet: {e}")
        
        # Get FD statistics based on filters (AM, Province, PO)
        fd_n = 0.0
        fd_n1 = 0.0
        vs_n1 = 0.0
        fd_n7 = 0.0
        vs_n7 = 0.0
        
        global FD_CACHE
        fd_data = FD_CACHE
        if fd_data is None or "error" in fd_data:
            fd_data = process_fd_report()
            
        if fd_data and "error" not in fd_data:
            found = False
            # Check po filter
            if po:
                po_clean = str(po).strip().lower()
                for r in fd_data.get('po', []):
                    if r.get('post_office', '').strip().lower() == po_clean:
                        fd_n = r.get('fd_n', 0.0)
                        fd_n1 = r.get('fd_n1', 0.0)
                        vs_n1 = r.get('vs_n1', 0.0)
                        fd_n7 = r.get('fd_n7', 0.0)
                        vs_n7 = r.get('vs_n7', 0.0)
                        found = True
                        break
            # Check am filter
            if not found and am:
                am_clean = str(am).strip().lower()
                for r in fd_data.get('am', []):
                    if r.get('am', '').strip().lower() == am_clean:
                        fd_n = r.get('fd_n', 0.0)
                        fd_n1 = r.get('fd_n1', 0.0)
                        vs_n1 = r.get('vs_n1', 0.0)
                        fd_n7 = r.get('fd_n7', 0.0)
                        vs_n7 = r.get('vs_n7', 0.0)
                        found = True
                        break
            # Check province filter
            if not found and province:
                prov_clean = str(province).strip().lower()
                for r in fd_data.get('province', []):
                    if r.get('province', '').strip().lower() == prov_clean:
                        fd_n = r.get('fd_n', 0.0)
                        fd_n1 = r.get('fd_n1', 0.0)
                        vs_n1 = r.get('vs_n1', 0.0)
                        fd_n7 = r.get('fd_n7', 0.0)
                        vs_n7 = r.get('vs_n7', 0.0)
                        found = True
                        break
            # Fallback to kpi / Tổng NTB
            if not found:
                kpi = fd_data.get('kpi', {})
                fd_n = kpi.get('fd_n', 0.0)
                fd_n1 = kpi.get('fd_n1', 0.0)
                vs_n1 = kpi.get('vs_n1', 0.0)
                fd_n7 = kpi.get('fd_n7', 0.0)
                vs_n7 = kpi.get('vs_n7', 0.0)

        return {
            "total_volume": int(total_vol),
            "overall_gtc": overall_gtc,
            "overall_gan": overall_gan,
            "overall_gan_tts": overall_gan_tts,
            "overall_ltc": overall_ltc,
            "overall_odr_tts": overall_odr_tts,
            "avg_leadtime": round(avg_leadtime, 2),
            "ca1_vol": int(ca1_vol),
            "ca2_vol": int(ca2_vol),
            "ton_vol": int(ton_vol),
            "new_vol": int(new_vol),
            "top_10_gtc": top_10_gtc,
            "worst_10_gtc": worst_10_gtc,
            "top_10_ltc": top_10_ltc,
            "worst_10_ltc": worst_10_ltc,
            "trend_gtc": trend_gtc_list,
            "trend_ltc": trend_ltc_list,
            "trend_odr": trend_odr_list,
            "trend_tts": trend_tts_list,
            "overall_fd": fd_n,
            "fd_n1": fd_n1,
            "fd_vs_n1": vs_n1,
            "fd_n7": fd_n7,
            "fd_vs_n7": vs_n7
        }
    except Exception as e:
        return {"error": f"Lỗi xử lý file báo cáo vận hành: {str(e)}"}

# ==========================================
# 2. PROCESS OPR TTS REPORT
# ==========================================
def process_opr_report(df_opr=None, df_oe=None, df_rawopr=None, am=None, province=None, post_office=None):
    try:
        if df_opr is None:
            df_opr = safe_read_csv(resolve_path('opr_opr.csv', write=False))
        if df_oe is None:
            df_oe = safe_read_csv(resolve_path('opr_oe.csv', write=False))
        if df_rawopr is None:
            df_rawopr = safe_read_csv(resolve_path('opr_raw.csv', write=False))
            
        if df_opr is None or df_oe is None:
            return {"error": "Không tìm thấy dữ liệu OPR (opr_opr.csv hoặc opr_oe.csv)."}
        
        # Normalize df_opr columns
        df_opr.columns = [str(c).strip() for c in df_opr.columns]
        opr_cols_lower = {c.lower(): c for c in df_opr.columns}
        opr_rename = {}
        if 'ngayltc' in opr_cols_lower:
            opr_rename[opr_cols_lower['ngayltc']] = 'NgayLTC'
            
        if 'vol_ltc' in opr_cols_lower:
            opr_rename[opr_cols_lower['vol_ltc']] = 'vol_ltc'
        elif 'don_ltc' in opr_cols_lower:
            opr_rename[opr_cols_lower['don_ltc']] = 'vol_ltc'
        elif 'don ltc' in opr_cols_lower:
            opr_rename[opr_cols_lower['don ltc']] = 'vol_ltc'
            
        if 'ot' in opr_cols_lower:
            opr_rename[opr_cols_lower['ot']] = 'ot'
        elif 'don_ontime' in opr_cols_lower:
            opr_rename[opr_cols_lower['don_ontime']] = 'ot'
        elif 'don ontime' in opr_cols_lower:
            opr_rename[opr_cols_lower['don ontime']] = 'ot'
            
        if 'am' in opr_cols_lower:
            opr_rename[opr_cols_lower['am']] = 'AM'
            
        if 'ly_do_tre_12h' in opr_cols_lower:
            opr_rename[opr_cols_lower['ly_do_tre_12h']] = 'ly_do_tre_12h'
            
        if 'tutinh' in opr_cols_lower:
            opr_rename[opr_cols_lower['tutinh']] = 'tutinh'
        elif 'tu tinh' in opr_cols_lower:
            opr_rename[opr_cols_lower['tu tinh']] = 'tutinh'
            
        if 'kholay' in opr_cols_lower:
            opr_rename[opr_cols_lower['kholay']] = 'kholay'
        elif 'kho lay' in opr_cols_lower:
            opr_rename[opr_cols_lower['kho lay']] = 'kholay'
            
        if 'vung' in opr_cols_lower:
            opr_rename[opr_cols_lower['vung']] = 'vung'
        elif 'tuvung' in opr_cols_lower:
            opr_rename[opr_cols_lower['tuvung']] = 'vung'
        elif 'tu vung' in opr_cols_lower:
            opr_rename[opr_cols_lower['tu vung']] = 'vung'
            
        if opr_rename:
            df_opr = df_opr.rename(columns=opr_rename)
            
        for col in ['NgayLTC', 'vol_ltc', 'ot', 'AM']:
            if col not in df_opr.columns:
                df_opr[col] = np.nan if col in ['NgayLTC', 'AM'] else 0.0

        # Normalize df_oe columns (from RAW n-1)
        df_oe.columns = [str(c).strip() for c in df_oe.columns]
        oe_cols_lower = {c.lower(): c for c in df_oe.columns}
        oe_rename = {}
        if 'bc lấy' in oe_cols_lower:
            oe_rename[oe_cols_lower['bc lấy']] = 'kholay'
        elif 'bc lay' in oe_cols_lower:
            oe_rename[oe_cols_lower['bc lay']] = 'kholay'
        elif 'kholay' in oe_cols_lower:
            oe_rename[oe_cols_lower['kholay']] = 'kholay'
            
        if 'thời gian tạo' in oe_cols_lower:
            oe_rename[oe_cols_lower['thời gian tạo']] = 'khung_gio_tao_don'
        elif 'thoi gian tao' in oe_cols_lower:
            oe_rename[oe_cols_lower['thoi gian tao']] = 'khung_gio_tao_don'
        elif 'khung_gio_tao_don' in oe_cols_lower:
            oe_rename[oe_cols_lower['khung_gio_tao_don']] = 'khung_gio_tao_don'
            
        if 'ly_do_tre_12h' in oe_cols_lower:
            oe_rename[oe_cols_lower['ly_do_tre_12h']] = 'ly_do_tre_12h'
            
        if 'sellername' in oe_cols_lower:
            oe_rename[oe_cols_lower['sellername']] = 'sellername'
            
        if 'madh' in oe_cols_lower:
            oe_rename[oe_cols_lower['madh']] = 'madh'
            
        if 'am' in oe_cols_lower:
            oe_rename[oe_cols_lower['am']] = 'AM'
            
        if 'vung' in oe_cols_lower:
            oe_rename[oe_cols_lower['vung']] = 'vung'
            
        if oe_rename:
            df_oe = df_oe.rename(columns=oe_rename)
            
        required_oe_cols = ['tutinh', 'kholay', 'sellername', 'khung_gio_tao_don', 'ly_do_tre_12h', 'madh', 'AM']
        for col in required_oe_cols:
            if col not in df_oe.columns:
                if col == 'tutinh' and 'vung' in df_oe.columns:
                    df_oe['tutinh'] = df_oe['vung']
                else:
                    df_oe[col] = np.nan

        # Normalize df_rawopr columns
        if df_rawopr is not None and not df_rawopr.empty:
            df_rawopr.columns = [str(c).strip() for c in df_rawopr.columns]
            rawopr_cols_lower = {c.lower(): c for c in df_rawopr.columns}
            rawopr_rename = {}
            if 'ngayltc' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['ngayltc']] = 'NgayLTC'
                
            if 'vol_ltc' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['vol_ltc']] = 'vol_ltc'
            elif 'don_ltc' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['don_ltc']] = 'vol_ltc'
            elif 'don ltc' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['don ltc']] = 'vol_ltc'
                
            if 'ot' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['ot']] = 'ot'
            elif 'don_ontime' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['don_ontime']] = 'ot'
            elif 'don ontime' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['don ontime']] = 'ot'
                
            if 'am' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['am']] = 'AM'
                
            if 'ly_do_tre_12h' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['ly_do_tre_12h']] = 'ly_do_tre_12h'
                
            if 'tutinh' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['tutinh']] = 'tutinh'
            elif 'tu tinh' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['tu tinh']] = 'tutinh'
                
            if 'kholay' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['kholay']] = 'kholay'
            elif 'kho lay' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['kho lay']] = 'kholay'
                
            if 'vung' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['vung']] = 'vung'
            elif 'tuvung' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['tuvung']] = 'vung'
            elif 'tu vung' in rawopr_cols_lower:
                rawopr_rename[rawopr_cols_lower['tu vung']] = 'vung'
                
            if rawopr_rename:
                df_rawopr = df_rawopr.rename(columns=rawopr_rename)
                
            for col in ['NgayLTC', 'vol_ltc', 'ot', 'AM']:
                if col not in df_rawopr.columns:
                    df_rawopr[col] = np.nan if col in ['NgayLTC', 'AM'] else 0.0

        # Standardize AM spelling mismatches
        for df in [df_opr, df_oe, df_rawopr]:
            if df is not None and 'AM' in df.columns:
                df['AM'] = df['AM'].replace({'Huỳnh Tấn Hiền': 'Huỳnh Tấn Hiển'})

        # Filter OPR data to NTB region only
        if 'vung' in df_opr.columns:
            df_opr = df_opr[df_opr['vung'].astype(str).str.strip() == 'NTB'].copy()
        elif 'tutinh' in df_opr.columns:
            ntb_provinces = ['Bình Thuận', 'Ninh Thuận', 'Lâm Đồng', 'Khánh Hòa', 'Đắk Nông']
            df_opr = df_opr[df_opr['tutinh'].astype(str).str.strip().isin(ntb_provinces)].copy()

        # Build dynamic mapping of kholay -> tutinh from df_opr
        po_to_prov = {}
        if 'kholay' in df_opr.columns and 'tutinh' in df_opr.columns:
            tmp_df = df_opr.dropna(subset=['kholay', 'tutinh'])
            po_to_prov = dict(zip(tmp_df['kholay'].astype(str).str.strip(), tmp_df['tutinh'].astype(str).str.strip()))
            
        if df_oe is not None and not df_oe.empty:
            if 'vung' in df_oe.columns:
                df_oe = df_oe[df_oe['vung'].astype(str).str.strip() == 'NTB'].copy()
            elif 'tutinh' in df_oe.columns:
                ntb_provinces = ['Bình Thuận', 'Ninh Thuận', 'Lâm Đồng', 'Khánh Hòa', 'Đắk Nông']
                df_oe = df_oe[df_oe['tutinh'].astype(str).str.strip().isin(ntb_provinces)].copy()
            
            if 'kholay' in df_oe.columns:
                df_oe['tutinh_mapped'] = df_oe['kholay'].astype(str).str.strip().map(po_to_prov)
                if 'tutinh' in df_oe.columns:
                    df_oe['tutinh'] = df_oe['tutinh_mapped'].fillna(df_oe['tutinh'])
                else:
                    df_oe['tutinh'] = df_oe['tutinh_mapped']
                if 'tutinh_mapped' in df_oe.columns:
                    df_oe = df_oe.drop(columns=['tutinh_mapped'])

        if df_rawopr is not None and not df_rawopr.empty:
            if 'vung' in df_rawopr.columns:
                df_rawopr = df_rawopr[df_rawopr['vung'].astype(str).str.strip() == 'NTB'].copy()
            elif 'tutinh' in df_rawopr.columns:
                ntb_provinces = ['Bình Thuận', 'Ninh Thuận', 'Lâm Đồng', 'Khánh Hòa', 'Đắk Nông']
                df_rawopr = df_rawopr[df_rawopr['tutinh'].astype(str).str.strip().isin(ntb_provinces)].copy()

        # Apply active filters dynamically
        if am and am.strip():
            df_opr = df_opr[df_opr['AM'].astype(str).str.strip() == am.strip()]
            if df_oe is not None and not df_oe.empty:
                df_oe = df_oe[df_oe['AM'].astype(str).str.strip() == am.strip()]
            if df_rawopr is not None and not df_rawopr.empty:
                df_rawopr = df_rawopr[df_rawopr['AM'].astype(str).str.strip() == am.strip()]
                
        if province and province.strip():
            df_opr = df_opr[df_opr['tutinh'].astype(str).str.strip() == province.strip()]
            if df_oe is not None and not df_oe.empty:
                df_oe = df_oe[df_oe['tutinh'].astype(str).str.strip() == province.strip()]
            if df_rawopr is not None and not df_rawopr.empty:
                df_rawopr = df_rawopr[df_rawopr['tutinh'].astype(str).str.strip() == province.strip()]
                
        if post_office and post_office.strip():
            df_opr = df_opr[df_opr['kholay'].astype(str).str.strip() == post_office.strip()]
            if df_oe is not None and not df_oe.empty:
                df_oe = df_oe[df_oe['kholay'].astype(str).str.strip() == post_office.strip()]
            if df_rawopr is not None and not df_rawopr.empty:
                df_rawopr = df_rawopr[df_rawopr['kholay'].astype(str).str.strip() == post_office.strip()]

        df_opr = df_opr.dropna(subset=["vol_ltc"]).copy()
        
        # Find latest date in df_opr dynamically
        df_opr_dates = pd.to_datetime(df_opr['NgayLTC'], errors='coerce').dt.strftime('%Y-%m-%d')
        valid_dates = df_opr_dates.dropna().unique()
        report_date_str = max(valid_dates) if len(valid_dates) > 0 else None
        
        # Calculate OPR Overall (only for the latest report date if multiple dates exist)
        if report_date_str:
            df_opr_all_dates = df_opr.copy()
            df_opr_dates_str = df_opr_dates
            df_opr = df_opr[df_opr_dates == report_date_str].copy()
        else:
            df_opr_all_dates = df_opr.copy()
            df_opr_dates_str = df_opr_dates
            
        total_vol = float(df_opr['vol_ltc'].sum())
        total_ot = float(df_opr['ot'].sum())
        overall_opr = safe_divide(total_ot, total_vol)
        total_late = max(0.0, total_vol - total_ot)
        
        # Calculate OPR comparisons (n-1 and cùng kỳ thứ)
        opr_n1 = None
        opr_wk = None
        delta_n1 = None
        delta_wk = None
        
        if df_rawopr is not None and not df_rawopr.empty:
            try:
                df_rawopr_dates = pd.to_datetime(df_rawopr['NgayLTC'], errors='coerce').dt.strftime('%Y-%m-%d')
                
                if report_date_str:
                    report_dt = pd.to_datetime(report_date_str)
                    
                    n1_date_str = (report_dt - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                    wk_date_str = (report_dt - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
                    
                    # Create temporary date columns using unfiltered df_opr_all_dates
                    df_opr_temp = df_opr_all_dates.copy()
                    df_rawopr_temp = df_rawopr.copy()
                    df_opr_temp['NgayLTC_str'] = df_opr_dates_str
                    df_rawopr_temp['NgayLTC_str'] = df_rawopr_dates
                    
                    cols = ['NgayLTC_str', 'vol_ltc', 'ot']
                    df_comb = pd.concat([df_opr_temp[cols], df_rawopr_temp[cols]], ignore_index=True)
                    df_comb = df_comb.dropna(subset=['NgayLTC_str', 'vol_ltc', 'ot'])
                    
                    def get_opr_for_date(df, date_str):
                        df_date = df[df['NgayLTC_str'] == date_str]
                        if len(df_date) == 0:
                            return None
                        t_vol = float(df_date['vol_ltc'].sum())
                        t_ot = float(df_date['ot'].sum())
                        return safe_divide(t_ot, t_vol)
                    
                    opr_n1 = get_opr_for_date(df_comb, n1_date_str)
                    opr_wk = get_opr_for_date(df_comb, wk_date_str)
                    
                    if opr_n1 is not None:
                        delta_n1 = round(overall_opr - opr_n1, 2)
                    if opr_wk is not None:
                        delta_wk = round(overall_opr - opr_wk, 2)
            except Exception as ex:
                print(f"Lỗi tính toán OPR so sánh: {ex}")
        
        # Calculate OPR by Creation Time Slot (Khung giờ tạo)
        time_slot_col = 'Khung giờ tạo' if 'Khung giờ tạo' in df_opr.columns else 'khung_gio_tao_don'
        slot_opr = df_opr.groupby(time_slot_col).agg({'vol_ltc': 'sum', 'ot': 'sum'}).reset_index()
        slot_opr['% OPR'] = (slot_opr['ot'] / slot_opr['vol_ltc']) * 100
        slot_opr_list = slot_opr.to_dict(orient='records')
        
        # Calculate Error Reasons (Sắp xếp theo tỷ trọng lỗi)
        reason_col = 'ly_do_tre_12h'
        errors_list = []
        total_late_reasons = 0.0
        
        if reason_col in df_opr.columns:
            df_late = df_opr[df_opr[reason_col] != '0.Ontime OPR'].copy()
            df_late = df_late.dropna(subset=[reason_col])
            
            # Late orders column
            if 'Đơn trễ' in df_late.columns:
                df_late['late_orders'] = df_late['Đơn trễ']
            else:
                df_late['late_orders'] = df_late['vol_ltc'] - df_late['ot']
                
            total_late_reasons = float(df_late['late_orders'].sum())
            
            errors = df_late.groupby(reason_col).agg({'late_orders': 'sum'}).reset_index()
            errors['weight'] = (errors['late_orders'] / total_late_reasons) * 100 if total_late_reasons > 0 else 0
            errors = errors.sort_values(by='late_orders', ascending=False)
            errors_list = errors.to_dict(orient='records')
        elif df_oe is not None and reason_col in df_oe.columns:
            # Fallback to calculating error reasons from detailed raw n-1 sheet (df_oe)
            df_late = df_oe.dropna(subset=[reason_col]).copy()
            df_late['late_orders'] = 1
            total_late_reasons = float(len(df_late))
            
            errors = df_late.groupby(reason_col).agg({'late_orders': 'sum'}).reset_index()
            errors['weight'] = (errors['late_orders'] / total_late_reasons) * 100 if total_late_reasons > 0 else 0
            errors = errors.sort_values(by='late_orders', ascending=False)
            errors_list = errors.to_dict(orient='records')
        
        # Detail N-1 error orders
        df_oe = df_oe.dropna(subset=["madh"]).copy()
        
        # Clean details
        df_oe = df_oe.where(pd.notnull(df_oe), None)
        oe_details = df_oe[['tutinh', 'kholay', 'sellername', 'khung_gio_tao_don', 'ly_do_tre_12h', 'madh', 'AM']].to_dict(orient='records')
        
        # Calculate OPR performance by AM
        am_opr = df_opr.groupby('AM').agg({'vol_ltc': 'sum', 'ot': 'sum'}).reset_index()
        am_opr['% OPR'] = (am_opr['ot'] / am_opr['vol_ltc']) * 100
        am_opr = am_opr.sort_values(by='% OPR', ascending=True).to_dict(orient='records')
        
        return {
            "overall_opr": overall_opr,
            "total_volume": int(total_vol),
            "total_ontime": int(total_ot),
            "total_late": int(total_late),
            "time_slots": slot_opr_list,
            "error_reasons": errors_list,
            "am_performance": am_opr,
            "oe_details": oe_details,
            "opr_n1": opr_n1,
            "opr_wk": opr_wk,
            "delta_n1": delta_n1,
            "delta_wk": delta_wk
        }
    except Exception as e:
        return {"error": f"Lỗi xử lý file OPR: {str(e)}"}

# ==========================================
# 3. PROCESS BACKLOG AGING
# ==========================================
def process_aging_backlog(df_raw=None, df_co_cau=None, am=None, province=None, post_office=None):
    try:
        if df_raw is None:
            df_raw = safe_read_csv(resolve_path('aging_raw.csv', write=False))
        if df_co_cau is None:
            df_co_cau = safe_read_csv(resolve_path('ops_co_cau.csv', write=False))
            
        if df_raw is None or df_co_cau is None:
            return {"error": "Không tìm thấy dữ liệu aging (aging_raw.csv hoặc ops_co_cau.csv)."}
        
        ma_don_col = next((c for c in df_raw.columns if c.lower() in ['mã đơn', 'mã đơn hàng', 'madh', 'ma don']), None)
        if ma_don_col:
            df_raw = df_raw.dropna(subset=[ma_don_col]).copy()
            df_raw['Mã đơn'] = df_raw[ma_don_col]
        else:
            df_raw['Mã đơn'] = ""

        buucuc_col = next((c for c in df_co_cau.columns if c.lower() in ['bưu cục', 'buucuc', 'bc', 'chi tiết']), None)
        if buucuc_col:
            df_co_cau = df_co_cau.dropna(subset=[buucuc_col]).copy()
            df_co_cau['bc_clean'] = df_co_cau[buucuc_col].astype(str).str.strip().str.lower()
        else:
            df_co_cau['bc_clean'] = ""

        bc_col_raw = next((c for c in df_raw.columns if c.lower() in ['bc', 'bưu cục', 'buucuc', 'chi tiết']), None)
        if bc_col_raw:
            df_raw['bc_clean'] = df_raw[bc_col_raw].astype(str).str.strip().str.lower()
            df_raw['BC'] = df_raw[bc_col_raw]
        else:
            df_raw['bc_clean'] = ""
            df_raw['BC'] = "Không rõ"

        am_col_cc = next((c for c in df_co_cau.columns if c.lower() in ['am', 'id - họ tên am', 'họ tên am']), None)
        prov_col_cc = next((c for c in df_co_cau.columns if c.lower() in ['tỉnh', 'tinh']), None)

        bc_to_am = dict(zip(df_co_cau['bc_clean'], df_co_cau[am_col_cc])) if am_col_cc else {}
        bc_to_province = dict(zip(df_co_cau['bc_clean'], df_co_cau[prov_col_cc])) if prov_col_cc else {}
        
        df_raw['mapped_am'] = df_raw['bc_clean'].map(bc_to_am)
        df_raw['mapped_province'] = df_raw['bc_clean'].map(bc_to_province)
        
        # Fallback to existing columns if map fails
        fallback_am = df_raw['am_name'] if 'am_name' in df_raw.columns else pd.Series("Không xác định", index=df_raw.index)
        df_raw['final_am'] = df_raw['mapped_am'].fillna(fallback_am).fillna("Không xác định")
        
        fallback_prov = df_raw['Tỉnh'] if 'Tỉnh' in df_raw.columns else pd.Series("Không xác định", index=df_raw.index)
        df_raw['final_province'] = df_raw['mapped_province'].fillna(fallback_prov).fillna("Không xác định")
        
        df_raw = apply_filters(df_raw, am=am, province=province, post_office=post_office)
        
        if 'Trạng thái' not in df_raw.columns:
            if 'Nhóm BL' in df_raw.columns:
                df_raw['Trạng thái'] = df_raw['Nhóm BL']
            else:
                df_raw['Trạng thái'] = "Chưa giao"
        
        # Categorize into aging brackets
        def get_aging_bracket(days):
            try:
                d = float(days)
                if d >= 5 and d < 8:
                    return "5 - 8 ngày"
                elif d >= 8 and d < 15:
                    return "8 - 15 ngày"
                elif d >= 15:
                    return "Trên 15 ngày"
            except:
                pass
            return "Khác"
            
        df_raw['aging_bracket'] = df_raw['Số ngày đã nhập BC'].apply(get_aging_bracket)
        df_raw = df_raw.where(pd.notnull(df_raw), None)
        
        # Summarize by AM and Bracket
        am_summary = df_raw.groupby(['final_am', 'aging_bracket']).size().unstack(fill_value=0).reset_index()
        # Ensure all columns exist
        for col in ["5 - 8 ngày", "8 - 15 ngày", "Trên 15 ngày"]:
            if col not in am_summary.columns:
                am_summary[col] = 0
        am_summary['Total'] = am_summary["5 - 8 ngày"] + am_summary["8 - 15 ngày"] + am_summary["Trên 15 ngày"]
        am_summary_list = am_summary.to_dict(orient='records')
        
        # Summarize by Post Office (BC)
        po_summary = df_raw.groupby(['BC', 'final_am', 'final_province', 'aging_bracket']).size().unstack(fill_value=0).reset_index()
        for col in ["5 - 8 ngày", "8 - 15 ngày", "Trên 15 ngày"]:
            if col not in po_summary.columns:
                po_summary[col] = 0
        po_summary['Total'] = po_summary["5 - 8 ngày"] + po_summary["8 - 15 ngày"] + po_summary["Trên 15 ngày"]
        po_summary_list = po_summary.to_dict(orient='records')
        
        # Raw records
        raw_records = df_raw[['final_province', 'BC', 'Mã đơn', 'Tệp khách', 'Số ngày đã nhập BC', 'Số lần giao', 'aging_bracket', 'final_am', 'Trạng thái']].to_dict(orient='records')
        
        return {
            "am_summary": am_summary_list,
            "po_summary": po_summary_list,
            "raw_records": raw_records,
            "total_backlog": len(df_raw)
        }
    except Exception as e:
        return {"error": f"Lỗi xử lý file aging backlog: {str(e)}"}

# ==========================================
# 4. PROCESS PENDING TRANSIT (TREO LUÂN CHUYỂN)
# ==========================================
def process_treo_backlog(df_raw=None, df_co_cau=None, am=None, province=None, post_office=None):
    try:
        if df_raw is None:
            df_raw = safe_read_csv(resolve_path('treo_stuck.csv', write=False))
        if df_co_cau is None:
            df_co_cau = safe_read_csv(resolve_path('ops_co_cau.csv', write=False))
            
        if df_raw is None or df_co_cau is None:
            return {"error": "Không tìm thấy dữ liệu treo luân chuyển (treo_stuck.csv hoặc ops_co_cau.csv)."}
                    
        ma_don_col = next((c for c in df_raw.columns if c.lower() in ['mã đơn hàng', 'mã đơn', 'madh', 'ma don']), None)
        if ma_don_col:
            df_raw = df_raw.dropna(subset=[ma_don_col]).copy()
            df_raw['Mã đơn hàng'] = df_raw[ma_don_col]
        else:
            df_raw['Mã đơn hàng'] = ""

        buucuc_col = next((c for c in df_co_cau.columns if c.lower() in ['bưu cục', 'buucuc', 'bc', 'chi tiết']), None)
        if buucuc_col:
            df_co_cau = df_co_cau.dropna(subset=[buucuc_col]).copy()
            df_co_cau['bc_clean'] = df_co_cau[buucuc_col].astype(str).str.strip().str.lower()
        else:
            df_co_cau['bc_clean'] = ""

        am_col_cc = next((c for c in df_co_cau.columns if c.lower() in ['am', 'id - họ tên am', 'họ tên am']), None)
        prov_col_cc = next((c for c in df_co_cau.columns if c.lower() in ['tỉnh', 'tinh']), None)

        bc_to_am = dict(zip(df_co_cau['bc_clean'], df_co_cau[am_col_cc])) if am_col_cc else {}
        bc_to_province = dict(zip(df_co_cau['bc_clean'], df_co_cau[prov_col_cc])) if prov_col_cc else {}
        
        wh_col = next((c for c in df_raw.columns if c.lower() in ['warehouse_name', 'bưu cục', 'buucuc', 'bc', 'chi tiết']), None)
        if wh_col:
            df_raw['wh_clean'] = df_raw[wh_col].astype(str).str.strip().str.lower()
        else:
            df_raw['wh_clean'] = ""
        
        df_raw['mapped_am'] = df_raw['wh_clean'].map(bc_to_am)
        df_raw['mapped_province'] = df_raw['wh_clean'].map(bc_to_province)
        
        fallback_am = df_raw['am_name'] if 'am_name' in df_raw.columns else pd.Series(np.nan, index=df_raw.index)
        fallback_prov = df_raw['province_name'] if 'province_name' in df_raw.columns else pd.Series(np.nan, index=df_raw.index)
        df_raw['final_am'] = df_raw['mapped_am'].fillna(fallback_am).fillna("Không xác định")
        df_raw['final_province'] = df_raw['mapped_province'].fillna(fallback_prov).fillna("Không xác định")
        
        df_raw = apply_filters(df_raw, am=am, province=province, post_office=post_office)
        
        if 'Thời gian tồn đọng' not in df_raw.columns:
            ton_col = next((c for c in df_raw.columns if str(c).strip().lower() in ['thời gian tồn đọng', 'thoi gian ton dong', 'ton_dong']), None)
            df_raw['Thời gian tồn đọng'] = df_raw[ton_col] if ton_col else ""
        if 'Loại đơn' not in df_raw.columns:
            loai_col = next((c for c in df_raw.columns if str(c).strip().lower() in ['loại đơn', 'loai don']), None)
            df_raw['Loại đơn'] = df_raw[loai_col] if loai_col else "Luân chuyển giao"
        if 'Trạng thái' not in df_raw.columns:
            status_col = next((c for c in df_raw.columns if str(c).strip().lower() in ['trạng thái', 'trang thai', 'status']), None)
            df_raw['Trạng thái'] = df_raw[status_col] if status_col else "Chưa đóng kiện"
        
        # Define delay brackets based on 'Thời gian tồn đọng'
        def get_treo_bracket(t):
            if not isinstance(t, str):
                return None
            t = t.strip()
            if t in ["36_48", "48_72"]:
                return "36 - 72h"
            elif t in ["72_96", "96_120"]:
                return "72 - 120h"
            elif t in ["120_192"]:
                return "120 - 192h"
            elif t in ["192", "192h+"]:
                return "192h+"
            return None

        df_raw['treo_bracket'] = df_raw['Thời gian tồn đọng'].apply(get_treo_bracket)
        df_raw = df_raw.dropna(subset=["treo_bracket"]) # Filter to delay > 36h
        
        df_raw = df_raw.where(pd.notnull(df_raw), None)
        
        # Split into Delivery (Giao) and Return (Trả)
        # Loại đơn has 'Luân chuyển giao' or 'Luân chuyển trả'
        df_giao = df_raw[df_raw['Loại đơn'] == 'Luân chuyển giao']
        df_tra = df_raw[df_raw['Loại đơn'] == 'Luân chuyển trả']
        
        # Helper to summarize df
        def get_summary_data(df_sub):
            if len(df_sub) == 0:
                return [], []
            
            # AM Summary
            am_sum = df_sub.groupby(['final_am', 'treo_bracket']).size().unstack(fill_value=0).reset_index()
            for col in ["36 - 72h", "72 - 120h", "120 - 192h", "192h+"]:
                if col not in am_sum.columns:
                    am_sum[col] = 0
            am_sum['Total'] = am_sum["36 - 72h"] + am_sum["72 - 120h"] + am_sum["120 - 192h"] + am_sum["192h+"]
            
            # PO Summary
            po_sum = df_sub.groupby(['warehouse_name', 'final_am', 'final_province', 'treo_bracket']).size().unstack(fill_value=0).reset_index()
            for col in ["36 - 72h", "72 - 120h", "120 - 192h", "192h+"]:
                if col not in po_sum.columns:
                    po_sum[col] = 0
            po_sum['Total'] = po_sum["36 - 72h"] + po_sum["72 - 120h"] + po_sum["120 - 192h"] + po_sum["192h+"]
            
            return am_sum.to_dict(orient='records'), po_sum.to_dict(orient='records')

        giao_am_sum, giao_po_sum = get_summary_data(df_giao)
        tra_am_sum, tra_po_sum = get_summary_data(df_tra)
        
        raw_records = df_raw[['final_province', 'warehouse_name', 'Mã đơn hàng', 'Loại đơn', 'Thời gian tồn đọng', 'treo_bracket', 'final_am', 'Trạng thái']].to_dict(orient='records')
        
        return {
            "giao_am_summary": giao_am_sum,
            "giao_po_summary": giao_po_sum,
            "tra_am_summary": tra_am_sum,
            "tra_po_summary": tra_po_sum,
            "raw_records": raw_records,
            "total_backlog": len(df_raw),
            "total_giao": len(df_giao),
            "total_tra": len(df_tra)
        }
    except Exception as e:
        return {"error": f"Lỗi xử lý file treo luân chuyển: {str(e)}"}

# Helper: Universal Raw Tren10kg Splitter (Handles headerless CSVs & named DB DataFrames)
def split_raw_tren10kg_df(df_raw):
    if df_raw is None or len(df_raw) == 0:
        return None, None
    df_raw = df_raw.copy()
    is_headerless = any(isinstance(c, int) for c in df_raw.columns) or all(str(c).isdigit() for c in df_raw.columns)
    if is_headerless:
        header_row = 0
        for r_idx in range(min(5, len(df_raw))):
            row_vals = [str(v).lower() for v in df_raw.iloc[r_idx] if pd.notnull(v)]
            if any('cấp quản lý' in v or 'chi tiết' in v or 'loại hàng' in v or 'hen_lay' in v for v in row_vals):
                header_row = r_idx
                break
        df_ops = df_raw.iloc[header_row:].copy()
        if df_ops.shape[1] >= 21:
            df_ops = df_ops.iloc[:, 0:21]
            df_ops.columns = [str(c).strip() for c in df_ops.iloc[0]]
            df_ops = df_ops.iloc[1:].dropna(how='all')
        else:
            df_ops = pd.DataFrame()

        if df_raw.shape[1] >= 30:
            df_tao = df_raw.iloc[header_row:].copy()
            df_tao = df_tao.iloc[:, 22:30]
            df_tao.columns = [str(c).strip() for c in df_tao.iloc[0]]
            df_tao = df_tao.iloc[1:].dropna(how='all')
        else:
            df_tao = pd.DataFrame()
    else:
        cols_lower = [str(c).strip().lower() for c in df_raw.columns]
        has_creation_cols = any(k in cols_lower for k in ['hen_lay', 'deliverywarehouseid', 'nhom_kh', 'nhom_kg', 'vol', 'kl_kg'])
        if df_raw.shape[1] >= 30:
            df_ops = df_raw.iloc[:, 0:21].copy()
            df_ops.columns = [str(c).strip() for c in df_ops.columns]
            df_tao = df_raw.iloc[:, 22:30].copy()
            df_tao.columns = [str(c).strip() for c in df_tao.columns]
        elif has_creation_cols:
            df_ops = pd.DataFrame()
            df_tao = df_raw.copy()
            df_tao.columns = [str(c).strip() for c in df_tao.columns]
        else:
            df_ops = df_raw.copy()
            df_ops.columns = [str(c).strip() for c in df_ops.columns]
            df_tao = pd.DataFrame()
    return df_ops, df_tao

def split_raw_tren10kg():
    try:
        raw_path = resolve_path('raw_tren10kg.csv', write=False)
        df_raw = safe_read_csv(raw_path, header=None)
        if df_raw is None or len(df_raw) == 0:
            df_raw = load_df_from_db('raw_tren10kg.csv')
            
        df_ops, df_tao = split_raw_tren10kg_df(df_raw)
        
        if df_ops is not None and len(df_ops) > 0:
            try:
                df_ops.to_csv(resolve_path('ops_heavy_10kg.csv', write=True), index=False, encoding='utf-8-sig')
            except Exception:
                pass
            save_df_to_db(df_ops, 'ops_heavy_10kg.csv')

        if df_tao is not None and len(df_tao) > 0:
            try:
                df_tao.to_csv(resolve_path('ops_tao_don_10kg.csv', write=True), index=False, encoding='utf-8-sig')
            except Exception:
                pass
            save_df_to_db(df_tao, 'ops_tao_don_10kg.csv')
            
        print("[Heavy 10kg] Successfully split raw_tren10kg into ops_heavy_10kg and ops_tao_don_10kg")
    except Exception as e:
        print(f"[Heavy 10kg] Error splitting raw_tren10kg: {e}")

# ==========================================
# 4b. PROCESS HEAVY GOODS > 10KG REPORT & SURGE ANOMALY ENGINE
# ==========================================
def is_ck_po(name):
    if not name or pd.isna(name):
        return False
    s = str(name).strip().lower()
    return bool(re.search(r'(^|\s|\(|\/|-)ck(\s|\)|\/|-|$)|bcck|cồng kềnh|cong kenh', s))

def process_heavy_10kg_report(am=None, province=None, post_office=None, date=None, ck_only=False, spike_level=None):
    try:
        heavy_ops_path = resolve_path('ops_heavy_10kg.csv', write=False)
        heavy_tao_path = resolve_path('ops_tao_don_10kg.csv', write=False)

        df_ops = safe_read_csv(heavy_ops_path)
        df_tao = safe_read_csv(heavy_tao_path)

        # Fallback: if df_ops or df_tao is empty, attempt to read raw_tren10kg.csv directly
        if (df_ops is None or len(df_ops) == 0) or (df_tao is None or len(df_tao) == 0):
            df_raw = safe_read_csv(resolve_path('raw_tren10kg.csv', write=False), header=None)
            if df_raw is None or len(df_raw) == 0:
                df_raw = load_df_from_db('raw_tren10kg.csv')
            
            fb_ops, fb_tao = split_raw_tren10kg_df(df_raw)
            if (df_ops is None or len(df_ops) == 0) and fb_ops is not None:
                df_ops = fb_ops
            if (df_tao is None or len(df_tao) == 0) and fb_tao is not None:
                df_tao = fb_tao

        if df_ops is None or len(df_ops) == 0:
            df_ops = pd.DataFrame()
        if df_tao is None or len(df_tao) == 0:
            df_tao = pd.DataFrame()

        df_co_cau = DF_CO_CAU_CACHE if DF_CO_CAU_CACHE is not None else safe_read_csv(resolve_path('ops_co_cau.csv', write=False))
        bc_to_prov = {}
        bc_to_am = {}
        if df_co_cau is not None and len(df_co_cau) > 0:
            buucuc_col = next((c for c in df_co_cau.columns if c.lower() in ['bưu cục', 'buucuc', 'bc', 'chi tiết']), None)
            prov_col_cc = next((c for c in df_co_cau.columns if c.lower() in ['tỉnh', 'tinh']), None)
            am_col_cc = next((c for c in df_co_cau.columns if c.lower() in ['am', 'id - họ tên am', 'họ tên am']), None)
            if buucuc_col:
                df_co_cau['bc_clean'] = df_co_cau[buucuc_col].astype(str).str.strip().str.lower()
                if prov_col_cc:
                    bc_to_prov = dict(zip(df_co_cau['bc_clean'], df_co_cau[prov_col_cc]))
                if am_col_cc:
                    bc_to_am = dict(zip(df_co_cau['bc_clean'], df_co_cau[am_col_cc]))

        # Phase 1: Process Operational Data (SL > 10kg)
        if len(df_ops) > 0:
            df_ops.columns = [str(c).strip() for c in df_ops.columns]
            vol_col = next((c for c in df_ops.columns if c.lower() == 'volume'), None)
            df_ops['Volume'] = safe_to_numeric(df_ops[vol_col]) if vol_col else 0.0
            
            gtc_col = next((c for c in df_ops.columns if c.lower() in ['% gtc', '%gtc']), None)
            df_ops['% GTC'] = normalize_pct_col(df_ops[gtc_col]) if gtc_col else 0.0
            
            gan_col = next((c for c in df_ops.columns if c.lower() in ['% gán', '%gán']), None)
            df_ops['% Gán'] = normalize_pct_col(df_ops[gan_col]) if gan_col else 0.0

            leadtime_col = next((c for c in df_ops.columns if c.lower() in ['leadtime', 'lead time']), None)
            df_ops['Leadtime'] = safe_to_numeric(df_ops[leadtime_col]) if leadtime_col else 0.0

            deliv_col = next((c for c in df_ops.columns if c.lower() in ['sản lượng giao thành công', 'san luong giao thanh cong']), None)
            if deliv_col:
                df_ops['delivered_vol'] = safe_to_numeric(df_ops[deliv_col])
            else:
                df_ops['delivered_vol'] = df_ops['Volume'] * (df_ops['% GTC'] / 100.0)

            new_in_day_col = next((c for c in df_ops.columns if c.lower() in ['hàng mới về trong ngày', 'hang moi ve trong ngay', 'hàng mới về', 'hang moi ve']), None)
            df_ops['Hàng Mới Về Trong Ngày'] = safe_to_numeric(df_ops[new_in_day_col]) if new_in_day_col else 0.0

            ton_col = next((c for c in df_ops.columns if c.lower() in ['sản lượng tồn', 'san luong ton', 'tồn', 'ton']), None)
            df_ops['Sản Lượng Tồn'] = safe_to_numeric(df_ops[ton_col]) if ton_col else 0.0

            chi_tiet_col = next((c for c in df_ops.columns if c.lower() in ['chi tiết', 'chitiết', 'bưu cục', 'buucuc', 'bc']), None)
            if chi_tiet_col:
                df_ops['po_name'] = df_ops[chi_tiet_col].fillna('Không xác định').astype(str).str.strip()
            else:
                df_ops['po_name'] = "Không xác định"

            df_ops['clean_bc'] = df_ops['po_name'].apply(clean_str)
            prov_col = next((df_ops[c] for c in df_ops.columns if c.lower() in ['tỉnh', 'tinh']), pd.Series("Không xác định", index=df_ops.index))
            am_col = next((df_ops[c] for c in df_ops.columns if c.lower() in ['am', 'am_name']), pd.Series("Không xác định", index=df_ops.index))

            df_ops['mapped_prov'] = df_ops['clean_bc'].map(bc_to_prov).replace({'': np.nan, 'none': np.nan, 'nan': np.nan}).fillna(prov_col).fillna("Không xác định")
            df_ops['mapped_am'] = df_ops['clean_bc'].map(bc_to_am).replace({'': np.nan, 'none': np.nan, 'nan': np.nan}).fillna(am_col).fillna("Không xác định")

            time_col = next((c for c in df_ops.columns if c.lower() in ['time', 'thời gian', 'ngày']), None)
            if time_col:
                df_ops['date'] = df_ops[time_col].astype(str).apply(lambda x: x.split(' - ')[0].strip() if ' - ' in str(x) else str(x).strip())
            else:
                df_ops['date'] = "Chưa xác định"

            df_ops['is_ck'] = df_ops['po_name'].apply(is_ck_po)

        # Phase 2: Process Order Creation Data (trên10kg / treen10kg)
        if len(df_tao) > 0:
            df_tao.columns = [str(c).strip() for c in df_tao.columns]
            v_col = next((c for c in df_tao.columns if c.lower() in ['so_don', 'số đơn', 'vol', 'volume', 'sản lượng']), None)
            k_col = next((c for c in df_tao.columns if c.lower() in ['kl_kg', 'khối lượng', 'khoi_luong']), None)
            w_col = next((c for c in df_tao.columns if c.lower() in ['warehouse_name', 'bưu cục', 'buucuc', 'bc', 'chi tiết']), None)
            d_col = next((c for c in df_tao.columns if c.lower() in ['ngay_tao_don', 'ngày tạo đơn', 'hen_lay', 'time', 'ngày']), None)

            df_tao['vol'] = safe_to_numeric(df_tao[v_col]) if v_col else 0.0
            df_tao['kl_kg'] = safe_to_numeric(df_tao[k_col]) if k_col else 0.0
            df_tao['po_name'] = df_tao[w_col].fillna('Không xác định').astype(str).str.strip() if w_col else "Không xác định"
            df_tao['date'] = df_tao[d_col].astype(str).str.strip() if d_col else "Chưa xác định"
            df_tao['clean_bc'] = df_tao['po_name'].apply(clean_str)

            prov_col_t = next((df_tao[c] for c in df_tao.columns if c.lower() in ['province_name', 'tỉnh', 'tinh']), pd.Series("Không xác định", index=df_tao.index))
            am_col_t = next((df_tao[c] for c in df_tao.columns if c.lower() in ['am', 'am_name']), pd.Series("Không xác định", index=df_tao.index))

            df_tao['mapped_prov'] = df_tao['clean_bc'].map(bc_to_prov).replace({'': np.nan, 'none': np.nan, 'nan': np.nan}).fillna(prov_col_t).fillna("Không xác định")
            df_tao['mapped_am'] = df_tao['clean_bc'].map(bc_to_am).replace({'': np.nan, 'none': np.nan, 'nan': np.nan}).fillna(am_col_t).fillna("Không xác định")
            df_tao['is_ck'] = df_tao['po_name'].apply(is_ck_po)

        # Build list of available dates (combine dates from both operational and creation data)
        ops_dates = set([str(d) for d in df_ops['date'].unique() if re.match(r'^\d{4}-\d{2}-\d{2}$', str(d))]) if (len(df_ops) > 0 and 'date' in df_ops.columns) else set()
        tao_dates = set([str(d) for d in df_tao['date'].unique() if re.match(r'^\d{4}-\d{2}-\d{2}$', str(d))]) if (len(df_tao) > 0 and 'date' in df_tao.columns) else set()
        all_dates = sorted(list(ops_dates.union(tao_dates)))

        selected_date = date if (date and date in all_dates) else (all_dates[-1] if all_dates else None)
        prev_dates = [d for d in all_dates if d < selected_date][-7:] if selected_date else []

        # Unique PO list before user filtering (for dropdown)
        po_list = []
        if len(df_ops) > 0:
            po_list = sorted([str(p) for p in df_ops['po_name'].dropna().unique() if str(p) not in ['Grand Total', 'nan', 'none', 'Không xác định']])

        # Apply Filters (CK only, AM, Province, Post Office)
        is_ck_bool = str(ck_only).lower() in ['true', '1', 'yes']
        if is_ck_bool:
            if len(df_ops) > 0: df_ops = df_ops[df_ops['is_ck'] == True]
            if len(df_tao) > 0: df_tao = df_tao[df_tao['is_ck'] == True]

        if am and am not in ['all', '']:
            if len(df_ops) > 0: df_ops = df_ops[df_ops['mapped_am'] == am]
            if len(df_tao) > 0: df_tao = df_tao[df_tao['mapped_am'] == am]

        if province and province not in ['all', '']:
            if len(df_ops) > 0: df_ops = df_ops[df_ops['mapped_prov'] == province]
            if len(df_tao) > 0: df_tao = df_tao[df_tao['mapped_prov'] == province]

        if post_office and post_office not in ['all', '']:
            if len(df_ops) > 0: df_ops = df_ops[df_ops['po_name'] == post_office]
            if len(df_tao) > 0: df_tao = df_tao[df_tao['po_name'] == post_office]

        # Slices for selected date
        ops_sel = df_ops[df_ops['date'] == selected_date] if (len(df_ops) > 0 and selected_date) else df_ops
        tao_sel = df_tao[df_tao['date'] == selected_date] if (len(df_tao) > 0 and selected_date) else df_tao

        # 1. Overall Aggregates for Selected Date
        total_ops_vol = float(ops_sel['Volume'].sum()) if len(ops_sel) > 0 else 0.0
        total_delivered = float(ops_sel['delivered_vol'].sum()) if len(ops_sel) > 0 else 0.0
        total_incoming = float(ops_sel['Hàng Mới Về Trong Ngày'].sum()) if len(ops_sel) > 0 else 0.0
        total_ton = float(ops_sel['Sản Lượng Tồn'].sum()) if len(ops_sel) > 0 else 0.0
        overall_gtc = round((total_delivered / total_ops_vol * 100), 2) if total_ops_vol > 0 else 0.0

        valid_lt = ops_sel[ops_sel['Leadtime'] > 0]['Leadtime'] if len(ops_sel) > 0 else []
        avg_leadtime = round(float(valid_lt.mean()), 2) if len(valid_lt) > 0 else 0.0

        total_created_vol = float(tao_sel['vol'].sum()) if len(tao_sel) > 0 else 0.0
        total_created_weight_kg = float(tao_sel['kl_kg'].sum()) if len(tao_sel) > 0 else 0.0
        total_created_weight_ton = round(total_created_weight_kg / 1000.0, 2)

        # Baseline volume comparison for total volume
        ops_prev = df_ops[df_ops['date'].isin(prev_dates)] if len(df_ops) > 0 else pd.DataFrame()
        baseline_daily_vol = float(ops_prev['Volume'].sum() / max(len(prev_dates), 1)) if len(ops_prev) > 0 else total_ops_vol
        vol_growth_pct = round(((total_ops_vol - baseline_daily_vol) / max(baseline_daily_vol, 1)) * 100, 1)

        # Baseline created volume comparison for total created volume
        tao_prev_all = df_tao[df_tao['date'].isin(prev_dates)] if len(df_tao) > 0 else pd.DataFrame()
        baseline_created_vol = float(tao_prev_all['vol'].sum() / max(len(prev_dates), 1)) if len(tao_prev_all) > 0 else total_created_vol
        created_growth_total_pct = round(((total_created_vol - baseline_created_vol) / max(baseline_created_vol, 1)) * 100, 1)

        # 2. BCCK Spotlight (Các Bưu Cục Cồng Kềnh CK)
        ck_ops_sel = ops_sel[ops_sel['is_ck'] == True] if len(ops_sel) > 0 else pd.DataFrame()
        ck_tao_sel = tao_sel[tao_sel['is_ck'] == True] if len(tao_sel) > 0 else pd.DataFrame()
        ck_total_ops_vol = float(ck_ops_sel['Volume'].sum()) if len(ck_ops_sel) > 0 else 0.0
        ck_total_delivered = float(ck_ops_sel['delivered_vol'].sum()) if len(ck_ops_sel) > 0 else 0.0
        ck_total_created = float(ck_tao_sel['vol'].sum()) if len(ck_tao_sel) > 0 else 0.0
        ck_gtc = round((ck_total_delivered / ck_total_ops_vol * 100), 2) if ck_total_ops_vol > 0 else 0.0
        ck_share_pct = round((ck_total_ops_vol / total_ops_vol * 100), 1) if total_ops_vol > 0 else 0.0

        # 3. PO Summary & Surge Anomaly Analysis
        po_ops_summary = []
        critical_count = 0
        high_count = 0
        warning_count = 0
        created_critical_count = 0
        created_high_count = 0
        created_warning_count = 0

        if len(ops_sel) > 0:
            po_ops = ops_sel.groupby(['po_name', 'mapped_prov', 'mapped_am', 'is_ck']).agg({
                'Volume': 'sum',
                'delivered_vol': 'sum',
                'Hàng Mới Về Trong Ngày': 'sum',
                'Sản Lượng Tồn': 'sum',
                'Leadtime': 'mean'
            }).reset_index().rename(columns={'Volume': 'vol_actual', 'delivered_vol': 'delivered_actual'})

            # Baseline 7 days average per PO in df_ops
            po_ops_prev = ops_prev.groupby('po_name')['Volume'].mean().reset_index().rename(columns={'Volume': 'vol_avg_prev'}) if len(ops_prev) > 0 else pd.DataFrame(columns=['po_name', 'vol_avg_prev'])
            
            # Created orders for selected date and baseline
            po_tao_cur = tao_sel.groupby('po_name')['vol'].sum().reset_index().rename(columns={'vol': 'vol_created'}) if len(tao_sel) > 0 else pd.DataFrame(columns=['po_name', 'vol_created'])
            tao_prev = df_tao[df_tao['date'].isin(prev_dates)] if len(df_tao) > 0 else pd.DataFrame()
            po_tao_prev = tao_prev.groupby('po_name')['vol'].mean().reset_index().rename(columns={'vol': 'vol_created_avg_prev'}) if len(tao_prev) > 0 else pd.DataFrame(columns=['po_name', 'vol_created_avg_prev'])

            po_merged = pd.merge(po_ops, po_ops_prev, on='po_name', how='left')
            po_merged = pd.merge(po_merged, po_tao_cur, on='po_name', how='left')
            po_merged = pd.merge(po_merged, po_tao_prev, on='po_name', how='left')
            po_merged = po_merged.fillna({'vol_avg_prev': 0.0, 'vol_created': 0.0, 'vol_created_avg_prev': 0.0})

            po_merged['vol_diff'] = (po_merged['vol_actual'] - po_merged['vol_avg_prev']).round(1)
            po_merged['growth_pct'] = np.where(
                po_merged['vol_avg_prev'] > 0,
                ((po_merged['vol_actual'] - po_merged['vol_avg_prev']) / po_merged['vol_avg_prev'] * 100).round(1),
                np.where(po_merged['vol_actual'] > 0, 100.0, 0.0)
            )

            po_merged['created_diff'] = (po_merged['vol_created'] - po_merged['vol_created_avg_prev']).round(1)
            po_merged['created_growth_pct'] = np.where(
                po_merged['vol_created_avg_prev'] > 0,
                ((po_merged['vol_created'] - po_merged['vol_created_avg_prev']) / po_merged['vol_created_avg_prev'] * 100).round(1),
                np.where(po_merged['vol_created'] > 0, 100.0, 0.0)
            )

            po_merged['gtc_pct'] = np.where(
                po_merged['vol_actual'] > 0,
                (po_merged['delivered_actual'] / po_merged['vol_actual'] * 100).round(1),
                0.0
            )
            po_merged['Leadtime'] = po_merged['Leadtime'].round(1).fillna(0.0)

            def classify_actual_spike(r):
                g = r['growth_pct']
                d = r['vol_diff']
                if g >= 100 and d >= 15:
                    return 'CRITICAL', '🔴 Đột biến cực đại (+{:.0f}%)'.format(g)
                elif (g >= 50 and d >= 10) or g >= 80:
                    return 'HIGH', '🟠 Đột biến cao (+{:.0f}%)'.format(g)
                elif g >= 25 and d >= 5:
                    return 'WARNING', '🟡 Tăng nhanh (+{:.0f}%)'.format(g)
                elif g <= -30:
                    return 'DOWN', '📉 Giảm mạnh ({:.0f}%)'.format(g)
                else:
                    return 'NORMAL', '🟢 Bình thường'

            def classify_created_spike(r):
                g = r['created_growth_pct']
                d = r['created_diff']
                if g >= 100 and d >= 15:
                    return 'CRITICAL', '🔴 Tạo cực đại (+{:.0f}%)'.format(g)
                elif (g >= 50 and d >= 10) or g >= 80:
                    return 'HIGH', '🟠 Tạo tăng cao (+{:.0f}%)'.format(g)
                elif g >= 25 and d >= 5:
                    return 'WARNING', '🟡 Tạo tăng (+{:.0f}%)'.format(g)
                elif g <= -30:
                    return 'DOWN', '📉 Giảm tạo ({:.0f}%)'.format(g)
                else:
                    return 'NORMAL', '🟢 Bình thường'

            po_merged['spike_level'], po_merged['spike_label'] = zip(*po_merged.apply(classify_actual_spike, axis=1))
            po_merged['spike_created_level'], po_merged['spike_created_label'] = zip(*po_merged.apply(classify_created_spike, axis=1))

            critical_count = int((po_merged['spike_level'] == 'CRITICAL').sum())
            high_count = int((po_merged['spike_level'] == 'HIGH').sum())
            warning_count = int((po_merged['spike_level'] == 'WARNING').sum())

            created_critical_count = int((po_merged['spike_created_level'] == 'CRITICAL').sum())
            created_high_count = int((po_merged['spike_created_level'] == 'HIGH').sum())
            created_warning_count = int((po_merged['spike_created_level'] == 'WARNING').sum())

            # Filter spike_level if specified
            if spike_level and spike_level != 'all':
                if spike_level == 'surge':
                    po_merged = po_merged[po_merged['spike_level'].isin(['CRITICAL', 'HIGH']) | po_merged['spike_created_level'].isin(['CRITICAL', 'HIGH'])]
                elif spike_level == 'actual_surge':
                    po_merged = po_merged[po_merged['spike_level'].isin(['CRITICAL', 'HIGH'])]
                elif spike_level == 'created_surge':
                    po_merged = po_merged[po_merged['spike_created_level'].isin(['CRITICAL', 'HIGH'])]
                else:
                    po_merged = po_merged[(po_merged['spike_level'] == spike_level.upper()) | (po_merged['spike_created_level'] == spike_level.upper())]

            po_merged = po_merged.sort_values(by='vol_actual', ascending=False)
            po_ops_summary = po_merged.to_dict(orient='records')

        total_surge_pos = critical_count + high_count
        total_created_surge_pos = created_critical_count + created_high_count

        # 4. Dual-Track Daily Trends (Created vs Actual Delivery)
        daily_trend = []
        daily_trend_ck = []
        daily_trend_by_po = {}
        if len(df_ops) > 0 or len(df_tao) > 0:
            daily_ops = df_ops.groupby('date').agg({'Volume': 'sum', 'delivered_vol': 'sum'}).reset_index() if len(df_ops) > 0 else pd.DataFrame(columns=['date', 'Volume', 'delivered_vol'])
            if len(daily_ops) > 0:
                daily_ops['gtc_pct'] = np.where(daily_ops['Volume'] > 0, (daily_ops['delivered_vol'] / daily_ops['Volume'] * 100).round(1), 0.0)

            daily_tao = df_tao.groupby('date')['vol'].sum().reset_index().rename(columns={'vol': 'vol_created'}) if len(df_tao) > 0 else pd.DataFrame(columns=['date', 'vol_created'])

            daily_m = pd.merge(daily_ops, daily_tao, on='date', how='outer').sort_values(by='date').fillna(0)
            daily_trend = daily_m.to_dict(orient='records')

            # Daily trend specifically for all CK post offices
            ops_ck = df_ops[df_ops['is_ck'] == True] if len(df_ops) > 0 else pd.DataFrame()
            tao_ck = df_tao[df_tao['is_ck'] == True] if len(df_tao) > 0 else pd.DataFrame()
            if len(ops_ck) > 0 or len(tao_ck) > 0:
                d_ops_ck = ops_ck.groupby('date').agg({'Volume': 'sum', 'delivered_vol': 'sum'}).reset_index() if len(ops_ck) > 0 else pd.DataFrame(columns=['date', 'Volume', 'delivered_vol'])
                if len(d_ops_ck) > 0:
                    d_ops_ck['gtc_pct'] = np.where(d_ops_ck['Volume'] > 0, (d_ops_ck['delivered_vol'] / d_ops_ck['Volume'] * 100).round(1), 0.0)
                d_tao_ck = tao_ck.groupby('date')['vol'].sum().reset_index().rename(columns={'vol': 'vol_created'}) if len(tao_ck) > 0 else pd.DataFrame(columns=['date', 'vol_created'])
                d_m_ck = pd.merge(d_ops_ck, d_tao_ck, on='date', how='outer').sort_values(by='date').fillna(0)
                daily_trend_ck = d_m_ck.to_dict(orient='records')

            # Daily trend grouped by PO
            all_po_names = set(df_ops['po_name'].dropna().unique()) | set(df_tao['po_name'].dropna().unique())
            for po_item in all_po_names:
                p_ops = df_ops[df_ops['po_name'] == po_item] if len(df_ops) > 0 else pd.DataFrame()
                p_tao = df_tao[df_tao['po_name'] == po_item] if len(df_tao) > 0 else pd.DataFrame()
                if len(p_ops) > 0 or len(p_tao) > 0:
                    dp_ops = p_ops.groupby('date').agg({'Volume': 'sum', 'delivered_vol': 'sum'}).reset_index() if len(p_ops) > 0 else pd.DataFrame(columns=['date', 'Volume', 'delivered_vol'])
                    if len(dp_ops) > 0:
                        dp_ops['gtc_pct'] = np.where(dp_ops['Volume'] > 0, (dp_ops['delivered_vol'] / dp_ops['Volume'] * 100).round(1), 0.0)
                    dp_tao = p_tao.groupby('date')['vol'].sum().reset_index().rename(columns={'vol': 'vol_created'}) if len(p_tao) > 0 else pd.DataFrame(columns=['date', 'vol_created'])
                    dp_m = pd.merge(dp_ops, dp_tao, on='date', how='outer').sort_values(by='date').fillna(0)
                    daily_trend_by_po[str(po_item)] = dp_m.to_dict(orient='records')

        # 5. Weight Brackets Breakdown (from df_tao)
        weight_bracket_summary = []
        pct_heavy_30kg = 0.0
        kg_col_name = next((c for c in tao_sel.columns if c.lower() in ['nhom_kl', 'nhom_kg', 'nhóm kg']), None) if len(tao_sel) > 0 else None
        if kg_col_name and len(tao_sel) > 0:
            w_grp = tao_sel.groupby(kg_col_name)['vol'].sum().reset_index()
            w_grp['pct'] = np.where(total_created_vol > 0, (w_grp['vol'] / total_created_vol * 100).round(1), 0.0)
            weight_bracket_summary = w_grp.to_dict(orient='records')
            
            over_30 = float(w_grp[w_grp[kg_col_name].astype(str).str.contains('>30|30|50|>50', case=False)]['vol'].sum())
            pct_heavy_30kg = round((over_30 / total_created_vol * 100), 1) if total_created_vol > 0 else 0.0

        # 6. Customer Groups Breakdown (from df_tao)
        customer_group_summary = []
        kh_col_name = next((c for c in tao_sel.columns if c.lower() in ['nhom_kh', 'nhóm kh']), None) if len(tao_sel) > 0 else None
        if kh_col_name and len(tao_sel) > 0:
            c_grp = tao_sel.groupby(kh_col_name)['vol'].sum().reset_index()
            c_grp['pct'] = np.where(total_created_vol > 0, (c_grp['vol'] / total_created_vol * 100).round(1), 0.0)
            customer_group_summary = c_grp.to_dict(orient='records')

        # 7. Top Spike POs for Actual vs Created
        top_spikes = []
        top_spikes_created = []
        if po_ops_summary:
            valid_spikes_act = [r for r in po_ops_summary if r.get('vol_actual', 0) >= 10]
            top_spikes = sorted(valid_spikes_act, key=lambda x: x.get('growth_pct', 0), reverse=True)[:10]

            valid_spikes_cre = [r for r in po_ops_summary if r.get('vol_created', 0) >= 10]
            top_spikes_created = sorted(valid_spikes_cre, key=lambda x: x.get('created_growth_pct', 0), reverse=True)[:10]

        # 8. Top & Worst % GTC POs
        top_pos = []
        worst_pos = []
        if po_ops_summary:
            valid_gtc = [r for r in po_ops_summary if r.get('vol_actual', 0) >= 10]
            top_pos = sorted(valid_gtc, key=lambda x: x.get('gtc_pct', 0), reverse=True)[:5]
            worst_pos = sorted(valid_gtc, key=lambda x: x.get('gtc_pct', 0))[:5]

        # CK PO list for spotlight table
        ck_pos_records = [r for r in po_ops_summary if r.get('is_ck')]

        return {
            "selected_date": selected_date,
            "available_dates": all_dates,
            "total_ops_vol": total_ops_vol,
            "total_created_vol": total_created_vol,
            "total_incoming_vol": total_incoming,
            "total_ton_vol": total_ton,
            "overall_gtc": overall_gtc,
            "avg_leadtime": avg_leadtime,
            "vol_growth_pct": vol_growth_pct,
            "baseline_daily_vol": round(baseline_daily_vol, 1),
            "baseline_created_vol": round(baseline_created_vol, 1),
            "created_growth_total_pct": created_growth_total_pct,
            "pct_heavy_30kg": pct_heavy_30kg,
            "critical_count": critical_count,
            "high_count": high_count,
            "warning_count": warning_count,
            "created_critical_count": created_critical_count,
            "created_high_count": created_high_count,
            "created_warning_count": created_warning_count,
            "total_surge_pos": total_surge_pos,
            "total_created_surge_pos": total_created_surge_pos,
            "bcck_spotlight": {
                "ck_total_ops_vol": ck_total_ops_vol,
                "ck_total_created": ck_total_created,
                "ck_gtc": ck_gtc,
                "ck_share_pct": ck_share_pct,
                "ck_pos_count": len(ck_pos_records),
                "ck_pos": ck_pos_records
            },
            "weight_bracket_summary": weight_bracket_summary,
            "customer_group_summary": customer_group_summary,
            "po_ops_summary": po_ops_summary,
            "daily_trend": daily_trend,
            "daily_trend_ck": daily_trend_ck,
            "daily_trend_by_po": daily_trend_by_po,
            "top_spikes": top_spikes,
            "top_spikes_created": top_spikes_created,
            "top_pos": top_pos,
            "worst_pos": worst_pos,
            "po_list": po_list
        }
    except Exception as e:
        return {"error": f"Lỗi xử lý báo cáo hàng nặng >10kg: {str(e)}"}


# ==========================================
# 4c. PROCESS UNSTABLE POST OFFICES
# ==========================================
def clean_po_name(name):
    if not name:
        return ""
    name = str(name).lower().strip()
    prefixes = ["bưu cục ", "kho giao hàng ", "kho giao ", "kho hàng ", "điểm xử lý ", "giao hàng nhanh ", "ghn "]
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
    replacements = {
        "khánh hoà": "khánh hòa",
        "đắc nông": "đắk nông",
        "bình phước": "lâm đồng",
        "-": " ",
        ".": " ",
        ",": " "
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    name = " ".join(name.split())
    return name

def map_po_to_am_prov(po_id, po_name, id_to_am, id_to_prov, name_to_am, name_to_prov, default_am="Không xác định", default_prov="Không xác định"):
    def clean_val(val, default):
        if pd.isna(val) or not str(val).strip() or str(val).lower() == 'nan':
            return default
        return str(val).strip()
    
    default_am = clean_val(default_am, "Không xác định")
    default_prov = clean_val(default_prov, "Không xác định")

    try:
        pid = int(float(po_id))
        if pid in id_to_am:
            return clean_val(id_to_am[pid], default_am), clean_val(id_to_prov[pid], default_prov)
    except:
        pass

    name_clean = clean_po_name(po_name)
    if name_clean in name_to_am:
        return clean_val(name_to_am[name_clean], default_am), clean_val(name_to_prov[name_clean], default_prov)

    for k in name_to_am:
        if k in name_clean or name_clean in k:
            return clean_val(name_to_am[k], default_am), clean_val(name_to_prov[k], default_prov)

    return default_am, default_prov

def process_unstable_po(am=None, province=None, post_office=None):
    file_path = resolve_path('buu_cuc_bat_on.csv', write=False)
    try:
        df_raw = safe_read_csv(file_path, header=None)
        if df_raw is None or df_raw.empty:
            return {"error": "Không tìm thấy dữ liệu bưu cục bất ổn (buu_cuc_bat_on.csv)."}
            
        update_time = None
        total_warning = None
        
        # Search metadata in the first 10 rows
        for r_idx in range(min(10, len(df_raw))):
            for c_idx in range(len(df_raw.columns)):
                cell_val = str(df_raw.iloc[r_idx, c_idx])
                if "Thời gian cập nhật" in cell_val:
                    update_time = cell_val.split("Thời gian cập nhật")[-1].strip()
                    if not update_time and c_idx + 1 < len(df_raw.columns):
                        update_time = str(df_raw.iloc[r_idx, c_idx + 1]).strip()
                elif "Tổng số lượng BC cảnh báo" in cell_val or "bưu cục cảnh báo" in cell_val:
                    if r_idx + 1 < len(df_raw):
                        val = str(df_raw.iloc[r_idx + 1, c_idx]).strip()
                        if val.isdigit():
                            total_warning = int(val)
        
        # Find the table headers row
        header_row_idx = None
        for r_idx in range(len(df_raw)):
            row_vals = [str(x).lower().strip() for x in df_raw.iloc[r_idx].values]
            if any("tổng số lượng" in x or "thời gian cập nhật" in x for x in row_vals):
                continue
            if any(x in ["vùng", "tỉnh", "bưu cục", "chi tiết", "tên bc", "id bưu cục"] or "tên bưu cục" in x or "kho_giao_id" in x for x in row_vals):
                header_row_idx = r_idx
                break
                
        if header_row_idx is None:
            header_row_idx = 4 if len(df_raw) > 4 else 0
            
        # Load table with header line
        df_table = safe_read_csv(file_path, skiprows=header_row_idx)
        if df_table is None:
            return {"error": "Lỗi đọc bảng bưu cục bất ổn."}
        df_table.columns = [str(c).replace('\n', ' ').strip() for c in df_table.columns]
        
        id_col = next((c for c in df_table.columns if "id bưu cục" in c.lower() or "kho_giao_id" in c.lower() or c.lower() == "id"), df_table.columns[2] if len(df_table.columns)>2 else df_table.columns[0])
        name_col = next((c for c in df_table.columns if "tên bưu cục" in c.lower() or "kho_giao_name" in c.lower() or ("tên" in c.lower() and "id" not in c.lower())), df_table.columns[3] if len(df_table.columns)>3 else df_table.columns[1])
        
        df_table = df_table.dropna(subset=[id_col, name_col], how='all')
        df_table = df_table[df_table[id_col].astype(str).str.strip() != ""]
        
        # Ensure clean mappings from co_cau_ntb.csv
        id_to_am = {}
        id_to_prov = {}
        name_to_am = {}
        name_to_prov = {}
        co_cau_path = resolve_path('co_cau_ntb.csv', write=False)
        if os.path.exists(co_cau_path):
            try:
                df_cc = safe_read_csv(co_cau_path)
                for _, r in df_cc.iterrows():
                    bc_id = r.get('warehouse_id')
                    bc_name = str(r.get('Bưu cục', '')).strip()
                    am_val = str(r.get('AM', '')).strip()
                    prov_val = str(r.get('Tỉnh', '')).strip()
                    if prov_val == 'Khánh Hoà': prov_val = 'Khánh Hòa'
                    if prov_val == 'Bình Phước': prov_val = 'Lâm Đồng'
                    
                    if pd.notna(bc_id):
                        try:
                            id_to_am[int(bc_id)] = am_val
                            id_to_prov[int(bc_id)] = prov_val
                        except: pass
                    if bc_name:
                        name_clean = clean_po_name(bc_name)
                        name_to_am[name_clean] = am_val
                        name_to_prov[name_clean] = prov_val
            except Exception as e:
                print(f"Error reading co_cau_ntb.csv in process_unstable_po: {e}")

        # Now map each row
        processed_records = []
        for _, r in df_table.iterrows():
            po_id = r.get(id_col)
            po_name = r.get(name_col)
            
            mapped_am, mapped_prov = map_po_to_am_prov(po_id, po_name, id_to_am, id_to_prov, name_to_am, name_to_prov, r.get('AM', 'Không xác định'), r.get('Tỉnh', r.get('tinh_giao', 'Không xác định')))
            
            try:
                po_id_clean = int(float(po_id)) if pd.notna(po_id) else None
            except:
                continue
                
            def get_val(col_name, is_float=False):
                target = str(col_name).strip().lower().replace('\n', ' ')
                for c in r.index:
                    c_clean = str(c).strip().lower().replace('\n', ' ')
                    if c_clean == target or target in c_clean:
                        val = r[c]
                        if pd.notna(val) and str(val).strip() not in ["", "nan", "NaN", "None"]:
                            val_str = str(val).replace('%', '').replace(',', '').strip()
                            try:
                                return float(val_str) if is_float else int(float(val_str))
                            except:
                                return str(val).strip()
                return 0 if not is_float else 0.0

            vol_ton = get_val('Vol_Tồn (3)') or get_val('Vol_Tồn') or get_val('tồn lm')
            vol_moi = get_val('Vol_Mới (4)') or get_val('Vol_Mới') or get_val('tồn ktc')
            backlog = get_val('Backlog tồn đọng')
            backlog_5n = get_val('Backlog >5 ngày')
            days_unstable = get_val('Số ngày nằm trong danh sách cảnh báo - 3 tháng gần nhất') or get_val('Số ngày dự kiến clear hàng')
            reason_val = str(get_val('Cảnh báo') or get_val('Lý do cảnh báo') or get_val('ly_do_bat_on') or '').strip()
            if reason_val in ['0', '0.0', 'nan', 'NaN']: reason_val = ''

            pct_gtc_7d = round(get_val('%GTC_TB 7 ngày (1)', True), 2)
            pct_gtc_best = round(get_val('%GTC_tốt nhất', True), 2)
            pct_gtc_n1 = round(get_val('%GTC_N-1', True), 2)
            clear_days = get_val('Số ngày dự kiến clear hàng')
            pct_backlog_gan = round(get_val('%Backlog tồn đọng đã gán', True), 2)

            # Detect warning condition based on new business logic:
            # 1. HN / HCM %GTC < 50%
            # 2. Other provinces %GTC < 45%
            # 3. %GTC < 70% of historical best %GTC
            prov_lower = str(mapped_prov or '').lower()
            is_hn_hcm = any(k in prov_lower for k in ['hà nội', 'ha noi', 'hồ chí minh', 'ho chi minh', 'hcm', 'hn'])
            
            auto_reasons = []
            if is_hn_hcm and pct_gtc_7d > 0 and pct_gtc_7d < 50.0:
                auto_reasons.append("Cảnh báo GTC < 50% (HN/HCM)")
            elif not is_hn_hcm and pct_gtc_7d > 0 and pct_gtc_7d < 45.0:
                auto_reasons.append("Cảnh báo GTC < 45%")
                
            if pct_gtc_best > 0 and pct_gtc_7d > 0:
                if pct_gtc_7d < round(0.70 * pct_gtc_best, 2):
                    auto_reasons.append("Cảnh báo GTC < 70% lịch sử tốt nhất")

            if not reason_val and auto_reasons:
                reason_val = " | ".join(auto_reasons)

            status_val = "Bình thường"
            if (reason_val and ("Cảnh báo" in reason_val or "Bất ổn" in reason_val)) or auto_reasons:
                status_val = "Bất ổn"
            elif reason_val:
                status_val = "Chuẩn bị nhảy nhóm"

            record = {
                "id": po_id_clean,
                "name": str(po_name).strip() if pd.notna(po_name) else "",
                "am": mapped_am,
                "province": mapped_prov,
                "pct_gtc_7d": pct_gtc_7d,
                "pct_gtc_best": pct_gtc_best,
                "pct_gtc_n1": pct_gtc_n1,
                "reason": reason_val,
                "days_unstable": days_unstable,
                "clear_days_estimate": clear_days,
                "backlog": backlog if backlog > 0 else vol_ton,
                "pct_backlog_gan": pct_backlog_gan,
                "backlog_5n": backlog_5n,
                "status": status_val,
                # Compatibility fields
                "ton_lm": vol_ton if vol_ton > 0 else backlog,
                "ton_lm_5n": backlog_5n,
                "pct_lm_5n": pct_backlog_gan,
                "ton_ktc": vol_moi,
                "ton_ktc_cung_tinh": get_val('VolGTC_N-1'),
                "pct_ktc_cung_tinh": pct_gtc_n1,
                "pct_ty_trong": round(get_val('%Tỷ trọng (1)/(2)', True), 2),
                "total_need_deliver": get_val('Tổng Vol cần giao'),
                "staff_count": get_val('Số lượng nhân sự'),
                "pct_fd_n1": round(get_val('%FD_N-1', True), 2),
                "pct_ontime_sla_n1": round(get_val('%OntimeSLA_N-1', True), 2),
                "pct_opr_n1": round(get_val('%OPR_N-1', True), 2),
                "vol_create_n1": get_val('Volume tạo mới_N-1')
            }
            processed_records.append(record)
            
        if am:
            processed_records = [r for r in processed_records if clean_str(r.get('am')) == clean_str(am)]
        if province:
            processed_records = [r for r in processed_records if clean_str(r.get('prov')) == clean_str(province)]
        if post_office:
            processed_records = [r for r in processed_records if clean_str(r.get('name')) == clean_str(post_office)]
            
        # Group warning/unstable post offices by AM
        unstable_by_am = {}
        for rec in processed_records:
            if rec["status"] == "Bất ổn":
                am_name = rec["am"]
                if am_name not in unstable_by_am:
                    unstable_by_am[am_name] = []
                unstable_by_am[am_name].append(rec["name"])
                
        # Sort AMs by number of warning post offices
        am_deepdive = []
        for am_key, pos in unstable_by_am.items():
            am_deepdive.append({
                "am": am_key,
                "count": len(pos),
                "pos": pos
            })
        am_deepdive.sort(key=lambda x: x["count"], reverse=True)
        am_deepdive = sorted(am_deepdive, key=lambda x: x["count"], reverse=True)
        
        # Calculate actual total warnings (only Bất ổn)
        actual_total_warnings = sum(1 for rec in processed_records if rec["status"] == "Bất ổn")
        
        return {
            "update_time": update_time,
            "total_warning": actual_total_warnings,
            "records": clean_nan(processed_records),
            "am_deepdive": clean_nan(am_deepdive)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Lỗi xử lý bưu cục bất ổn: {str(e)}"}

def process_off_spe(am=None, province=None, post_office=None):
    file_path = resolve_path('off_tuyen_spe.csv', write=False)
    try:
        # Load co_cau mapping for AM lookup
        am_mapping = {}
        try:
            df_cc = safe_read_csv(resolve_path('co_cau_ntb.csv', write=False))
            if df_cc is not None and not df_cc.empty:
                for _, row_cc in df_cc.iterrows():
                    po_name = str(row_cc.get('Bưu cục', '')).strip()
                    am_name = str(row_cc.get('AM', '')).strip()
                    if po_name and am_name:
                        am_mapping[po_name.lower()] = am_name
        except Exception as ecc:
            print(f"Error loading co_cau_ntb.csv in process_off_spe: {ecc}")

        df_raw = safe_read_csv(file_path)
        if df_raw is None:
            return {"error": "Không tìm thấy file off_tuyen_spe.csv"}
        
        # Remove empty rows or rows that have all NaN
        df_raw = df_raw.dropna(how='all')
        if df_raw.empty:
            mtime_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            if file_path and os.path.exists(file_path):
                mtime_str = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d-%m-%Y %H:%M:%S")
            return {
                "update_time": mtime_str,
                "total_off": 0,
                "total_pending": 0,
                "records": [],
                "status_desc": "Hoạt động bình thường 100%"
            }
        
        # Find columns dynamically
        col_tinh = next((c for c in df_raw.columns if any(k in c.lower() for k in ["tỉnh", "tinh", "province"])), None)
        col_quan = next((c for c in df_raw.columns if any(k in c.lower() for k in ["quận", "huyện", "quan", "huyen", "district"])), None)
        col_phuong = next((c for c in df_raw.columns if any(k in c.lower() for k in ["phường", "xã", "phuong", "xa"]) and "id" not in c.lower()), None)
        col_id = next((c for c in df_raw.columns if any(k in c.lower() for k in ["id phường/xã", "id phuong/xa", "ward_code", "mã xã", "ma xa"]) or ("id" in c.lower() and any(k in c.lower() for k in ["phường", "xã", "ward"])) or c.strip().lower() in ["id", "id xã", "id xa"]), None)
        col_bc = next((c for c in df_raw.columns if any(k in c.lower() for k in ["bưu cục", "buu cuc", "post"]) or c.strip().lower() == "bc"), None)
        col_am = next((c for c in df_raw.columns if c.strip().lower() in ["am", "am phụ trách", "am phu trach"]), None)
        col_ketqua = next((c for c in df_raw.columns if any(k in c.lower() for k in ["kết quả", "ket qua", "update", "trạng thái", "trang thai"])), None)
        col_capdown = next((c for c in df_raw.columns if ("cap" in c.lower() or "down" in c.lower()) and "am" not in c.lower() and "time" not in c.lower()), None)
        col_time_off = next((c for c in df_raw.columns if any(k in c.lower() for k in ["thời gian tắt", "thoi gian tat", "tg tắt", "tg tat"])), None)
        col_time_on = next((c for c in df_raw.columns if any(k in c.lower() for k in ["thời gian mở", "thoi gian mo", "tg mở", "tg mo"])), None)
        col_note = next((c for c in df_raw.columns if any(k in c.lower() for k in ["note", "ghi chú", "ghi chu", "phân loại", "phan loai"]) and "thời gian" not in c.lower() and "am" not in c.lower()), None)
        
        # Fallback to positional indices only if essential columns are missing
        cols = list(df_raw.columns)
        if not col_tinh and len(cols) > 0: col_tinh = cols[0]
        if not col_quan and len(cols) > 1: col_quan = cols[1]
        if not col_phuong and len(cols) > 2: col_phuong = cols[2]
        if not col_id and len(cols) > 3 and any(k in str(cols[3]).lower() for k in ["id", "mã", "ma"]): col_id = cols[3]
        if not col_bc and len(cols) > 4: col_bc = cols[4]
        if not col_am and len(cols) > 5 and "am" in str(cols[5]).lower(): col_am = cols[5]
        
        df_table = df_raw.dropna(subset=[col_tinh, col_bc], how='all')
        
        processed_records = []
        total_off = 0
        total_pending = 0
        
        # Map standard dates if they look like timestamp objects
        def clean_date_str(val):
            if pd.isna(val):
                return ""
            if isinstance(val, (datetime.datetime, pd.Timestamp)):
                return val.strftime("%d-%m-%Y")
            val_str = str(val).strip()
            # If timestamp string, format it
            if "00:00:00" in val_str:
                val_str = val_str.replace(" 00:00:00", "")
            return val_str
            
        for _, r in df_table.iterrows():
            tinh_val = str(r[col_tinh]).strip() if col_tinh and pd.notna(r[col_tinh]) else "Không xác định"
            quan_val = str(r[col_quan]).strip() if col_quan and pd.notna(r[col_quan]) else ""
            phuong_val = str(r[col_phuong]).strip() if col_phuong and pd.notna(r[col_phuong]) else ""
            bc_val = str(r[col_bc]).strip() if col_bc and pd.notna(r[col_bc]) else ""
            
            ward_id_val = str(r[col_id]).strip() if col_id and pd.notna(r[col_id]) else ""
            if ward_id_val.endswith(".0"):
                ward_id_val = ward_id_val[:-2]
            if ward_id_val.lower() in ["nan", "none"]:
                ward_id_val = ""
            
            # Status:
            # - Column has "duyệt" => Đang OFF
            # - Empty / other => Đang chờ duyệt
            kq_raw = r[col_ketqua] if col_ketqua else ""
            kq_val = str(kq_raw).strip().lower() if pd.notna(kq_raw) else ""
            
            if pd.isna(kq_raw) or not kq_val:
                status_val = "Đang chờ duyệt"
                total_pending += 1
            elif "duyệt" in kq_val or "duyet" in kq_val or "off" in kq_val:
                status_val = "Đang OFF"
                total_off += 1
            else:
                status_val = "Đang chờ duyệt"
                total_pending += 1
                
            capdown_val = ""
            if col_capdown and pd.notna(r[col_capdown]):
                val_str = str(r[col_capdown]).strip()
                try:
                    val_float = float(val_str)
                    if val_float <= 1.0:
                        capdown_val = f"{int(val_float * 100)}%"
                    else:
                        capdown_val = f"{int(val_float)}%"
                except Exception:
                    if "%" in val_str:
                        capdown_val = val_str
                    
            time_off_val = clean_date_str(r[col_time_off]) if col_time_off else ""
            time_on_val = clean_date_str(r[col_time_on]) if col_time_on else ""
            note_val = str(r[col_note]).strip() if col_note and pd.notna(r[col_note]) else ""
            if note_val.lower() in ["nan", "none"]:
                note_val = ""
            
            # AM identification: prefer sheet's AM column, fallback to co_cau mapping
            am_val = str(r[col_am]).strip() if col_am and pd.notna(r[col_am]) else ""
            if not am_val or am_val.lower() in ["nan", "none"]:
                bc_clean = bc_val.lower().strip()
                am_val = am_mapping.get(bc_clean, "")
                if not am_val:
                    for cc_po, cc_am in am_mapping.items():
                        if cc_po in bc_clean or bc_clean in cc_po:
                            am_val = cc_am
                            break
            if not am_val or am_val.lower() in ["nan", "none"]:
                am_val = "Chưa phân công"
            
            processed_records.append({
                "province": tinh_val,
                "district": quan_val,
                "ward": phuong_val,
                "ward_id": ward_id_val,
                "post_office": bc_val,
                "am": am_val,
                "status": status_val,
                "pct_cap_down": capdown_val,
                "off_time": time_off_val,
                "on_time": time_on_val,
                "note": note_val
            })
            
        if am:
            processed_records = [r for r in processed_records if clean_str(r.get('am')) == clean_str(am)]
        if province:
            processed_records = [r for r in processed_records if clean_str(r.get('province')) == clean_str(province)]
        if post_office:
            processed_records = [r for r in processed_records if clean_str(r.get('post_office')) == clean_str(post_office)]
            
        total_off = sum(1 for r in processed_records if r.get("status") == "Đang OFF")
        total_pending = sum(1 for r in processed_records if r.get("status") == "Đang chờ duyệt")
            
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            update_time = datetime.datetime.fromtimestamp(mtime).strftime("%d-%m-%Y %H:%M:%S")
        else:
            update_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        
        return {
            "update_time": update_time,
            "total_off": total_off,
            "total_pending": total_pending,
            "records": clean_nan(processed_records)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Lỗi xử lý file off_tuyen_spe.xlsx: {str(e)}"}

# ==========================================
# 5. SYNC & HISTORY CACHE MANAGEMENT
# ==========================================
def load_history():
    db_history = load_json_from_db('backlog_history.json')
    if db_history is not None:
        return db_history
        
    history_file = resolve_path('backlog_history.json', write=False)
    if not os.path.exists(history_file):
        return []
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_history(history):
    save_json_to_db(history, 'backlog_history.json')
    try:
        history_file = resolve_path('backlog_history.json', write=True)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

# Save current run to history
def add_to_history(aging_data, treo_data):
    history = load_history()
    
    # Format date and time
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save simple metrics map for comparison
    aging_am_map = {}
    for r in aging_data.get("am_summary", []):
        aging_am_map[r["final_am"]] = int(r["Total"])
        
    aging_po_map = {}
    for r in aging_data.get("po_summary", []):
        aging_po_map[r["BC"]] = int(r["Total"])
        
    treo_giao_am_map = {}
    for r in treo_data.get("giao_am_summary", []):
        treo_giao_am_map[r["final_am"]] = int(r["Total"])
        
    treo_giao_po_map = {}
    for r in treo_data.get("giao_po_summary", []):
        treo_giao_po_map[r["warehouse_name"]] = int(r["Total"])
        
    treo_tra_am_map = {}
    for r in treo_data.get("tra_am_summary", []):
        treo_tra_am_map[r["final_am"]] = int(r["Total"])
        
    treo_tra_po_map = {}
    for r in treo_data.get("tra_po_summary", []):
        treo_tra_po_map[r["warehouse_name"]] = int(r["Total"])
        
    new_entry = {
        "timestamp": now_str,
        "aging_total": aging_data.get("total_backlog", 0),
        "treo_total": treo_data.get("total_backlog", 0),
        "treo_giao_total": treo_data.get("total_giao", 0),
        "treo_tra_total": treo_data.get("total_tra", 0),
        "aging_am_map": aging_am_map,
        "aging_po_map": aging_po_map,
        "treo_giao_am_map": treo_giao_am_map,
        "treo_giao_po_map": treo_giao_po_map,
        "treo_tra_am_map": treo_tra_am_map,
        "treo_tra_po_map": treo_tra_po_map
    }
    
    history.append(new_entry)
    # Keep last 20 entries
    if len(history) > 20:
        history = history[-20:]
    save_history(history)
    return now_str

# Helper to calculate chênh lệch (+/-) based on history entry
def calculate_trend(current_data, baseline_entry):
    if not baseline_entry:
        return current_data
        
    # Process Aging Backlog
    aging_am_map = baseline_entry.get("aging_am_map", {})
    aging_po_map = baseline_entry.get("aging_po_map", {})
    
    for r in current_data["aging"].get("am_summary", []):
        prev = aging_am_map.get(r["final_am"], 0)
        r["diff"] = int(r["Total"]) - prev
        
    for r in current_data["aging"].get("po_summary", []):
        prev = aging_po_map.get(r["BC"], 0)
        r["diff"] = int(r["Total"]) - prev
        
    current_data["aging"]["diff_total"] = current_data["aging"].get("total_backlog", 0) - baseline_entry.get("aging_total", 0)
    
    # Process Treo luân chuyển
    tg_am_map = baseline_entry.get("treo_giao_am_map", {})
    tg_po_map = baseline_entry.get("treo_giao_po_map", {})
    tt_am_map = baseline_entry.get("treo_tra_am_map", {})
    tt_po_map = baseline_entry.get("treo_tra_po_map", {})
    
    for r in current_data["treo"].get("giao_am_summary", []):
        prev = tg_am_map.get(r["final_am"], 0)
        r["diff"] = int(r["Total"]) - prev
        
    for r in current_data["treo"].get("giao_po_summary", []):
        prev = tg_po_map.get(r["warehouse_name"], 0)
        r["diff"] = int(r["Total"]) - prev
        
    for r in current_data["treo"].get("tra_am_summary", []):
        prev = tt_am_map.get(r["final_am"], 0)
        r["diff"] = int(r["Total"]) - prev
        
    for r in current_data["treo"].get("tra_po_summary", []):
        prev = tt_po_map.get(r["warehouse_name"], 0)
        r["diff"] = int(r["Total"]) - prev
        
    current_data["treo"]["diff_total"] = current_data["treo"].get("total_backlog", 0) - baseline_entry.get("treo_total", 0)
    current_data["treo"]["diff_giao"] = current_data["treo"].get("total_giao", 0) - baseline_entry.get("treo_giao_total", 0)
    current_data["treo"]["diff_tra"] = current_data["treo"].get("total_tra", 0) - baseline_entry.get("treo_tra_total", 0)
    
    return current_data



def process_ca_report():
    import urllib.request, io as _io

    CA_GID = '260711009'
    CA_SHEET_ID = '1JZ1eRerRqrpwjZ4HBevQunjd8VquM_cvPFz12TaJfMQ'
    url = f'https://docs.google.com/spreadsheets/d/{CA_SHEET_ID}/export?format=csv&gid={CA_GID}'

    df = None
    err_logs = []
    try:
        import requests
        h = get_google_auth_headers()
        res = requests.get(url, headers=h, timeout=30)
        if res.status_code == 200:
            content = res.content
            df = pd.read_csv(_io.BytesIO(content), header=1, encoding='utf-8')
            try:
                filepath = resolve_path('ops_ca_data.csv', write=True)
                df.to_csv(filepath, index=False)
            except Exception as _e:
                err_logs.append(f"Write CSV err: {_e}")
            save_df_to_db(df, 'ops_ca_data.csv')
            print(f"[CA] Loaded from GSheet GID={CA_GID}, shape={df.shape}")
        else:
            err_logs.append(f"GSheet HTTP {res.status_code}")
            raise Exception(f"GSheet status {res.status_code}")
    except Exception as e:
        err_logs.append(f"GSheet fetch exception: {e}")
        try:
            df = safe_read_csv(resolve_path('ops_ca_data.csv', write=False))
            if df is None or df.empty:
                df = load_df_from_db('ops_ca_data.csv')
            err_logs.append(f"Fallback df shape: {df.shape if df is not None else None}")
        except Exception as fe:
            err_logs.append(f"Fallback err: {fe}")

    if df is None or df.empty:
        return {"error": f"Không tìm thấy dữ liệu báo cáo Ca. Details: {' | '.join(err_logs)}"}

    def clean_num(x):
        try:
            if pd.isna(x) or str(x).strip() == '': return 0
            s = str(x).replace('.','').replace(',','').strip()
            return int(s)
        except:
            return 0

    def clean_pct(x):
        try:
            if pd.isna(x) or str(x).strip() == '': return 0.0
            val_str = str(x).strip()
            has_percent = '%' in val_str
            val_str = val_str.replace('%', '').replace(',', '.')
            val = float(val_str)
            if not has_percent and 0 < val <= 1.0:
                val = val * 100
            return val
        except:
            return 0.0

    records = []
    
    # Check if we should parse by index or by column name pattern (in case DB fallback has different shape)
    if df.shape[1] >= 41:
        # Position-based parsing (highly robust for new layout)
        for idx, row in df.iterrows():
            date1 = str(row.iloc[3]).strip()
            date2 = str(row.iloc[17]).strip()
            date3 = str(row.iloc[31]).strip()
            row_date = date1 if (date1 and date1 not in ('nan', 'None', '')) else (date2 if (date2 and date2 not in ('nan', 'None', '')) else date3)
            if not row_date or row_date in ('nan', 'None', '', 'Time'):
                continue

            # Ca 1
            bc1 = str(row.iloc[1]).strip()
            vol1 = clean_num(row.iloc[4])
            pct_gan1 = clean_pct(row.iloc[5])
            pct_gtc1 = clean_pct(row.iloc[6])
            gtc1 = round(vol1 * (pct_gtc1 / 100.0))
            am1 = str(row.iloc[12]).strip()
            if bc1 and bc1 not in ('nan', 'None', '', 'Cấp Quản Lý', 'Chi tiết'):
                records.append({
                    'Bưu Cục': bc1,
                    'AM': am1 if am1 not in ('nan', 'None', '') else 'Không xác định',
                    'Date': row_date,
                    'Loại Hàng': 'Hàng Mới Ca 1',
                    'Volume': vol1,
                    'Sản Lượng Giao Thành Công': gtc1,
                    'Assigned_Vol': vol1 * (pct_gan1 / 100.0)
                })

            # Ca 2
            bc2 = str(row.iloc[15]).strip()
            vol2 = clean_num(row.iloc[18])
            pct_gan2 = clean_pct(row.iloc[19])
            pct_gtc2 = clean_pct(row.iloc[20])
            gtc2 = round(vol2 * (pct_gtc2 / 100.0))
            am2 = str(row.iloc[26]).strip()
            if bc2 and bc2 not in ('nan', 'None', '', 'Cấp Quản Lý', 'Chi tiết'):
                records.append({
                    'Bưu Cục': bc2,
                    'AM': am2 if am2 not in ('nan', 'None', '') else 'Không xác định',
                    'Date': row_date,
                    'Loại Hàng': 'Hàng Mới Ca 2',
                    'Volume': vol2,
                    'Sản Lượng Giao Thành Công': gtc2,
                    'Assigned_Vol': vol2 * (pct_gan2 / 100.0)
                })

            # Hàng Tồn
            bc3 = str(row.iloc[29]).strip()
            vol3 = clean_num(row.iloc[32])
            pct_gan3 = clean_pct(row.iloc[33])
            pct_gtc3 = clean_pct(row.iloc[34])
            gtc3 = round(vol3 * (pct_gtc3 / 100.0))
            am3 = str(row.iloc[40]).strip()
            if bc3 and bc3 not in ('nan', 'None', '', 'Cấp Quản Lý', 'Chi tiết'):
                records.append({
                    'Bưu Cục': bc3,
                    'AM': am3 if am3 not in ('nan', 'None', '') else 'Không xác định',
                    'Date': row_date,
                    'Loại Hàng': 'Hàng Tồn',
                    'Volume': vol3,
                    'Sản Lượng Giao Thành Công': gtc3,
                    'Assigned_Vol': vol3 * (pct_gan3 / 100.0)
                })
    else:
        # Fallback to column name patterns if database layout is old
        cols = df.columns.tolist()
        
        col_bc1  = next((c for c in cols if 'tiết' in str(c).lower() and '.1' not in str(c).lower() and '.2' not in str(c).lower()), 'Chi tiết')
        col_vol1 = next((c for c in cols if 'volume' in str(c).lower() and '.1' not in str(c).lower() and '.2' not in str(c).lower()), 'Volume')
        col_gan1 = next((c for c in cols if 'gán' in str(c).lower() and '.1' not in str(c).lower() and '.2' not in str(c).lower()), '% Gán')
        col_gtc1 = next((c for c in cols if '% gtc' in str(c).lower() and '.1' not in str(c).lower() and '.2' not in str(c).lower()), '% GTC')
        col_am1  = next((c for c in cols if 'am' in str(c).lower() and '.1' not in str(c).lower() and '.2' not in str(c).lower()), 'AM')
        col_date1 = next((c for c in cols if 'time' in str(c).lower() and '.1' not in str(c).lower() and '.2' not in str(c).lower()), 'Time')

        col_bc2  = next((c for c in cols if 'tiết.1' in str(c).lower()), 'Chi tiết.1')
        col_vol2 = next((c for c in cols if 'volume.1' in str(c).lower()), 'Volume.1')
        col_gan2 = next((c for c in cols if 'gán.1' in str(c).lower() or ('gán' in str(c).lower() and '.1' in str(c).lower())), '% Gán.1')
        col_gtc2 = next((c for c in cols if '% gtc.1' in str(c).lower() or ('gtc' in str(c).lower() and '.1' in str(c).lower())), '% GTC.1')
        col_am2  = next((c for c in cols if 'am.1' in str(c).lower()), 'AM.1')
        col_date2 = next((c for c in cols if 'time.1' in str(c).lower()), 'Time.1')

        col_bc3  = next((c for c in cols if 'tiết.2' in str(c).lower()), 'Chi tiết.2')
        col_vol3 = next((c for c in cols if 'volume.2' in str(c).lower()), 'Volume.2')
        col_gan3 = next((c for c in cols if 'gán.2' in str(c).lower() or ('gán' in str(c).lower() and '.2' in str(c).lower())), '% Gán.2')
        col_gtc3 = next((c for c in cols if '% gtc.2' in str(c).lower() or ('gtc' in str(c).lower() and '.2' in str(c).lower())), '% GTC.2')
        col_am3  = next((c for c in cols if 'am.2' in str(c).lower()), 'AM.2')
        col_date3 = next((c for c in cols if 'time.2' in str(c).lower()), 'Time.2')

        for idx, row in df.iterrows():
            date1 = str(row.get(col_date1, '')).strip()
            date2 = str(row.get(col_date2, '')).strip()
            date3 = str(row.get(col_date3, '')).strip()
            row_date = date1 if (date1 and date1 not in ('nan', 'None', '')) else (date2 if (date2 and date2 not in ('nan', 'None', '')) else date3)
            if not row_date or row_date in ('nan', 'None', '', 'Time'):
                continue

            # Ca 1
            bc1 = str(row.get(col_bc1, '')).strip()
            vol1 = clean_num(row.get(col_vol1, 0))
            pct_gan1 = clean_pct(row.get(col_gan1, 0.0))
            pct_gtc1 = clean_pct(row.get(col_gtc1, 0.0))
            gtc1 = round(vol1 * (pct_gtc1 / 100.0))
            am1 = str(row.get(col_am1, 'Không xác định')).strip()
            if bc1 and bc1 not in ('nan', 'None', '', 'Cấp Quản Lý', 'Chi tiết'):
                records.append({'Bưu Cục': bc1, 'AM': am1, 'Date': row_date, 'Loại Hàng': 'Hàng Mới Ca 1', 'Volume': vol1, 'Sản Lượng Giao Thành Công': gtc1, 'Assigned_Vol': vol1 * (pct_gan1 / 100.0)})

            # Ca 2
            bc2 = str(row.get(col_bc2, '')).strip()
            vol2 = clean_num(row.get(col_vol2, 0))
            pct_gan2 = clean_pct(row.get(col_gan2, 0.0))
            pct_gtc2 = clean_pct(row.get(col_gtc2, 0.0))
            gtc2 = round(vol2 * (pct_gtc2 / 100.0))
            am2 = str(row.get(col_am2, 'Không xác định')).strip()
            if bc2 and bc2 not in ('nan', 'None', '', 'Cấp Quản Lý', 'Chi tiết'):
                records.append({'Bưu Cục': bc2, 'AM': am2, 'Date': row_date, 'Loại Hàng': 'Hàng Mới Ca 2', 'Volume': vol2, 'Sản Lượng Giao Thành Công': gtc2, 'Assigned_Vol': vol2 * (pct_gan2 / 100.0)})

            # Hàng Tồn
            bc3 = str(row.get(col_bc3, '')).strip()
            vol3 = clean_num(row.get(col_vol3, 0))
            pct_gan3 = clean_pct(row.get(col_gan3, 0.0))
            pct_gtc3 = clean_pct(row.get(col_gtc3, 0.0))
            gtc3 = round(vol3 * (pct_gtc3 / 100.0))
            am3 = str(row.get(col_am3, 'Không xác định')).strip()
            if bc3 and bc3 not in ('nan', 'None', '', 'Cấp Quản Lý', 'Chi tiết'):
                records.append({'Bưu Cục': bc3, 'AM': am3, 'Date': row_date, 'Loại Hàng': 'Hàng Tồn', 'Volume': vol3, 'Sản Lượng Giao Thành Công': gtc3, 'Assigned_Vol': vol3 * (pct_gan3 / 100.0)})

    if not records:
        return {"error": "Không có dữ liệu trong báo cáo Ca."}

    df_parsed = pd.DataFrame(records)

    # 1. Pivot Daily (for filters)
    pt_daily = df_parsed.pivot_table(index=['Date', 'AM', 'Bưu Cục'], columns='Loại Hàng', values=['Volume', 'Sản Lượng Giao Thành Công', 'Assigned_Vol'], aggfunc='sum', fill_value=0)
    pt_daily.columns = [f"{c[1]}_{c[0]}" for c in pt_daily.columns]
    pt_daily = pt_daily.reset_index()

    # 2. Pivot BC (overall aggregated)
    pt_bc = df_parsed.pivot_table(index=['AM', 'Bưu Cục'], columns='Loại Hàng', values=['Volume', 'Sản Lượng Giao Thành Công', 'Assigned_Vol'], aggfunc='sum', fill_value=0)
    pt_bc.columns = [f"{c[1]}_{c[0]}" for c in pt_bc.columns]
    pt_bc = pt_bc.reset_index()

    # 3. Pivot AM (overall aggregated)
    pt_am = df_parsed.pivot_table(index=['AM'], columns='Loại Hàng', values=['Volume', 'Sản Lượng Giao Thành Công', 'Assigned_Vol'], aggfunc='sum', fill_value=0)
    pt_am.columns = [f"{c[1]}_{c[0]}" for c in pt_am.columns]
    pt_am = pt_am.reset_index()

    # Lists for dropdown filter options
    unique_dates = df_parsed['Date'].unique().tolist()
    unique_dates = sorted([d for d in unique_dates if d not in ('nan', '')])
    
    unique_ams = df_parsed['AM'].unique().tolist()
    unique_ams = sorted([a for a in unique_ams if a not in ('nan', '', 'Không xác định')])

    # 4. Extract Warning Post Offices info from buu_cuc_bat_on
    warning_pos_map = {}
    try:
        unstable_data = process_unstable_po()
        for r in unstable_data.get('records', []):
            pname = str(r.get('name', '')).strip()
            if pname:
                warning_pos_map[pname] = {
                    'name': pname,
                    'status': r.get('status', 'Bất ổn'),
                    'reason': r.get('reason', 'Bưu cục cảnh báo'),
                    'days_unstable': r.get('days_unstable', 0),
                    'backlog': r.get('backlog', 0),
                    'am': r.get('am', ''),
                    'province': r.get('province', '')
                }
    except Exception as _e_unstable:
        print(f"Warning PO lookup error in process_ca_report: {_e_unstable}")

    return {
        "by_bc_daily": clean_nan(pt_daily.to_dict(orient='records')),
        "by_bc": clean_nan(pt_bc.to_dict(orient='records')),
        "by_am": clean_nan(pt_am.to_dict(orient='records')),
        "unique_dates": unique_dates,
        "unique_ams": unique_ams,
        "warning_pos": warning_pos_map
    }



def load_fd_history():
    db_history = load_json_from_db('fd_history.json')
    if db_history is not None:
        return db_history
    history_file = resolve_path('fd_history.json', write=False)
    if not os.path.exists(history_file):
        return []
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_fd_history(history):
    save_json_to_db(history, 'fd_history.json')
    try:
        history_file = resolve_path('fd_history.json', write=True)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving fd_history: {e}")

def add_fd_to_history(summary_metrics, channel_breakdown, am_rankings, all_pos, date_str):
    history = load_fd_history()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_date = str(date_str).strip() if date_str else now_str[:10]
    
    new_entry = {
        "timestamp": now_str,
        "date": clean_date,
        "summary": summary_metrics,
        "channels": {c.get("channel", ""): c for c in channel_breakdown},
        "am_map": {a.get("am", ""): a for a in am_rankings},
        "po_map": {p.get("post_office", ""): p for p in all_pos}
    }
    
    existing_idx = next((i for i, h in enumerate(history) if h.get("date") == clean_date), None)
    if existing_idx is not None:
        history[existing_idx] = new_entry
    else:
        history.append(new_entry)
        
    if len(history) > 60:
        history = history[-60:]
    save_fd_history(history)
    return history

def process_fd_report(am=None, province=None, post_office=None):
    import csv
    import re
    import os
    
    file_path = resolve_path('ops_fd.csv', write=False)
    if not os.path.exists(file_path):
        return {"error": "Không tìm thấy file ops_fd.csv"}
        
    def clean_pct(val):
        if val is None or val == '':
            return 0.0
        val_str = str(val).strip()
        val_str = val_str.replace('%', '').replace(',', '.')
        val_str = val_str.replace('▲', '').replace('▼', '').strip()
        try:
            return float(val_str)
        except:
            return 0.0

    def clean_num(val):
        if val is None or val == '':
            return 0
        val_str = str(val).strip().replace(',', '')
        try:
            f = float(val_str)
            return int(f) if f.is_integer() else f
        except:
            return 0

    try:
        lines = []
        for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, mode='r', encoding=enc) as f:
                    reader = csv.reader(f)
                    lines = list(reader)
                if lines:
                    break
            except Exception:
                continue
            
        if not lines:
            return {"error": "File ops_fd.csv trống"}
            
        # 1. Parse Title & Date / Period
        title = "BÁO CÁO %FD HUB (N-1) – VÙNG NTB"
        date_str = "N-1"
        if len(lines) > 0 and len(lines[0]) > 0 and lines[0][0].strip():
            title = lines[0][0].strip()
            m = re.search(r'\(N-1\)|N-1|\d{2}/\d{2}/\d{4}', title)
            if m:
                date_str = m.group(0)

        # 2. Parse Channel Breakdown from Header (Rows 1-3)
        channel_breakdown = []
        if len(lines) >= 3:
            r1 = lines[0]
            r2 = lines[1]
            r3 = lines[2]
            c = 0
            while c < max(len(r1), len(r3)):
                ch_name = r1[c].strip() if c < len(r1) else ""
                if ch_name and ch_name not in ['BÁO CÁO %FD HUB (N-1) – VÙNG NTB', '1. BẢNG TỔNG QUAN VÙNG NTB (N-1)']:
                    total_orders = clean_num(r3[c]) if c < len(r3) else 0
                    ret_rate = clean_pct(r3[c+1]) if (c+1) < len(r3) else 0.0
                    channel_breakdown.append({
                        "channel": ch_name,
                        "total_orders": total_orders,
                        "return_rate": ret_rate
                    })
                    c += 2
                else:
                    c += 1

        # 3. Parse Sections
        summary_metrics = {}
        top_10_pos = []
        am_rankings = []
        all_pos = []

        current_section = None

        for line in lines:
            if not line or not any(str(cell).strip() for cell in line):
                continue

            first_cell = line[0].strip() if len(line) > 0 else ""

            if "1. BẢNG TỔNG QUAN" in first_cell:
                current_section = "summary"
                continue
            elif "2. TOP 10 BƯU CỤC" in first_cell:
                current_section = "top10"
                continue
            elif "3. XẾP HẠNG %FD THEO CÁC AM" in first_cell:
                current_section = "am_ranking"
                continue
            elif "4. DANH SÁCH TẤT CẢ BƯU CỤC" in first_cell:
                current_section = "all_pos"
                continue

            # Skip table headers
            if first_cell in ['Chỉ Số Tổng Quan', 'STT'] or 'Tên Bưu Cục' in line or 'AM Phụ Trách' in line:
                continue

            if current_section == "summary":
                metric_name = first_cell
                val_str = line[1].strip() if len(line) > 1 else ""
                note = line[2].strip() if len(line) > 2 else ""
                if "Tổng Đơn Có Gán Giao" in metric_name:
                    summary_metrics["total_orders"] = clean_num(val_str)
                    summary_metrics["total_orders_note"] = note
                elif "Tổng Đơn Return" in metric_name:
                    summary_metrics["return_orders"] = clean_num(val_str)
                    summary_metrics["return_orders_note"] = note
                elif "%FD Tổng Vùng" in metric_name:
                    summary_metrics["fd_rate"] = clean_pct(val_str)
                    summary_metrics["fd_rate_note"] = note
                elif "Số Bưu Cục Quản Lý" in metric_name:
                    summary_metrics["po_count"] = clean_num(val_str)
                    summary_metrics["po_count_note"] = note

            elif current_section == "top10":
                if len(line) >= 7 and first_cell.isdigit():
                    top_10_pos.append({
                        "stt": int(first_cell),
                        "post_office": line[1].strip(),
                        "am": line[2].strip(),
                        "total_orders": clean_num(line[3]),
                        "return_orders": clean_num(line[4]),
                        "fd_rate": clean_pct(line[5]),
                        "return_share": clean_pct(line[6])
                    })

            elif current_section == "am_ranking":
                if len(line) >= 7 and first_cell.isdigit():
                    am_rankings.append({
                        "stt": int(first_cell),
                        "am": line[1].strip(),
                        "total_orders": clean_num(line[2]),
                        "return_orders": clean_num(line[3]),
                        "fd_rate": clean_pct(line[4]),
                        "return_share": clean_pct(line[5]),
                        "volume_share": clean_pct(line[6]) if len(line) > 6 else 0.0
                    })

            elif current_section == "all_pos":
                if len(line) >= 7 and first_cell.isdigit():
                    all_pos.append({
                        "stt": int(first_cell),
                        "post_office": line[1].strip(),
                        "am": line[2].strip(),
                        "total_orders": clean_num(line[3]),
                        "return_orders": clean_num(line[4]),
                        "fd_rate": clean_pct(line[5]),
                        "return_share": clean_pct(line[6])
                    })

        # Summary fallback calculation if not explicitly in table
        if "total_orders" not in summary_metrics and all_pos:
            tot = sum(p["total_orders"] for p in all_pos)
            ret = sum(p["return_orders"] for p in all_pos)
            summary_metrics["total_orders"] = tot
            summary_metrics["return_orders"] = ret
            summary_metrics["fd_rate"] = round(ret / tot * 100, 2) if tot > 0 else 0.0
            summary_metrics["po_count"] = len(all_pos)

        # Automatically save snapshot to DB & calculate trend / comparison
        comparison_info = {"has_baseline": False}
        try:
            history = add_fd_to_history(summary_metrics, channel_breakdown, am_rankings, all_pos, date_str)
            # Find baseline entry (different from current date)
            clean_date = str(date_str).strip() if date_str else ""
            prev_entries = [h for h in history if h.get("date") != clean_date]
            if prev_entries:
                baseline = prev_entries[-1]
                prev_sum = baseline.get("summary", {})
                prev_rate = prev_sum.get("fd_rate", 0.0)
                diff_rate = round(summary_metrics.get("fd_rate", 0.0) - prev_rate, 2)
                diff_total = summary_metrics.get("total_orders", 0) - prev_sum.get("total_orders", 0)
                diff_return = summary_metrics.get("return_orders", 0) - prev_sum.get("return_orders", 0)
                
                comparison_info = {
                    "has_baseline": True,
                    "baseline_date": baseline.get("date", ""),
                    "prev_fd_rate": prev_rate,
                    "vs_d1_rate": diff_rate,
                    "vs_d1_total": diff_total,
                    "vs_d1_return": diff_return
                }
                
                # Attach diff to AM rankings
                prev_am_map = baseline.get("am_map", {})
                for a in am_rankings:
                    prev_a = prev_am_map.get(a.get("am", ""), {})
                    if prev_a and "fd_rate" in prev_a:
                        a["diff_fd"] = round(a.get("fd_rate", 0.0) - prev_a.get("fd_rate", 0.0), 2)
                        a["prev_fd"] = prev_a.get("fd_rate", 0.0)
                        
                # Attach diff to POs
                prev_po_map = baseline.get("po_map", {})
                for p in all_pos:
                    prev_p = prev_po_map.get(p.get("post_office", ""), {})
                    if prev_p and "fd_rate" in prev_p:
                        p["diff_fd"] = round(p.get("fd_rate", 0.0) - prev_p.get("fd_rate", 0.0), 2)
                        p["prev_fd"] = prev_p.get("fd_rate", 0.0)
        except Exception as hist_err:
            print(f"Error updating FD history comparison: {hist_err}")

        # Filters
        filtered_pos = all_pos
        filtered_am_rankings = am_rankings
        filtered_top10 = top_10_pos

        if am:
            am_clean = am.lower().strip()
            filtered_pos = [p for p in filtered_pos if am_clean in p["am"].lower()]
            filtered_am_rankings = [a for a in filtered_am_rankings if am_clean in a["am"].lower()]
            filtered_top10 = [p for p in filtered_pos[:10]]

        if post_office:
            po_clean = post_office.lower().strip()
            filtered_pos = [p for p in filtered_pos if po_clean in p["post_office"].lower()]

        unique_ams = sorted(list(set(p["am"] for p in all_pos if p["am"])))

        return {
            "title": title,
            "date": date_str,
            "summary": summary_metrics,
            "channels": channel_breakdown,
            "comparison": comparison_info,
            "top10": filtered_top10,
            "am_rankings": filtered_am_rankings,
            "all_pos": filtered_pos,
            "unique_ams": unique_ams,
            # Backward compatibility keys
            "kpi": {
                "fd_n": summary_metrics.get("fd_rate", 0.0),
                "fd_n1": comparison_info.get("prev_fd_rate", summary_metrics.get("fd_rate", 0.0)),
                "vs_n1": comparison_info.get("vs_d1_rate", 0.0),
                "fd_n7": 0.0,
                "vs_n7": 0.0
            },
            "po": [
                {
                    "post_office": p["post_office"],
                    "am": p["am"],
                    "fd_n": p["fd_rate"],
                    "fd_n1": p.get("prev_fd", p["fd_rate"]),
                    "vs_n1": p.get("diff_fd", 0.0),
                    "fd_n7": 0.0,
                    "vs_n7": 0.0,
                    "vol_giao": p["total_orders"],
                    "vol_tra": p["return_orders"],
                    "ty_trong_tra": p["return_share"]
                }
                for p in filtered_pos
            ],
            "am": [
                {
                    "am": a["am"],
                    "fd_n": a["fd_rate"],
                    "fd_n1": a.get("prev_fd", a["fd_rate"]),
                    "vs_n1": a.get("diff_fd", 0.0),
                    "fd_n7": 0.0,
                    "vs_n7": 0.0,
                    "vol_tra": a["return_orders"],
                    "ty_trong_tra": a["return_share"]
                }
                for a in filtered_am_rankings
            ],
            "province": []
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Lỗi xử lý FD report: {str(e)}"}


# ==========================================
# 6. IN-MEMORY CACHE DECLARATION & INITIALIZATION
# ==========================================
OPERATIONAL_CACHE = None
OPR_CACHE = None
BACKLOG_CACHE_RAW = None
UNSTABLE_PO_CACHE = None
OFF_SPE_CACHE = None
FD_CACHE = None
CA_REPORT_CACHE = None
PRODUCTIVITY_REALTIME_CACHE = None
HEAVY_10KG_CACHE = None

LAST_CACHE_UPDATE_TIME = None
LAST_CACHE_CHECK_TIME = 0
LAST_DB_SYNC_TIME = 0

# Dataframe caches for NTB Summary Dashboard
DF_GTC_CACHE = None
DF_LTC_CACHE = None
DF_CO_CAU_CACHE = None
DF_AGING_CACHE = None
DF_TREO_CACHE = None
DF_TTS_CACHE = None
DF_TAO_DON_CACHE = None
DF_BUU_CUC_TYPE_MAP = None

def load_buu_cuc_type_map():
    file_path = resolve_path('buu_cuc_bat_on.csv', write=False)
    try:
        df_raw = safe_read_csv(file_path, header=None)
        if df_raw is None or df_raw.empty:
            return {}
        header_row_idx = None
        for r_idx in range(len(df_raw)):
            row_vals = [str(x).lower().strip() for x in df_raw.iloc[r_idx].values]
            if any("tổng số lượng" in x or "thời gian cập nhật" in x for x in row_vals):
                continue
            if any(x == "bưu cục" or x == "chi tiết" or x == "tên bc" or "tên bưu cục" in x or "kho_giao_id" in x or "kho_giao_name" in x or "tinh_giao" in x for x in row_vals):
                header_row_idx = r_idx
                break
        if header_row_idx is None:
            header_row_idx = 4 if len(df_raw) > 4 else 0
        df_table = safe_read_csv(file_path, skiprows=header_row_idx)
        if df_table is None or df_table.empty:
            return {}
        df_table.columns = [str(c).strip() for c in df_table.columns]
        
        id_col = next((c for c in df_table.columns if "id" in c.lower() or "kho_giao_id" in c.lower()), None)
        type_col = next((c for c in df_table.columns if "type" in c.lower() or "warehouse_type" in c.lower() or "loại" in c.lower()), None)
        
        if id_col and type_col:
            df_table = df_table.dropna(subset=[id_col, type_col])
            type_map = {}
            for _, row in df_table.iterrows():
                try:
                    p_id = int(float(row[id_col]))
                    p_type = str(row[type_col]).strip()
                    type_map[p_id] = p_type
                except:
                    pass
            return type_map
    except Exception as e:
        print(f"Error loading buu_cuc_type_map: {e}")
    return {}

def load_vols_tao_don_df():
    file_path = resolve_path('vols_tao_don.csv', write=False)
    try:
        df = safe_read_csv(file_path)
        if df is None or df.empty:
            return None
        
        # Standardize column names for vols_tao_don
        col_rename = {}
        for c in df.columns:
            cl = str(c).strip().lower()
            if cl == 'date': col_rename[c] = 'Date'
            elif cl in ['vùng', 'vung']: col_rename[c] = 'Vùng'
            elif cl in ['tỉnh', 'tinh']: col_rename[c] = 'Tỉnh'
            elif cl in ['quận/huyện', 'quan/huyen', 'quận_huyện', 'district']: col_rename[c] = 'Quận/Huyện'
            elif cl in ['phường/xã', 'phuong/xa', 'phường_xã', 'ward']: col_rename[c] = 'Phường/Xã'
            elif cl in ['bưu cục', 'buu cuc', 'bưu_cục', 'buu_cuc', 'bc', 'post_office']: col_rename[c] = 'Bưu cục'
            elif cl in ['khách hàng', 'khach hang', 'customer']: col_rename[c] = 'Khách hàng'
            elif cl in ['volume', 'vol', 'sản lượng']: col_rename[c] = 'Volume'
            elif cl in ['khối lượng', 'khoi luong', 'weight']: col_rename[c] = 'Khối lượng'
            elif cl in ['warehouse_id', 'idbuucuc', 'mã bưu cục']: col_rename[c] = 'warehouse_id'
            elif cl in ['bat_on', 'bất ổn']: col_rename[c] = 'bat_on'
        
        if col_rename:
            df.rename(columns=col_rename, inplace=True)
            
        df['Date'] = pd.to_datetime(df['Date'])
        if 'bat_on' in df.columns:
            df = df[df['bat_on'].fillna('').str.strip() != 'BC Cũ/Không thuộc ĐCL'].copy()
        return df
    except Exception as e:
        print(f"Error loading vols_tao_don.csv: {e}")
    return None

def clean_str_key(val):
    if pd.isna(val):
        return "unknown"
    val = str(val).strip().lower()
    replacements = {
        "lâm đồng": "lam_dong",
        "bình thuận": "binh_thuan",
        "khánh hòa": "khanh_hoa",
        "ninh thuận": "ninh_thuan",
        "đắk nông": "dak_nong",
        "đắc nông": "dak_nong"
    }
    return replacements.get(val, val.replace(" ", "_"))

def get_dataframes(force=False, raw_gtc=None, raw_ltc=None, raw_co_cau=None, raw_aging=None, raw_co_cau_aging=None, raw_treo=None, raw_co_cau_treo=None, raw_tts=None):
    global DF_GTC_CACHE, DF_LTC_CACHE, DF_CO_CAU_CACHE, DF_AGING_CACHE, DF_TREO_CACHE, DF_TTS_CACHE
    import gc
    if force or DF_GTC_CACHE is None or DF_LTC_CACHE is None or DF_CO_CAU_CACHE is None or DF_AGING_CACHE is None or DF_TREO_CACHE is None or DF_TTS_CACHE is None:
        if not force:
            print("Cache is empty. Initializing cache synchronously...")
            try:
                update_all_caches()
            except Exception as e:
                print(f"Error loading cache synchronously: {e}")
                raise RuntimeError("Dữ liệu đang được tải vào bộ nhớ đệm hoặc chưa được đồng bộ. Vui lòng đợi vài giây hoặc nhấn nút Đồng bộ dữ liệu.")
            if DF_GTC_CACHE is None or DF_LTC_CACHE is None or DF_CO_CAU_CACHE is None or DF_AGING_CACHE is None or DF_TREO_CACHE is None or DF_TTS_CACHE is None:
                raise RuntimeError("Dữ liệu đang được tải vào bộ nhớ đệm hoặc chưa được đồng bộ. Vui lòng đợi vài giây hoặc nhấn nút Đồng bộ dữ liệu.")
        bc_to_am = {}
        bc_to_prov = {}
        
        # 1. Load and process Báo cáo Vận hành
        if raw_gtc is None:
            raw_gtc = safe_read_csv(resolve_path('ops_gtc.csv', write=False))
        raw_gtc = clean_ops_df(raw_gtc, "gtc")
        
        if raw_ltc is None:
            raw_ltc = safe_read_csv(resolve_path('ops_ltc.csv', write=False))
        raw_ltc = clean_ops_df(raw_ltc, "ltc")
        
        if raw_co_cau is None:
            raw_co_cau = safe_read_csv(resolve_path('ops_co_cau.csv', write=False))

        if raw_tts is None:
            raw_tts = safe_read_csv(resolve_path('ops_tts.csv', write=False))
        raw_tts = clean_ops_df(raw_tts, "tts")
            
        if raw_gtc is None or raw_ltc is None or raw_co_cau is None:
            raise FileNotFoundError("Không tìm thấy dữ liệu vận hành CSV (ops_gtc.csv, ops_ltc.csv hoặc ops_co_cau.csv).")
            
        cq_gtc = next((c for c in raw_gtc.columns if c.lower() == 'cấp quản lý'), None)
        vol_gtc = next((c for c in raw_gtc.columns if c.lower() == 'volume'), None)
        df_gtc = raw_gtc.copy()
        if cq_gtc:
            df_gtc = df_gtc[df_gtc[cq_gtc] != 'Grand Total']
        if vol_gtc:
            df_gtc = df_gtc.dropna(subset=[vol_gtc]).copy()
        else:
            df_gtc = df_gtc.copy()

        if 'Leadtime' not in df_gtc.columns:
            df_gtc['Leadtime'] = np.nan
        else:
            df_gtc['Leadtime'] = pd.to_numeric(df_gtc['Leadtime'], errors='coerce')
        
        cq_ltc = next((c for c in raw_ltc.columns if c.lower() == 'cấp quản lý'), None)
        vol_ltc = next((c for c in raw_ltc.columns if c.lower() == 'volume'), None)
        df_ltc = raw_ltc.copy()
        if cq_ltc:
            df_ltc = df_ltc[df_ltc[cq_ltc] != 'Grand Total']
        if vol_ltc:
            df_ltc = df_ltc.dropna(subset=[vol_ltc]).copy()
        else:
            df_ltc = df_ltc.copy()

        if 'Leadtime' not in df_ltc.columns:
            df_ltc['Leadtime'] = np.nan
        else:
            df_ltc['Leadtime'] = pd.to_numeric(df_ltc['Leadtime'], errors='coerce')
        
        df_tts = None
        if raw_tts is not None:
            df_tts = raw_tts.copy()
            vol_tts = next((c for c in raw_tts.columns if c.lower() == 'volume'), None)
            if vol_tts:
                df_tts = df_tts.dropna(subset=[vol_tts]).copy()
            cq_tts = next((c for c in df_tts.columns if c.lower() == 'cấp quản lý'), None)
            if cq_tts:
                df_tts = df_tts[df_tts[cq_tts] != 'Grand Total'].copy()
            leadtime_col = next((c for c in df_tts.columns if c.lower() == 'leadtime'), 'Leadtime')
            df_tts['Leadtime'] = pd.to_numeric(df_tts.get(leadtime_col, 0), errors='coerce')
            
        df_co_cau = raw_co_cau.copy()
        
        # Map co_cau
        for _, r in df_co_cau.iterrows():
            bc = str(r.get('BC', '')).strip().lower()
            buucuc = str(r.get('Bưu cục', '')).strip().lower()
            am = str(r.get('AM', r.get('Am', r.get('ID - Họ Tên Am', '')))).strip()
            prov = str(r.get('Tỉnh', '')).strip()
            if prov == 'Bình Phước':
                prov = 'Lâm Đồng'
            if bc and bc != 'nan':
                bc_to_am[bc] = am
                bc_to_prov[bc] = prov
            if buucuc and buucuc != 'nan':
                bc_to_am[buucuc] = am
                bc_to_prov[buucuc] = prov
                
        # Delete raw and clean memory (keep raw_co_cau for reuse in aging/treo)
        del raw_gtc, raw_ltc
        if raw_tts is not None:
            del raw_tts
        gc.collect()
        
        # 2. Load and process Aging (reuse df_co_cau from step 1 to avoid redundant file/DB loads)
        if raw_aging is None:
            raw_aging = safe_read_csv(resolve_path('aging_raw.csv', write=False))
        if raw_co_cau_aging is None:
            raw_co_cau_aging = raw_co_cau  # Reuse already-loaded co_cau
            
        if raw_aging is None or raw_co_cau_aging is None:
            raise FileNotFoundError("Không tìm thấy dữ liệu aging CSV (aging_raw.csv hoặc ops_co_cau.csv).")
            
        df_aging = raw_aging.copy()
        if 'am_name' not in df_aging.columns:
            df_aging['am_name'] = np.nan
        if 'Trạng thái' not in df_aging.columns:
            df_aging['Trạng thái'] = np.nan
        # bc_to_am and bc_to_prov already populated from step 1, no need to iterate again
                
        del raw_aging, raw_co_cau_aging
        gc.collect()
        
        # 3. Load and process Treo (reuse co_cau from step 1)
        if raw_treo is None:
            raw_treo = safe_read_csv(resolve_path('treo_stuck.csv', write=False))
        if raw_co_cau_treo is None:
            raw_co_cau_treo = raw_co_cau  # Reuse already-loaded co_cau
            
        if raw_treo is None or raw_co_cau_treo is None:
            raise FileNotFoundError("Không tìm thấy dữ liệu treo luân chuyển CSV (treo_stuck.csv hoặc ops_co_cau.csv).")
            
        df_treo = raw_treo.copy()
        if 'am_name' not in df_treo.columns:
            df_treo['am_name'] = np.nan
        if 'province_name' not in df_treo.columns:
            df_treo['province_name'] = np.nan
        # bc_to_am and bc_to_prov already populated from step 1, no need to iterate again
                
        del raw_treo, raw_co_cau_treo, raw_co_cau
        gc.collect()
        
        # 4. Final Processing & Mapping
        chi_tiet_gtc = next((c for c in df_gtc.columns if c.lower() in ['chi tiết', 'chitiết', 'bưu cục', 'buucuc', 'bc', 'warehouse_name']), None)
        if chi_tiet_gtc:
            df_gtc['Chi tiết'] = df_gtc[chi_tiet_gtc]
            df_gtc['clean_bc'] = df_gtc[chi_tiet_gtc].apply(clean_str)
        else:
            df_gtc['Chi tiết'] = "Không xác định"
            df_gtc['clean_bc'] = ""

        gtc_prov_col = next((df_gtc[c] for c in df_gtc.columns if c.lower() in ['tỉnh', 'tinh', 'province']), pd.Series("Không xác định", index=df_gtc.index))
        gtc_am_col = next((df_gtc[c] for c in df_gtc.columns if c.lower() in ['am', 'am_name']), pd.Series("Không xác định", index=df_gtc.index))

        df_gtc['mapped_prov'] = df_gtc['clean_bc'].map(bc_to_prov).replace({'': np.nan, 'none': np.nan, 'nan': np.nan}).fillna(gtc_prov_col).fillna("Không xác định")
        df_gtc['mapped_am'] = df_gtc['clean_bc'].map(bc_to_am).replace({'': np.nan, 'none': np.nan, 'nan': np.nan}).fillna(gtc_am_col).fillna("Không xác định")
        
        vol_gtc_col_map = next((c for c in df_gtc.columns if c.lower() == 'volume'), 'Volume')
        df_gtc['Volume'] = safe_to_numeric(df_gtc[vol_gtc_col_map]) if vol_gtc_col_map in df_gtc.columns else 0.0

        gtc_pct_col = next((c for c in df_gtc.columns if c.lower() in ['% gtc', '%gtc']), None)
        df_gtc['% GTC'] = normalize_pct_col(df_gtc[gtc_pct_col]) if gtc_pct_col else 0.0

        ct_pct_col = next((c for c in df_gtc.columns if c.lower() in ['% chuyển trả', '%chuyển trả']), None)
        df_gtc['% Chuyển trả'] = normalize_pct_col(df_gtc[ct_pct_col]) if ct_pct_col else 0.0
        
        df_gtc['delivered_vol'] = df_gtc['Volume'] * df_gtc['% GTC']
        df_gtc['return_vol'] = df_gtc['Volume'] * df_gtc['% Chuyển trả']
        df_gtc['ttc_vol'] = df_gtc['delivered_vol'] + df_gtc['return_vol']
        
        chi_tiet_ltc = next((c for c in df_ltc.columns if c.lower() in ['chi tiết', 'chitiết', 'bưu cục', 'buucuc', 'bc', 'warehouse_name']), None)
        if chi_tiet_ltc:
            df_ltc['Chi tiết'] = df_ltc[chi_tiet_ltc]
            df_ltc['clean_bc'] = df_ltc[chi_tiet_ltc].apply(clean_str)
        else:
            df_ltc['Chi tiết'] = "Không xác định"
            df_ltc['clean_bc'] = ""

        prov_col = next((c for c in df_ltc.columns if c.lower() in ['tỉnh', 'tinh', 'province']), None)
        am_col = next((c for c in df_ltc.columns if c.lower() in ['am', 'am_name']), None)
        
        df_ltc['mapped_prov'] = df_ltc['clean_bc'].map(bc_to_prov).replace({'': np.nan, 'none': np.nan, 'nan': np.nan})
        if prov_col:
            df_ltc['mapped_prov'] = df_ltc['mapped_prov'].fillna(df_ltc[prov_col])
        df_ltc['mapped_prov'] = df_ltc['mapped_prov'].fillna("Không xác định")
        
        df_ltc['mapped_am'] = df_ltc['clean_bc'].map(bc_to_am).replace({'': np.nan, 'none': np.nan, 'nan': np.nan})
        if am_col:
            df_ltc['mapped_am'] = df_ltc['mapped_am'].fillna(df_ltc[am_col])
        df_ltc['mapped_am'] = df_ltc['mapped_am'].fillna("Không xác định")
        
        # Normalize columns and map ltc_vol to Column K (Sản Lượng Lấy Thành Công)
        vol_ltc_col_map = next((c for c in df_ltc.columns if c.lower() == 'volume'), 'Volume')
        df_ltc['Volume'] = safe_to_numeric(df_ltc[vol_ltc_col_map]) if vol_ltc_col_map in df_ltc.columns else 0.0

        ltc_pct_col = next((c for c in df_ltc.columns if c.lower() in ['%ltc', '% ltc']), None)
        df_ltc['%LTC'] = normalize_pct_col(df_ltc[ltc_pct_col]) if ltc_pct_col else 0.0
        df_ltc.columns = [c.strip() for c in df_ltc.columns]
        if 'Sản Lượng Lấy Thành Công' in df_ltc.columns:
            df_ltc['ltc_vol'] = safe_to_numeric(df_ltc['Sản Lượng Lấy Thành Công'])
        else:
            df_ltc['ltc_vol'] = df_ltc['Volume'] * df_ltc['%LTC']
            
        # Align dates: ensure both df_gtc and df_ltc cover all dates present in either dataset
        if len(df_gtc) > 0 and len(df_ltc) > 0:
            gtc_dates = set(df_gtc['Time'].dropna().unique())
            ltc_dates = set(df_ltc['Time'].dropna().unique())
            
            missing_ltc_dates = [d for d in gtc_dates if d not in ltc_dates]
            if missing_ltc_dates and len(ltc_dates) > 0:
                try:
                    ltc_dates_sorted = sorted(list(ltc_dates), key=lambda x: pd.to_datetime(str(x).split(' - ')[0]))
                    latest_ltc_date = ltc_dates_sorted[-1]
                except Exception as e:
                    latest_ltc_date = list(ltc_dates)[-1]
                
                latest_ltc_rows = df_ltc[df_ltc['Time'] == latest_ltc_date].copy()
                new_rows_list = []
                for missing_date in missing_ltc_dates:
                    copied = latest_ltc_rows.copy()
                    copied['Time'] = missing_date
                    new_rows_list.append(copied)
                if new_rows_list:
                    df_ltc = pd.concat([df_ltc] + new_rows_list, ignore_index=True)

            missing_gtc_dates = [d for d in ltc_dates if d not in gtc_dates]
            if missing_gtc_dates and len(gtc_dates) > 0:
                try:
                    gtc_dates_sorted = sorted(list(gtc_dates), key=lambda x: pd.to_datetime(str(x).split(' - ')[0]))
                    latest_gtc_date = gtc_dates_sorted[-1]
                except Exception as e:
                    latest_gtc_date = list(gtc_dates)[-1]
                
                latest_gtc_rows = df_gtc[df_gtc['Time'] == latest_gtc_date].copy()
                new_rows_list = []
                for missing_date in missing_gtc_dates:
                    copied = latest_gtc_rows.copy()
                    copied['Time'] = missing_date
                    new_rows_list.append(copied)
                if new_rows_list:
                    df_gtc = pd.concat([df_gtc] + new_rows_list, ignore_index=True)
        
        aging_bc_col = next((c for c in df_aging.columns if c.lower() in ['bc', 'bưu cục', 'buucuc', 'chi tiết']), 'BC')
        if aging_bc_col in df_aging.columns:
            df_aging['clean_bc'] = df_aging[aging_bc_col].apply(clean_str)
        else:
            df_aging['clean_bc'] = ""

        aging_prov_fallback = next((df_aging[c] for c in df_aging.columns if c.lower() in ['tỉnh', 'tinh', 'province', 'mapped_prov']), pd.Series("Không xác định", index=df_aging.index))
        aging_am_fallback = next((df_aging[c] for c in df_aging.columns if c.lower() in ['am', 'am_name', 'mapped_am']), pd.Series("Không xác định", index=df_aging.index))

        df_aging['mapped_prov'] = df_aging['clean_bc'].map(bc_to_prov).fillna(aging_prov_fallback).fillna("Không xác định")
        df_aging['mapped_am'] = df_aging['clean_bc'].map(bc_to_am).fillna(aging_am_fallback).fillna("Không xác định")
        
        treo_bc_col = next((c for c in df_treo.columns if c.lower() in ['warehouse_name', 'bưu cục', 'buucuc', 'bc', 'chi tiết']), 'warehouse_name')
        if treo_bc_col in df_treo.columns:
            df_treo['clean_bc'] = df_treo[treo_bc_col].apply(clean_str)
        else:
            df_treo['clean_bc'] = ""

        treo_prov_fallback = next((df_treo[c] for c in df_treo.columns if c.lower() in ['province_name', 'tỉnh', 'tinh', 'province']), pd.Series("Không xác định", index=df_treo.index))
        treo_am_fallback = next((df_treo[c] for c in df_treo.columns if c.lower() in ['am_name', 'am', 'mapped_am']), pd.Series("Không xác định", index=df_treo.index))

        df_treo['mapped_prov'] = df_treo['clean_bc'].map(bc_to_prov).fillna(treo_prov_fallback).fillna("Không xác định")
        df_treo['mapped_am'] = df_treo['clean_bc'].map(bc_to_am).fillna(treo_am_fallback).fillna("Không xác định")
        
        if 'Trạng thái' not in df_treo.columns:
            status_col = next((c for c in df_treo.columns if str(c).strip().lower() in ['trạng thái', 'trang thai', 'status']), None)
            if status_col:
                df_treo['Trạng thái'] = df_treo[status_col]
            else:
                df_treo['Trạng thái'] = "Chưa đóng kiện"
                
        if 'Thời gian tồn đọng' not in df_treo.columns:
            ton_col = next((c for c in df_treo.columns if str(c).strip().lower() in ['thời gian tồn đọng', 'thoi gian ton dong', 'ton_dong']), None)
            if ton_col:
                df_treo['Thời gian tồn đọng'] = df_treo[ton_col]
            else:
                df_treo['Thời gian tồn đọng'] = ""

        if 'Loại đơn' not in df_treo.columns:
            loai_col = next((c for c in df_treo.columns if str(c).strip().lower() in ['loại đơn', 'loai don']), None)
            if loai_col:
                df_treo['Loại đơn'] = df_treo[loai_col]
            else:
                df_treo['Loại đơn'] = "Luân chuyển giao"

        allowed_statuses = ['Chưa đóng kiện', 'Không cần đóng kiện', 'chua dong kien', 'khong can dong kien']
        df_treo_filtered = df_treo[df_treo['Trạng thái'].astype(str).str.strip().isin(allowed_statuses) | df_treo['Trạng thái'].isna()].copy()
        
        def get_treo_bracket_local(t):
            if not isinstance(t, str):
                return None
            t = t.strip()
            if t in ["36_48", "48_72"]:
                return "36 - 72h"
            elif t in ["72_96", "96_120"]:
                return "72 - 120h"
            elif t in ["120_192"]:
                return "120 - 192h"
            elif t in ["192", "192h+"]:
                return "192h+"
            return None

        df_treo_filtered['treo_bracket'] = df_treo_filtered['Thời gian tồn đọng'].apply(get_treo_bracket_local)
        df_treo_filtered = df_treo_filtered.dropna(subset=["treo_bracket"])
        
        DF_GTC_CACHE = df_gtc
        DF_LTC_CACHE = df_ltc
        DF_CO_CAU_CACHE = df_co_cau
        DF_AGING_CACHE = df_aging
        DF_TREO_CACHE = df_treo_filtered
        DF_TTS_CACHE = df_tts
        
        gc.collect()
        
    return DF_GTC_CACHE, DF_LTC_CACHE, DF_AGING_CACHE, DF_TREO_CACHE

def apply_filters(df, am=None, province=None, post_office=None):
    if df is None or df.empty:
        return df
        
    from flask import has_request_context, session
    if has_request_context():
        am_name = session.get('am_name')
        if am_name:
            am = am_name

    df_filtered = df.copy()
    if am:
        df_filtered = filter_df_by_logged_in_am(df_filtered, force_am_name=am)
        if df_filtered.empty:
            return df_filtered

    if province:
        prov_cols = [c for c in df_filtered.columns if str(c).strip() in ['mapped_prov', 'Tỉnh', 'province_name', 'province']]
        if prov_cols:
            col = prov_cols[0]
            if col == 'mapped_prov':
                df_filtered = df_filtered[df_filtered[col] == province]
            else:
                def match_prov(x):
                    return clean_str(x) == clean_str(province)
                df_filtered = df_filtered[df_filtered[col].apply(match_prov)]
        if df_filtered.empty:
            return df_filtered

    if post_office:
        po_cols = [c for c in df_filtered.columns if str(c).strip() in ['clean_bc', 'BC', 'warehouse_name', 'Bưu cục', 'post_office']]
        if po_cols:
            col = po_cols[0]
            if col == 'clean_bc':
                df_filtered = df_filtered[df_filtered[col] == clean_str(post_office)]
            else:
                def match_po(x):
                    return clean_str(x) == clean_str(post_office)
                df_filtered = df_filtered[df_filtered[col].apply(match_po)]

    return df_filtered

def update_all_caches():
    global OPERATIONAL_CACHE, OPR_CACHE, BACKLOG_CACHE_RAW, UNSTABLE_PO_CACHE, OFF_SPE_CACHE, CA_REPORT_CACHE, PRODUCTIVITY_REALTIME_CACHE, DF_TAO_DON_CACHE, DF_BUU_CUC_TYPE_MAP, FD_CACHE, HEAVY_10KG_CACHE
    import gc
    CA_REPORT_CACHE = None
    PRODUCTIVITY_REALTIME_CACHE = None
    
    print("--------------------------------------------------")
    print("STARTING MEMORY-EFFICIENT CACHE LOAD...")
    print("--------------------------------------------------")
    
    # 1. First trigger get_dataframes(force=True) to build DF_GTC_CACHE, DF_LTC_CACHE, DF_AGING_CACHE, DF_TREO_CACHE
    # sequentially and efficiently!
    try:
        get_dataframes(force=True)
        print("-> Pandas DataFrames loaded sequentially.")
    except Exception as e:
        err_msg = f"Loi doc file Excel: {str(e)}"
        print(err_msg)
        OPERATIONAL_CACHE = {"error": err_msg}
        OPR_CACHE = {"error": err_msg}
        BACKLOG_CACHE_RAW = {"aging": {"error": err_msg}, "treo": {"error": err_msg}}
        UNSTABLE_PO_CACHE = {"error": err_msg}
        OFF_SPE_CACHE = {"error": err_msg}
        FD_CACHE = {"error": err_msg}
        return

    # 1.5. Process FD report
    try:
        print("Parsing FD report...")
        FD_CACHE = process_fd_report()
        print("-> FD report processed and cached.")
    except Exception as e:
        FD_CACHE = {"error": f"Lỗi xử lý FD report: {e}"}

    # 2. Now process operational report using cached DataFrames
    try:
        print("Parsing Operational report...")
        # Note: process_operational_report reads file_path inside if df_gtc is None
        # We pass the cached dataframes so it doesn't need to load the file again!
        ops = process_operational_report(df_gtc=DF_GTC_CACHE, df_ltc=DF_LTC_CACHE, df_tts=DF_TTS_CACHE)
        if "error" not in ops:
            OPERATIONAL_CACHE = ops
            print("-> Operational report processed and cached.")
        else:
            OPERATIONAL_CACHE = ops
            print("-> Error processing operational report.")
    except Exception as e:
        OPERATIONAL_CACHE = {"error": f"Lỗi xử lý báo cáo vận hành: {e}"}
        

    # 3. Process OPR report
    try:
        print("Parsing OPR report...")
        raw_opr = safe_read_csv(resolve_path('opr_opr.csv', write=False))
        raw_oe = safe_read_csv(resolve_path('opr_oe.csv', write=False))
        raw_rawopr = safe_read_csv(resolve_path('opr_raw.csv', write=False))
        if raw_opr is not None and raw_oe is not None:
            opr = process_opr_report(df_opr=raw_opr, df_oe=raw_oe, df_rawopr=raw_rawopr)
            OPR_CACHE = opr
            del raw_opr, raw_oe, raw_rawopr
            print("-> OPR report processed and cached.")
        else:
            OPR_CACHE = {"error": "Không tìm thấy dữ liệu OPR CSV."}
        gc.collect()
    except Exception as e:
        OPR_CACHE = {"error": f"Lỗi xử lý OPR: {e}"}
        
    # 4. Process Backlog reports (Aging and Treo)
    try:
        print("Parsing Backlog reports...")
        # Fallback to ops_co_cau.csv automatically by passing df_co_cau=None
        aging = process_aging_backlog(df_raw=DF_AGING_CACHE, df_co_cau=None)
        treo = process_treo_backlog(df_raw=DF_TREO_CACHE, df_co_cau=None)
        
        BACKLOG_CACHE_RAW = {
            "aging": aging,
            "treo": treo
        }
        print("-> Backlog reports processed and cached.")
        gc.collect()
    except Exception as e:
        BACKLOG_CACHE_RAW = {"aging": {"error": f"Lỗi: {e}"}, "treo": {"error": f"Lỗi: {e}"}}

    # 5. Process Unstable POs
    try:
        print("Parsing Unstable POs...")
        UNSTABLE_PO_CACHE = process_unstable_po()
        gc.collect()
    except Exception as e:
        UNSTABLE_PO_CACHE = {"error": f"Lỗi: {e}"}
        
    # 6. Process OFF SPE
    try:
        print("Parsing OFF SPE...")
        OFF_SPE_CACHE = process_off_spe()
        gc.collect()
    except Exception as e:
        OFF_SPE_CACHE = {"error": f"Lỗi: {e}"}
        
    # 7. Process Volume Creation
    try:
        print("Parsing Volume Creation...")
        DF_TAO_DON_CACHE = load_vols_tao_don_df()
        DF_BUU_CUC_TYPE_MAP = load_buu_cuc_type_map()
        gc.collect()
    except Exception as e:
        print(f"Error volume: {e}")

    # 8. Process Heavy Goods >10kg
    try:
        print("Parsing Heavy Goods >10kg...")
        HEAVY_10KG_CACHE = process_heavy_10kg_report()
        gc.collect()
    except Exception as e:
        print(f"Error Heavy Goods: {e}")
        HEAVY_10KG_CACHE = {"error": f"Lỗi: {e}"}
        
    print("--------------------------------------------------")
    print("MEMORY-EFFICIENT CACHE LOAD COMPLETE.")
    print("--------------------------------------------------")
    gc.collect()
    
    global LAST_CACHE_UPDATE_TIME
    import time
    LAST_CACHE_UPDATE_TIME = time.time()


# ==========================================
# 7. API FLASK ENDPOINTS
# ==========================================
@app.route('/')
def home():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return render_template('index.html')

@app.route('/hop')
@app.route('/meeting')
@app.route('/bao-cao-hop')
@app.route('/bao-cao-tuan')
@app.route('/index.html')
@app.route('/dashboard')
def meeting_dashboard():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    response = send_from_directory(root_dir, 'index.html')
    response.headers['Cache-Control'] = 'public, max-age=60, s-maxage=300, stale-while-revalidate=600'
    return response

@app.route('/slide')
@app.route('/showcase')
def showcase_slide():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, 'showcase_presentation.html')

@app.route('/kich-ban-cod-truy-thu')
@app.route('/KICH_BAN_NOP_COD_QR_VA_TRUY_THU_W43.html')
def meeting_script_cod_truythu():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, 'KICH_BAN_NOP_COD_QR_VA_TRUY_THU_W43.html')

@app.route('/KICH_BAN_NOP_COD_QR_VA_TRUY_THU_W43.docx')
def download_cod_truythu_docx():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, 'KICH_BAN_NOP_COD_QR_VA_TRUY_THU_W43.docx', as_attachment=True)

@app.route('/kich-ban')
@app.route('/script')
@app.route('/KICH_BAN_THUYET_TRINH_W43_NAM_TRUNG_BO.html')
@app.route('/kich-ban-w43')
@app.route('/KICH_BAN_THUYET_TRINH_W42_NAM_TRUNG_BO.html')
@app.route('/kich-ban-w42')
@app.route('/KICH_BAN_THUYET_TRINH_W41_NAM_TRUNG_BO.html')
@app.route('/KICH_BAN_THUYET_TRINH_W40_NAM_TRUNG_BO.html')
@app.route('/kich-ban-w41')
@app.route('/kich-ban-w40')
@app.route('/kich-ban-w39')
@app.route('/kich-ban-w38')
def meeting_script_w38():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = "KICH_BAN_THUYET_TRINH_W41_NAM_TRUNG_BO.html"
    for f_cand in ["KICH_BAN_THUYET_TRINH_W43_NAM_TRUNG_BO.html", "KICH_BAN_THUYET_TRINH_W42_NAM_TRUNG_BO.html", "KICH_BAN_THUYET_TRINH_W41_NAM_TRUNG_BO.html", "KICH_BAN_THUYET_TRINH_W40_NAM_TRUNG_BO.html", "KICH_BAN_THUYET_TRINH_W39_NAM_TRUNG_BO.html", "KICH_BAN_THUYET_TRINH_W38_NAM_TRUNG_BO.html"]:
        if os.path.exists(os.path.join(root_dir, f_cand)):
            target_file = f_cand
            break
    response = send_from_directory(root_dir, target_file)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
def meeting_script():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    response = send_from_directory(root_dir, 'KICH_BAN_THUYET_TRINH_W37_NAM_TRUNG_BO.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/styles.css')
@app.route('/control_tower_visuals.css')
@app.route('/app.js')
@app.route('/control_tower_visuals.js')
@app.route('/data.js')
@app.route('/data.json')
@app.route('/download-doc')
@app.route('/KICH_BAN_THUYET_TRINH_W41_NAM_TRUNG_BO.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W40_NAM_TRUNG_BO.docx')
@app.route('/KICH_BAN_CANH_BAO_BUU_CUC_W38_VS_W39.docx')
@app.route('/KICH_BAN_THUYET_TRINH_MOI_NHAT.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W43_NAM_TRUNG_BO.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W42_NAM_TRUNG_BO.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W39_INSIGHT_CHUYEN_SAU_CHINH_SUA.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W39_INSIGHT_CHUYEN_SAU.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W39_NAM_TRUNG_BO.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W38_INSIGHT_CHUYEN_SAU_CHINH_SUA.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W38_INSIGHT_CHUYEN_SAU.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W38_NAM_TRUNG_BO.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W37_NAM_TRUNG_BO_MOI_NHAT.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W37_FULL_OPR_TTS.docx')
@app.route('/KICH_BAN_THUYET_TRINH_W37_NAM_TRUNG_BO.docx')
def serve_meeting_assets():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    req_file = request.path.lstrip('/')
    if req_file == 'download-doc':
        for cand in ['KICH_BAN_THUYET_TRINH_W43_NAM_TRUNG_BO.docx', 'KICH_BAN_THUYET_TRINH_W42_NAM_TRUNG_BO.docx', 'KICH_BAN_THUYET_TRINH_W41_NAM_TRUNG_BO.docx', 'KICH_BAN_THUYET_TRINH_W40_NAM_TRUNG_BO.docx', 'KICH_BAN_THUYET_TRINH_W39_NAM_TRUNG_BO.docx', 'KICH_BAN_THUYET_TRINH_W38_NAM_TRUNG_BO.docx']:
            if os.path.exists(os.path.join(root_dir, cand)):
                req_file = cand
                break
    response = send_from_directory(root_dir, req_file, as_attachment=True if req_file.endswith('.docx') else False)
    if req_file.endswith(('.css', '.js', '.png', '.jpg', '.svg', '.woff', '.woff2')):
        response.headers['Cache-Control'] = 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=86400'
    elif req_file in ['data.js', 'data.json']:
        response.headers['Cache-Control'] = 'public, max-age=60, s-maxage=300, stale-while-revalidate=600'
    else:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/sync-sheets-oauth', methods=['GET', 'POST'])
def api_sync_sheets_oauth():
    try:
        import subprocess
        root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 1. Run sync_google_sheets_oauth.py
        sync_script = os.path.join(root_dir, 'sync_google_sheets_oauth.py')
        res1 = subprocess.run([sys.executable, sync_script], cwd=root_dir, capture_output=True, text=True, timeout=120)
        
        # 2. Run build_data_js.py to refresh weekly meeting data (/hop)
        build_script = os.path.join(root_dir, 'build_data_js.py')
        if os.path.exists(build_script):
            subprocess.run([sys.executable, build_script], cwd=root_dir, capture_output=True, text=True, timeout=120)

        # 3. Enrich with auxiliary scripts (COD, Aging, Truy Thu)
        for s_name in ['parse_4_cod_tabs.py', 'calc_aging_buckets.py', 'process_truy_thu_report.py']:
            s_path = os.path.join(root_dir, 'scratch', s_name)
            if os.path.exists(s_path):
                subprocess.run([sys.executable, s_path], cwd=root_dir, capture_output=True, text=True, timeout=60)
        
        return jsonify({
            "success": True,
            "message": "Đã đồng bộ thành công toàn bộ số liệu từ Google Sheets qua OAuth 2.0 và cập nhật dữ liệu tuần mới!",
            "log": res1.stdout[-500:] if res1.stdout else ""
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sync-realtime-aging-treo', methods=['GET', 'POST'])
def api_sync_realtime_aging_treo():
    try:
        import subprocess
        root_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(root_dir, 'sync_realtime_aging_treo.py')
        res = subprocess.run([sys.executable, script_path], cwd=root_dir, capture_output=True, text=True, timeout=90)
        
        data_json_path = os.path.join(root_dir, 'data.json')
        aging_data = {}
        treo_data = {}
        if os.path.exists(data_json_path):
            with open(data_json_path, 'r', encoding='utf-8') as f:
                dj = json.load(f)
                aging_data = dj.get('aging', {})
                treo_data = dj.get('treo_lc', {})

        return jsonify({
            "success": res.returncode == 0,
            "message": "Đã cập nhật real-time dữ liệu Aging & Treo Luân Chuyển thành công!",
            "aging": aging_data,
            "treo_lc": treo_data,
            "log": res.stdout[-300:] if res.stdout else ""
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        ip = request.remote_addr
        is_ok, retry_after = check_rate_limit(f"{ip}_login", limit=10, period=60)
        if not is_ok:
            return jsonify({"error": f"Quá nhiều yêu cầu đăng nhập. Vui lòng thử lại sau {retry_after} giây."}), 429
        
        if not username or not password:
            return jsonify({"error": "Vui lòng nhập đầy đủ mã nhân viên và mật khẩu."}), 400
            
        users = load_users()
        am_name = get_am_name_by_id(username)
        
        authenticated = False
        user_role = "staff"
        
        if username in users and check_password_hash(users[username]["password"], password):
            authenticated = True
            user_role = users[username].get("role", "staff")
        elif am_name and password == "123456":
            authenticated = True
            user_role = "am"
            
        if authenticated:
            session.clear()
            session['username'] = username
            session['role'] = user_role
            if am_name:
                session['am_name'] = am_name
                session['role'] = 'am'
            
            perms = get_user_permissions(username)
            session['permissions'] = perms
            session.permanent = True
            
            # Generate CSRF token
            session['csrf_token'] = secrets.token_hex(32)
            
            return jsonify({
                "success": True,
                "username": username,
                "role": session['role'],
                "permissions": perms,
                "csrf_token": session['csrf_token']
            })
        return jsonify({"error": "Sai mã nhân viên hoặc mật khẩu."}), 401
    except Exception as e:
        return jsonify({"error": f"Lỗi đăng nhập: {str(e)}"}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Đăng xuất thành công."})

@app.route('/api/users', methods=['GET', 'POST'])
@requires_permission('tab-sync', 'edit')
def api_users():
    if not is_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
        
    users = load_users()
    
    if request.method == 'GET':
        users_list = []
        for uname, udata in users.items():
            users_list.append({
                "username": udata["username"],
                "role": udata.get("role", "staff"),
                "permissions": get_user_permissions(uname)
            })
        return jsonify(users_list)
        
    elif request.method == 'POST':
        data = request.json or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        role = data.get("role", "staff").strip()
        permissions = data.get("permissions", {})
        
        if not username:
            return jsonify({"error": "Username không được để trống."}), 400
            
        if username not in users and not password:
            return jsonify({"error": "Mật khẩu không được để trống khi tạo mới user."}), 400
            
        if username in users:
            users[username]["role"] = role
            users[username]["permissions"] = permissions
            if password:
                users[username]["password"] = generate_password_hash(password, method="pbkdf2:sha256")
        else:
            users[username] = {
                "username": username,
                "password": generate_password_hash(password, method="pbkdf2:sha256"),
                "role": role,
                "permissions": permissions
            }
            
        save_users(users)
        return jsonify({"success": True, "message": f"User {username} đã được lưu thành công."})

@app.route('/api/users/<username>', methods=['DELETE'])
@requires_permission('tab-sync', 'delete')
def api_delete_user(username):
    if not is_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
        
    current_user = session.get('username')
    if not current_user:
        auth = request.authorization
        if auth:
            current_user = auth.username
            
    if current_user == username:
        return jsonify({"error": "Không thể tự xóa chính mình."}), 400
        
    users = load_users()
    if username not in users:
        return jsonify({"error": "User không tồn tại."}), 404
        
    admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
    if users[username].get("role") == "admin" and admin_count <= 1:
        return jsonify({"error": "Không thể xóa admin duy nhất của hệ thống."}), 400
        
    del users[username]
    save_users(users)
    return jsonify({"success": True, "message": f"User {username} đã được xóa."})

@app.route('/api/roles', methods=['GET'])
@requires_permission('tab-sync', 'view')
def api_get_roles():
    if not is_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
    roles = load_roles()
    return jsonify(roles)

@app.route('/api/roles', methods=['POST'])
@requires_permission('tab-sync', 'edit')
def api_save_role():
    if not is_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
    data = request.json or {}
    role_id = data.get("role_id", "").strip().lower()
    role_name = data.get("name", "").strip()
    role_desc = data.get("description", "").strip()
    permissions = data.get("permissions", {})
    
    if not role_id:
        return jsonify({"error": "Mã vai trò không được để trống."}), 400
    if not role_name:
        return jsonify({"error": "Tên vai trò không được để trống."}), 400
        
    roles = load_roles()
    roles[role_id] = {
        "name": role_name,
        "description": role_desc,
        "permissions": permissions
    }
    save_roles(roles)
    return jsonify({"success": True, "message": f"Vai trò '{role_name}' đã được lưu."})

@app.route('/api/roles/<role_id>', methods=['DELETE'])
@requires_permission('tab-sync', 'delete')
def api_delete_role(role_id):
    if not is_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
    
    role_id = role_id.strip().lower()
    if role_id in ['admin', 'staff', 'am']:
        return jsonify({"error": "Không thể xóa vai trò hệ thống mặc định."}), 400
        
    roles = load_roles()
    if role_id not in roles:
        return jsonify({"error": "Vai trò không tồn tại."}), 404
        
    del roles[role_id]
    save_roles(roles)
    
    users = load_users()
    changed = False
    for uname, udata in users.items():
        if udata.get("role") == role_id:
            udata["role"] = "staff"
            changed = True
    if changed:
        save_users(users)
        
    return jsonify({"success": True, "message": f"Vai trò '{role_id}' đã được xóa."})

@app.route('/api/staff-list', methods=['GET'])
@requires_permission('tab-sync', 'view')
def api_get_staff_list():
    if not is_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
    try:
        ns_path = resolve_path('ops_nhan_su.csv', write=False)
        df_ns = safe_read_csv(ns_path)
        if df_ns is None or df_ns.empty:
            return jsonify([])
            
        df_ns.columns = [c.strip() for c in df_ns.columns]
        
        status_col = next((c for c in df_ns.columns if str(c).strip().lower() in ['trạng thái', 'trang thai', 'status']), None)
        active_mask = (df_ns[status_col].astype(str).str.strip().isin(["Đang làm việc", "dang lam viec"])) if status_col else pd.Series(True, index=df_ns.index)
        if 'Vùng' in df_ns.columns:
            active_mask &= (df_ns['Vùng'].astype(str).str.strip() == "NTB")
            
        active_df = df_ns[active_mask].copy()
        
        users = load_users()
        staff_list = []
        for _, row in active_df.iterrows():
            eid = str(row['ID']).strip()
            name = str(row['Tên nhân viên']).strip()
            chuc_vu = str(row['Chức vụ']).strip()
            
            user_info = users.get(eid, {})
            current_role = user_info.get("role", "")
            if not current_role:
                if get_am_name_by_id(eid) is not None:
                    current_role = "am"
                    
            staff_list.append({
                "id": eid,
                "name": name,
                "chuc_vu": chuc_vu,
                "role": current_role
            })
            
        staff_list.sort(key=lambda x: x["name"])
        return jsonify(staff_list)
    except Exception as e:
        print(f"Error reading staff list: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/assign-role', methods=['POST'])
@requires_permission('tab-sync', 'edit')
def api_assign_role():
    if not is_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
        
    data = request.json or {}
    employee_id = str(data.get("employee_id", "")).strip()
    role = str(data.get("role", "")).strip().lower()
    
    if not employee_id:
        return jsonify({"error": "Mã nhân viên không được để trống."}), 400
        
    users = load_users()
    
    if not role or role == "none":
        if employee_id in users:
            if users[employee_id].get("role") == "admin":
                admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
                if admin_count <= 1:
                    return jsonify({"error": "Không thể gỡ vai trò của admin duy nhất."}), 400
            del users[employee_id]
            save_users(users)
        return jsonify({"success": True, "message": "Đã gỡ vai trò của nhân viên thành công."})
        
    roles = load_roles()
    if role not in roles:
        return jsonify({"error": "Vai trò không hợp lệ hoặc không tồn tại."}), 400
        
    if employee_id in users:
        users[employee_id]["role"] = role
    else:
        users[employee_id] = {
            "username": employee_id,
            "password": generate_password_hash("123456", method="pbkdf2:sha256"),
            "role": role,
            "permissions": {}
        }
        
    save_users(users)
    return jsonify({"success": True, "message": f"Đã gán vai trò '{roles[role]['name']}' cho nhân viên {employee_id}."})

@app.route('/api/reset-password', methods=['POST'])
@requires_permission('tab-sync', 'edit')
def api_reset_password():
    if not is_admin():
        return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
        
    data = request.json or {}
    employee_id = str(data.get("employee_id", "")).strip()
    
    if not employee_id:
        return jsonify({"error": "Mã nhân viên không được để trống."}), 400
        
    users = load_users()
    if employee_id not in users:
        return jsonify({"error": "Nhân viên chưa được khởi tạo tài khoản (chưa gán vai trò)."}), 404
        
    users[employee_id]["password"] = generate_password_hash("123456", method="pbkdf2:sha256")
    save_users(users)
    return jsonify({"success": True, "message": f"Đã đặt lại mật khẩu cho nhân viên {employee_id} về mặc định '123456'."})

@app.route('/api/unstable-po')
@requires_permission('tab-unstable-po')
def get_unstable_po():
    am = request.args.get('am')
    province = request.args.get('province')
    post_office = request.args.get('post_office')
    
    if session.get('am_name'):
        am = session.get('am_name')
        
    if am or province or post_office:
        return jsonify(process_unstable_po(am=am, province=province, post_office=post_office))
        
    global UNSTABLE_PO_CACHE
    if UNSTABLE_PO_CACHE is None:
        with CACHE_LOCK:
            if UNSTABLE_PO_CACHE is None:
                UNSTABLE_PO_CACHE = process_unstable_po()
    return jsonify(UNSTABLE_PO_CACHE)

@app.route('/api/off-spe')
@requires_permission('tab-off-spe')
def get_off_spe():
    am = request.args.get('am')
    province = request.args.get('province')
    post_office = request.args.get('post_office')
    
    if session.get('am_name'):
        am = session.get('am_name')
        
    if am or province or post_office:
        return jsonify(process_off_spe(am=am, province=province, post_office=post_office))
        
    global OFF_SPE_CACHE
    if OFF_SPE_CACHE is None:
        with CACHE_LOCK:
            if OFF_SPE_CACHE is None:
                OFF_SPE_CACHE = process_off_spe()
    return jsonify(OFF_SPE_CACHE)


@app.route('/api/ca-report')
def api_ca_report():
    global CA_REPORT_CACHE
    if CA_REPORT_CACHE is None or (isinstance(CA_REPORT_CACHE, dict) and "error" in CA_REPORT_CACHE):
        with CACHE_LOCK:
            res = process_ca_report()
            if not ("error" in res and CA_REPORT_CACHE and "error" not in CA_REPORT_CACHE):
                CA_REPORT_CACHE = res
    return jsonify(clean_nan(CA_REPORT_CACHE))

def process_productivity_realtime():
    # Load from DB or CSV file via safe_read_csv (which checks /tmp, DB, and local file)
    df = None
    try:
        csv_path = resolve_path('ops_productivity_realtime.csv', write=False)
        df = safe_read_csv(csv_path, header=None)
    except Exception as e:
        print(f"safe_read_csv error for ops_productivity_realtime: {e}")
        
    if df is None or df.empty:
        df = load_df_from_db('ops_productivity_realtime.csv')
        
    if df is None or df.empty:
        csv_path = resolve_path('ops_productivity_realtime.csv', write=False)
        if os.path.exists(csv_path):
            try:
                for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(csv_path, header=None, encoding=enc)
                        break
                    except Exception:
                        continue
            except Exception as e:
                return {"error": f"Lỗi đọc file: {str(e)}"}
        else:
            return {"error": "Không tìm thấy dữ liệu năng suất. Vui lòng đồng bộ lại."}
            
    if df is None or df.empty:
        return {"error": "Không tìm thấy dữ liệu năng suất. Vui lòng đồng bộ lại."}
            
    # Check if headers are in the column names of df
    col_names = [str(c).strip().lower() for c in df.columns]
    if 'bưu cục' in col_names and 'mã nv' in col_names and 'nhân viên' in col_names:
        table_df = df.iloc[:, 0:9].copy()
        table_df.columns = df.columns[0:9]
    else:
        # Search for headers in the rows
        header_idx = None
        for idx, row in df.iterrows():
            row_vals = [str(x).strip().lower() for x in row.values]
            if 'bưu cục' in row_vals and 'mã nv' in row_vals and 'nhân viên' in row_vals:
                header_idx = idx
                break
        if header_idx is not None:
            headers = df.iloc[header_idx].values
            table_df = df.iloc[header_idx + 1:, 0:9].copy()
            table_df.columns = headers[0:9]
        else:
            return {"error": "Không tìm thấy cấu trúc bảng dữ liệu (Bưu Cục, Mã NV, Nhân Viên)."}

    # Clean headers and drop rows where 'Bưu Cục' or 'Mã NV' is NaN/null or blank
    table_df.rename(columns=lambda x: str(x).strip(), inplace=True)
    table_df = table_df.dropna(subset=['Bưu Cục', 'Mã NV'])
    table_df = table_df[table_df['Bưu Cục'].astype(str).str.strip() != '']
    table_df = table_df[table_df['Mã NV'].astype(str).str.strip() != '']
    
    # Fill NA values
    table_df = table_df.fillna({
        'AM': 'Không xác định',
        'Nhân Viên': 'Không xác định',
        'Gán Giao': 0,
        'Giao TC': 0,
        '%GTC': '0%',
        'LTC': 0,
        'Đánh Giá': 'Chưa đánh giá'
    })
    
    records = []
    for _, row in table_df.iterrows():
        try:
            gan_giao = int(float(str(row['Gán Giao']).replace(',', '').replace('%', '').strip() or 0))
        except:
            gan_giao = 0
            
        try:
            giao_tc = int(float(str(row['Giao TC']).replace(',', '').replace('%', '').strip() or 0))
        except:
            giao_tc = 0
            
        try:
            ltc = int(float(str(row['LTC']).replace(',', '').replace('%', '').strip() or 0))
        except:
            ltc = 0
            
        gtc_str = str(row['%GTC']).strip()
        try:
            gtc_val = float(gtc_str.replace('%', '').strip())
        except:
            gtc_val = 0.0
            
        records.append({
            'Bưu Cục': str(row['Bưu Cục']).strip(),
            'AM': str(row['AM']).strip(),
            'Mã NV': str(row['Mã NV']).strip(),
            'Nhân Viên': str(row['Nhân Viên']).strip(),
            'Gán Giao': gan_giao,
            'Giao TC': giao_tc,
            '%GTC': gtc_str,
            'GTC_Val': gtc_val,
            'LTC': ltc,
            'Đánh Giá': str(row['Đánh Giá']).strip()
        })
        
    return {"records": records}

@app.route('/api/productivity-realtime')
@requires_permission('tab-productivity-realtime')
def api_productivity_realtime():
    global PRODUCTIVITY_REALTIME_CACHE
    if PRODUCTIVITY_REALTIME_CACHE is None or (isinstance(PRODUCTIVITY_REALTIME_CACHE, dict) and "error" in PRODUCTIVITY_REALTIME_CACHE):
        with CACHE_LOCK:
            res = process_productivity_realtime()
            if not ("error" in res and PRODUCTIVITY_REALTIME_CACHE and "error" not in PRODUCTIVITY_REALTIME_CACHE):
                PRODUCTIVITY_REALTIME_CACHE = res
    return jsonify(clean_nan(PRODUCTIVITY_REALTIME_CACHE))

@app.route('/api/fd')
@requires_permission('tab-fd')
def get_fd():
    am = request.args.get('am')
    province = request.args.get('province')
    post_office = request.args.get('post_office')
    
    if session.get('am_name'):
        am = session.get('am_name')
        
    if am or province or post_office:
        return jsonify(clean_nan(process_fd_report(am=am, province=province, post_office=post_office)))
        
    global FD_CACHE
    with CACHE_LOCK:
        if FD_CACHE is None:
            FD_CACHE = process_fd_report()
    return jsonify(clean_nan(FD_CACHE))

@app.route('/api/operational')
@requires_permission('tab-operational')
def get_operational():
    global OPERATIONAL_CACHE, DF_GTC_CACHE, DF_LTC_CACHE, DF_TTS_CACHE
    am = request.args.get('am')
    province = request.args.get('province')
    po = request.args.get('po')
    date = request.args.get('date')
    
    if session.get('am_name'):
        am = session.get('am_name')
    
    if am or province or po or date:
        df_gtc = DF_GTC_CACHE if DF_GTC_CACHE is not None else None
        df_ltc = DF_LTC_CACHE if DF_LTC_CACHE is not None else None
        df_tts = DF_TTS_CACHE if DF_TTS_CACHE is not None else None
        
        ops = process_operational_report(
            df_gtc=df_gtc,
            df_ltc=df_ltc,
            df_tts=df_tts,
            am=am,
            province=province,
            po=po,
            date=date
        )
        return jsonify(clean_nan(ops))
        
    with CACHE_LOCK:
        if OPERATIONAL_CACHE is None:
            OPERATIONAL_CACHE = process_operational_report()
    return jsonify(clean_nan(OPERATIONAL_CACHE))

@app.route('/api/opr')
@requires_permission('tab-opr')
def get_opr():
    am = request.args.get('am')
    province = request.args.get('province')
    post_office = request.args.get('post_office')
    
    if session.get('am_name'):
        am = session.get('am_name')
    
    if am or province or post_office:
        # Dynamically compute OPR report with filters applied
        filtered_report = process_opr_report(am=am, province=province, post_office=post_office)
        return jsonify(clean_nan(filtered_report))
        
    global OPR_CACHE
    with CACHE_LOCK:
        if OPR_CACHE is None:
            OPR_CACHE = process_opr_report()
    return jsonify(clean_nan(OPR_CACHE))

@app.route('/api/backlog')
@requires_permission('tab-backlog')
def get_backlog():
    am = request.args.get('am')
    province = request.args.get('province')
    post_office = request.args.get('post_office')
    
    if session.get('am_name'):
        am = session.get('am_name')
        
    if am or province or post_office:
        aging = process_aging_backlog(am=am, province=province, post_office=post_office)
        treo = process_treo_backlog(am=am, province=province, post_office=post_office)
        current_data = {
            "aging": aging,
            "treo": treo
        }
    else:
        global BACKLOG_CACHE_RAW
        with CACHE_LOCK:
            if BACKLOG_CACHE_RAW is None:
                aging = process_aging_backlog()
                treo = process_treo_backlog()
                BACKLOG_CACHE_RAW = {
                    "aging": aging,
                    "treo": treo
                }
        import copy
        current_data = copy.deepcopy(BACKLOG_CACHE_RAW)
        
    if "error" in current_data["aging"]:
        return jsonify({"error": current_data["aging"]["error"]})
    if "error" in current_data["treo"]:
        return jsonify({"error": current_data["treo"]["error"]})
        
    history = load_history()
    baseline_ts = request.args.get("baseline")
    baseline_entry = None
    
    if history:
        if baseline_ts:
            for entry in history:
                if entry["timestamp"] == baseline_ts:
                    baseline_entry = entry
                    break
        else:
            if len(history) >= 2:
                baseline_entry = history[-2]
            else:
                baseline_entry = history[-1]
                
    current_data["baseline_timestamp"] = baseline_entry["timestamp"] if baseline_entry else None
    current_data = calculate_trend(current_data, baseline_entry)
    
    return jsonify(clean_nan(current_data))

@app.route('/api/history')
@requires_permission('tab-backlog')
def get_history():
    history = load_history()
    timestamps = [entry["timestamp"] for entry in history]
    return jsonify(timestamps[::-1])

@app.route('/api/user-role')
@requires_auth
def get_user_role():
    username = session.get('username')
    if not username and request.authorization:
        username = request.authorization.username
    role = session.get('role', 'staff')
    if get_am_name_by_id(username):
        role = 'am'
    permissions = get_user_permissions(username)
    return jsonify({"username": username, "role": role, "permissions": permissions})

def mask_url(url):
    if not url:
        return ""
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        return url
    spreadsheet_id = match.group(1)
    if len(spreadsheet_id) > 10:
        masked_id = spreadsheet_id[:4] + "****************" + spreadsheet_id[-4:]
    else:
        masked_id = "********"
    masked_url = url.replace(spreadsheet_id, masked_id)
    return masked_url

def mask_token(token):
    if not token:
        return ""
    if len(token) > 8:
        return token[:4] + "****************" + token[-4:]
    return "********"

@app.route('/api/config', methods=['GET', 'POST'])
@requires_permission('tab-sync')
def manage_config():
    if request.method == 'POST':
        if not is_admin():
            return jsonify({"error": "Quyền truy cập bị từ chối. Chỉ tài khoản admin mới được phép lưu cấu hình."}), 403
        try:
            data = request.json or {}
            current_config = load_config()
            
            config = {}
            if "consolidated_url" in data:
                val = data.get("consolidated_url", "").strip()
                if not val:
                    config["consolidated_url"] = ""
                elif "*" in val or "Ẩn" in val or "hidden" in val.lower():
                    config["consolidated_url"] = current_config.get("consolidated_url", "")
                else:
                    if not (val.startswith("https://docs.google.com/spreadsheets/") or val.startswith("http://docs.google.com/spreadsheets/")):
                        return jsonify({"error": "Link Google Sheet không hợp lệ cho consolidated_url. Phải bắt đầu bằng https://docs.google.com/spreadsheets/"}), 400
                    if not is_allowed_spreadsheet_url(val):
                        return jsonify({"error": "Spreadsheet ID không nằm trong danh sách được cho phép (SSRF Prevention)."}), 400
                    config["consolidated_url"] = val
            else:
                config["consolidated_url"] = current_config.get("consolidated_url", "")

            # Parse Telegram Bot Token
            if "telegram_bot_token" in data:
                val_token = data.get("telegram_bot_token", "").strip()
                if not val_token:
                    config["telegram_bot_token"] = ""
                elif "*" in val_token or "hidden" in val_token.lower():
                    config["telegram_bot_token"] = current_config.get("telegram_bot_token", "")
                else:
                    config["telegram_bot_token"] = val_token
            else:
                config["telegram_bot_token"] = current_config.get("telegram_bot_token", "")

            # Parse Telegram Chat ID
            if "telegram_chat_id" in data:
                config["telegram_chat_id"] = data.get("telegram_chat_id", "").strip()
            else:
                config["telegram_chat_id"] = current_config.get("telegram_chat_id", "")

            # Parse Gemini API Key
            if "gemini_api_key" in data:
                val_gemini = data.get("gemini_api_key", "").strip()
                if not val_gemini:
                    config["gemini_api_key"] = ""
                elif "*" in val_gemini or "hidden" in val_gemini.lower():
                    config["gemini_api_key"] = current_config.get("gemini_api_key", "")
                else:
                    config["gemini_api_key"] = val_gemini
            else:
                config["gemini_api_key"] = current_config.get("gemini_api_key", "")
            
            if save_config(config):
                masked_config = {
                    "consolidated_url": mask_url(config.get("consolidated_url", "")),
                    "telegram_bot_token": mask_token(config.get("telegram_bot_token", "")),
                    "telegram_chat_id": config.get("telegram_chat_id", ""),
                    "gemini_api_key": mask_token(config.get("gemini_api_key", ""))
                }
                return jsonify({"success": True, "config": masked_config})
            else:
                return jsonify({"error": "Không thể ghi cấu hình."}), 500
        except Exception as e:
            return jsonify({"error": f"Lỗi xử lý yêu cầu: {str(e)}"}), 400
    else:
        config = load_config()
        masked_config = {
            "consolidated_url": mask_url(config.get("consolidated_url", "")),
            "telegram_bot_token": mask_token(config.get("telegram_bot_token", "")),
            "telegram_chat_id": config.get("telegram_chat_id", ""),
            "gemini_api_key": mask_token(config.get("gemini_api_key", ""))
        }
        return jsonify(masked_config)

@app.route('/api/download-template', methods=['GET'])
@requires_permission('tab-sync')
def download_template():
    from flask import send_from_directory
    filename = request.args.get('filename', '').strip()
    allowed_files = [
        'ops_gtc.csv',
        'ops_ltc.csv',
        'ops_co_cau.csv',
        'opr_opr.csv',
        'opr_oe.csv',
        'opr_raw.csv',
        'aging_raw.csv',
        'treo_stuck.csv',
        'buu_cuc_bat_on.csv',
        'off_tuyen_spe.csv',
        'vols_tao_don.csv',
        'co_cau_ntb.csv'
    ]
    if filename not in allowed_files:
        return jsonify({"error": "Tên file không hợp lệ."}), 400
        
    try:
        filepath = resolve_path(filename, write=False)
        if not os.path.exists(filepath):
            headers_map = {
                'ops_gtc.csv': 'Cấp Quản Lý,Chi tiết,Loại Hàng,Time,Volume,% Gán,% GTC,% Chuyển trả,Leadtime,AM,Tỉnh',
                'ops_ltc.csv': 'Cấp quản lý,Chi tiết,Ca,Time,Volume,%LTC,%LC,%Gán,Leadtime',
                'ops_co_cau.csv': 'BC,Bưu cục,AM,Tỉnh',
                'opr_opr.csv': 'NgayLTC,vol_ltc,ot,khung_gio_tao_don,ly_do_tre_12h,AM',
                'opr_oe.csv': 'tutinh,kholay,sellername,khung_gio_tao_don,ly_do_tre_12h,madh,AM',
                'opr_raw.csv': 'NgayLTC,vol_ltc,ot,khung_gio_tao_don,ly_do_tre_12h,AM',
                'aging_raw.csv': 'Tỉnh,BC,Mã đơn,Tệp khách,Số ngày đã nhập BC,Số lần giao,am_name,Trạng thái',
                'treo_stuck.csv': 'warehouse_name,Mã đơn hàng,Loại đơn,Thời gian tồn đọng,am_name,province_name,Trạng thái',
                'buu_cuc_bat_on.csv': 'kho_giao_id,kho_giao_name,tinh_giao,BL LM,BL LM >5 ngay,%BL LM >5 ngay,BL KTC,BL KTC cung tinh,%BL KTC cung tinh,du_kien_clear_ton,ly_do_bat_on,trang_thai',
                'off_tuyen_spe.csv': 'tỉnh,huyện,phường,bưu cục,kết quả,cap,% time off,tg mở,ghi chú',
                'vols_tao_don.csv': 'Date,Province,buu_cuc,bat_on,Vol_Shopee_Tiktok,Vol_LTC_Ontime_Shopee_Tiktok,OPR_Shopee_Tiktok',
                'co_cau_ntb.csv': 'warehouse_id,Bưu cục,AM,Tỉnh'
            }
            if filename in headers_map:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8-sig') as f:
                    f.write(headers_map[filename] + "\n")
        
        directory = os.path.dirname(filepath)
        name = os.path.basename(filepath)
        return send_from_directory(directory, name, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Không thể tải file: {str(e)}"}), 500

@app.route('/api/upload', methods=['POST'])
@requires_permission('tab-sync')
def upload_file():
    global OPERATIONAL_CACHE, OPR_CACHE, BACKLOG_CACHE_RAW
    if 'file' not in request.files:
        return jsonify({"error": "Không tìm thấy file trong yêu cầu."}), 400
        
    file = request.files['file']
    filename = request.form.get('filename', '').strip()
    
    if not filename:
        return jsonify({"error": "Không xác định được tên file đích."}), 400
        
    allowed_files = [
        'ops_gtc.csv',
        'ops_ltc.csv',
        'ops_co_cau.csv',
        'ops_tts.csv',
        'opr_opr.csv',
        'opr_oe.csv',
        'opr_raw.csv',
        'aging_raw.csv',
        'treo_stuck.csv',
        'buu_cuc_bat_on.csv',
        'off_tuyen_spe.csv',
        'vols_tao_don.csv',
        'co_cau_ntb.csv',
        'ODR TTS.csv',
        'ops_fd.csv',
        'ops_productivity_realtime.csv',
        'ops_nhan_su.csv'
    ]
    
    if filename not in allowed_files:
        return jsonify({"error": "Tên file không hợp lệ."}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Định dạng file không hợp lệ. Chỉ hỗ trợ file CSV (.csv)."}), 400
        
    try:
        filepath = resolve_path(filename, write=True)
        file.save(filepath)
        
        # Save to DB so other serverless instances can read it
        try:
            for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    save_df_to_db(df, filename)
                    break
                except Exception:
                    continue
        except Exception as e:
            print(f"Error saving uploaded CSV {filename} to DB: {e}")
            
        # Update metadata timestamp in DB so other instances invalidate their cache
        try:
            import time
            save_json_to_db({"last_sync_time": time.time()}, "sync_metadata.json")
        except Exception as e:
            print(f"Error saving sync metadata to DB: {e}")
            
        update_all_caches()
        if BACKLOG_CACHE_RAW and "error" not in BACKLOG_CACHE_RAW["aging"] and "error" not in BACKLOG_CACHE_RAW["treo"]:
            add_to_history(BACKLOG_CACHE_RAW["aging"], BACKLOG_CACHE_RAW["treo"])
                
        return jsonify({"success": True, "message": f"Tải lên và đồng bộ file {filename} thành công!"})
    except Exception as e:
        return jsonify({"error": f"Lỗi lưu file hoặc cập nhật cache: {str(e)}"}), 500

SYNC_STATUS = {
    "status": "idle",
    "progress": "",
    "error": None,
    "timestamp": None
}

def extract_and_save_user_cocau(df):
    """
    Helper to map user sheet cocau dataframe to co_cau_ntb.csv/ops_co_cau.csv format
    """
    try:
        import pandas as pd
        import unicodedata
        
        # Clean column names (strip BOM, whitespaces, lowercase, NFC normalize)
        df.columns = [unicodedata.normalize('NFC', str(c).replace('\ufeff', '').strip().lower()) for c in df.columns]
        
        # Columns in cocau: 'Mã bưu cục', 'Bưu cục', 'BC', 'Tỉnh', 'Am', 'ID - Họ Tên Am'
        # Check if columns exist using cleaned names
        ma_bc_col = next((c for c in df.columns if c == 'mã bưu cục'), None)
        bc_name_col = next((c for c in df.columns if c == 'bưu cục'), None)
        bc_short_col = next((c for c in df.columns if c == 'bc'), None)
        tinh_col = next((c for c in df.columns if c == 'tỉnh'), None)
        am_col = next((c for c in df.columns if c in ['am', 'am_name', 'quản lý', 'họ tên am']), None)
        
        if ma_bc_col is None or am_col is None:
            print(f"Error mapping user cocau sheet: 'mã bưu cục' or 'am' columns not found. Found columns: {df.columns.tolist()}")
            return False
            
        df_mapped = pd.DataFrame()
        df_mapped['warehouse_id'] = df[ma_bc_col]
        df_mapped['Bưu cục'] = df[bc_name_col] if bc_name_col else df[ma_bc_col]
        df_mapped['BC'] = df[bc_short_col] if bc_short_col else df_mapped['Bưu cục']
        df_mapped['Tỉnh'] = df[tinh_col] if tinh_col else 'Lâm Đồng'
        df_mapped['AM'] = df[am_col].astype(str).str.strip().apply(lambda x: unicodedata.normalize('NFC', x))
        
        for target_csv in ['ops_co_cau.csv', 'co_cau_ntb.csv']:
            csv_path = resolve_path(target_csv, write=True)
            df_mapped.to_csv(csv_path, index=False, encoding='utf-8-sig')
            save_df_to_db(df_mapped, target_csv)
            
        print("Successfully extracted and saved cocau structure mapping!")
        return True
    except Exception as e:
        print(f"Error mapping user cocau sheet: {e}")
        return False

def split_excel_to_csvs(xlsx_path):
    print(f"Splitting {xlsx_path} to CSV files using optimized openpyxl...")
    import openpyxl
    import csv
    import pandas as pd
    try:
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        sheet_names = wb.sheetnames
        sheet_names_lower = [s.strip().lower() for s in sheet_names]
        
        sheet_mappings = [
            (["data"], "ops_gtc.csv"),
            (["dataltc", "rawltc", "data ltc"], "ops_ltc.csv"),
            (["cocauvung", "cơ cấu", "co_cau", "co cau"], "ops_co_cau.csv"),
            (["cocauvung", "cơ cấu", "co_cau", "co cau"], "co_cau_ntb.csv"),
            (["tts"], "ops_tts.csv"),
            (["opr"], "opr_opr.csv"),
            (["raw n-1", "oe_madh", "raw_n-1", "raw n - 1", "oe madh"], "opr_oe.csv"),
            (["rawopr"], "opr_raw.csv"),
            (["aging trên 5 ngày", "aging tren 5 ngay", "đơn giao aging trên 5 ngày", "don giao aging tren 5 ngay"], "aging_raw.csv"),
            (["treo lc", "stuck", "treo luân chuyển", "treo luan chuyen"], "treo_stuck.csv"),
            (["ntb", "bất ổn", "bat_on", "cảnh báo"], "buu_cuc_bat_on.csv"),
            (["đang off", "dang off", "off", "off_tuyen", "off tuyến"], "off_tuyen_spe.csv"),
            (["shopee_tiktok", "tao_don", "tạo đơn"], "vols_tao_don.csv"),
            (["odr tts", "odr_tts"], "ODR TTS.csv"),
            (["baocao", "báo cáo"], "ops_productivity_realtime.csv"),
            (["nhân sự", "nhan su"], "ops_nhan_su.csv"),
            (["sl > 10kg", "sl >10kg", "sl>10kg", "sl 10kg", "hàng nặng > 10kg", "hang nang > 10kg", "sl", "sản lượng"], "ops_heavy_10kg.csv"),
            (["trên10kg", "tren10kg", "trên 10kg", "tren 10kg", "treen10kg", "treen 10kg", "tạo đơn 10kg", "tao don 10kg"], "ops_tao_don_10kg.csv"),
            (["trên10kg", "tren10kg", "trên 10kg", "tren 10kg", "10kg", "hàng 10kg"], "raw_tren10kg.csv")
        ]
        
        # Check if the excel contains a dedicated user sheet style 'cocau' tab
        # (This is different from 'cocauvung' as it has short names & columns like 'Mã bưu cục' / 'Am')
        has_user_cocau_sheet = 'cocau' in sheet_names_lower
        
        if has_user_cocau_sheet:
            print("Found user-defined 'cocau' sheet. Excluding from generic split mapping.")
            sheet_mappings = [m for m in sheet_mappings if m[1] not in ["ops_co_cau.csv", "co_cau_ntb.csv"]]
            
        for candidates, target_csv in sheet_mappings:
            matched_sheet = None
            for c in candidates:
                if c in sheet_names_lower:
                    idx = sheet_names_lower.index(c)
                    matched_sheet = sheet_names[idx]
                    break
            
            if matched_sheet:
                safe_name = matched_sheet.encode('ascii', 'backslashreplace').decode('ascii')
                print(f"Extracting '{safe_name}' -> {target_csv}...")
                sheet = wb[matched_sheet]
                csv_path = resolve_path(target_csv, write=True)
                with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    for row in sheet.iter_rows(values_only=True):
                        # Filter out completely empty rows
                        if not any(x is not None for x in row):
                            continue
                        writer.writerow(row)
                try:
                    df = pd.read_csv(csv_path)
                    save_df_to_db(df, target_csv)
                except Exception as e:
                    print(f"Error saving split sheet {target_csv} to DB: {e}")
            else:
                print(f"Warning: sheet for {target_csv} not found in Excel workbook.")
        wb.close()
        try:
            split_raw_tren10kg()
        except Exception as e:
            print(f"Error splitting raw_tren10kg in split_excel_to_csvs: {e}")
        
        # If user cocau sheet exists, read it with pandas and map/save it properly
        if has_user_cocau_sheet:
            idx = sheet_names_lower.index('cocau')
            matched_sheet = sheet_names[idx]
            print(f"Extracting user-style structure sheet '{matched_sheet}' using pandas...")
            try:
                df_cocau = pd.read_excel(xlsx_path, sheet_name=matched_sheet)
                extract_and_save_user_cocau(df_cocau)
            except Exception as e:
                print(f"Error extracting user-style structure sheet: {e}")
                
        return True
    except Exception as e:
        print(f"Error splitting Excel to CSVs: {e}")
        import traceback
        traceback.print_exc()
        return False



def sync_sheets_directly_as_csv(url):
    import urllib.request
    import re
    import concurrent.futures
    import time
    
    if not url or not url.strip():
        return False, "Không có link Google Sheet."
        
    url = url.strip()
    if not is_allowed_spreadsheet_url(url):
        return False, "Spreadsheet ID không nằm trong danh sách được cho phép (SSRF Prevention)."
        
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        return False, "Không tìm thấy Spreadsheet ID hợp lệ trong link."
    spreadsheet_id = match.group(1)
    
    edit_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    headers = get_google_auth_headers()
    print(f"Fetching edit HTML to extract GIDs from: {edit_url}")
    try:
        r_edit = requests.get(edit_url, headers=headers, timeout=20)
        if r_edit.status_code == 401 and 'Authorization' in headers:
            print("HTTP 401 with Auth header, retrying without Auth header...")
            r_edit = requests.get(edit_url, headers={'User-Agent': headers.get('User-Agent', '')}, timeout=20)
        if r_edit.status_code == 200:
            html = r_edit.text
        elif r_edit.status_code == 401:
            return False, "Google Sheet riêng tư (HTTP 401 Unauthorized). Vui lòng đổi quyền chia sẻ Google Sheet sang 'Bất kỳ ai có liên kết đều có thể xem' (Anyone with link can view)."
        else:
            return False, f"Lỗi truy cập link Google Sheet (HTTP {r_edit.status_code})"
    except Exception as e:
        return False, f"Lỗi truy cập link Google Sheet: {str(e)}"
        
    pattern = r'\[\s*\d+\s*,\s*0\s*,\s*\\"?(\d+)\\"?\s*,\s*\[\s*\{\s*\\"?1\\"?\s*:\s*\[\s*\[\s*0\s*,\s*0\s*,\s*\\"?([^\\"\(\]]+)\\"?'
    matches = re.findall(pattern, html)
    if not matches:
        return False, "Không tìm thấy danh sách sheet (GIDs) trong HTML."
        
    gid_map = {}
    for gid, name in matches:
        norm_name = unicodedata.normalize('NFC', name.strip().lower())
        gid_map[norm_name] = gid
        
    sheet_mappings = [
        (["data"], "ops_gtc.csv"),
        (["dataltc", "rawltc", "data ltc"], "ops_ltc.csv"),
        (["cocauvung", "cơ cấu", "co_cau", "co cau"], "ops_co_cau.csv"),
        (["cocauvung", "cơ cấu", "co_cau", "co cau"], "co_cau_ntb.csv"),
        (["tts"], "ops_tts.csv"),
        (["opr"], "opr_opr.csv"),
        (["raw n-1", "oe_madh", "raw_n-1", "raw n - 1", "oe madh"], "opr_oe.csv"),
        (["rawopr"], "opr_raw.csv"),
        (["aging trên 5 ngày", "aging tren 5 ngay", "đơn giao aging trên 5 ngày", "don giao aging tren 5 ngay"], "aging_raw.csv"),
        (["treo lc", "stuck", "treo luân chuyển", "treo luan chuyen"], "treo_stuck.csv"),
        (["ntb", "bất ổn", "bat_on", "cảnh báo"], "buu_cuc_bat_on.csv"),
        (["đang off", "dang off", "off", "off_tuyen", "off tuyến"], "off_tuyen_spe.csv"),
        (["shopee_tiktok", "tao_don", "tạo đơn"], "vols_tao_don.csv"),
        (["odr tts", "odr_tts"], "ODR TTS.csv"),
        (["fd"], "ops_fd.csv"),
        (["baocao", "báo cáo"], "ops_productivity_realtime.csv"),
        (["nhân sự", "nhan su"], "ops_nhan_su.csv"),
        (["sl > 10kg", "sl >10kg", "sl>10kg", "sl 10kg", "hàng nặng > 10kg", "hang nang > 10kg"], "ops_heavy_10kg.csv"),
        (["sanluong", "sản lượng ca", "san luong ca", "ops_ca_data", "ca_data"], "ops_ca_data.csv"),
        (["trên10kg", "tren10kg", "trên 10kg", "tren 10kg", "treen10kg", "treen 10kg", "tạo đơn 10kg", "tao don 10kg"], "ops_tao_don_10kg.csv"),
        (["trên10kg", "tren10kg", "trên 10kg", "tren 10kg", "10kg", "hàng 10kg"], "raw_tren10kg.csv")
    ]
    
    
    gid_to_filenames = {}
    for candidates, target_csv in sheet_mappings:
        matched_gid = None
        for cand in candidates:
            cand_clean = unicodedata.normalize('NFC', cand.strip().lower())
            if cand_clean in gid_map:
                matched_gid = gid_map[cand_clean]
                break
        if matched_gid is not None:
            if matched_gid not in gid_to_filenames:
                gid_to_filenames[matched_gid] = []
            gid_to_filenames[matched_gid].append(target_csv)
            
    if not gid_to_filenames:
        return False, "Không tìm thấy sheet nào khớp với cấu hình."
        
    print(f"Found {len(gid_to_filenames)} unique GIDs to download.")
    
    # Phase 1: Download all CSVs in parallel (fast network I/O only, no DB writes)
    pending_db_writes = []  # list of (df, filename) to write to DB later
    
    def download_gid(gid, filenames):
        csv_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
        content = None
        for attempt in range(4):
            try:
                time.sleep(0.15 * (attempt + 1))
                r = requests.get(csv_url, headers=headers, timeout=30)
                if r.status_code == 200 and len(r.content) > 10:
                    content = r.content
                    break
                elif r.status_code == 429:
                    time.sleep(1.5 * (attempt + 1))
            except Exception as e:
                if attempt < 3:
                    time.sleep(1.5 * (attempt + 1))
                else:
                    print(f"Error downloading GID {gid} for {filenames}: {e}")
                    return False
        if not content:
            return False
            
        for filename in filenames:
            csv_path = resolve_path(filename, write=True)
            if filename == 'ops_ca_data.csv':
                import io
                try:
                    df_ca = pd.read_csv(io.BytesIO(content), header=1)
                    df_ca.to_csv(csv_path, index=False, encoding='utf-8')
                    pending_db_writes.append((df_ca, filename))
                    continue
                except Exception as e:
                    print(f"Error parsing synced CSV {filename}: {e}")
            with open(csv_path, 'wb') as f:
                f.write(content)
            # Parse CSV into DataFrame for deferred DB write
            try:
                import io
                for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                        pending_db_writes.append((df, filename))
                        break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Error parsing synced CSV {filename}: {e}")
        return True
        
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(gid_to_filenames), 2)) as executor:
        futures = {executor.submit(download_gid, gid, fnames): gid for gid, fnames in gid_to_filenames.items()}
        for future in concurrent.futures.as_completed(futures):
            gid = futures[future]
            try:
                if future.result():
                    success_count += len(gid_to_filenames[gid])
            except Exception as e:
                print(f"Exception downloading GID {gid}: {e}")
                
    if success_count == 0:
        return False, "Không tải được file CSV nào từ Google Sheets."
    
    # Phase 2: Batch DB writes in parallel (deferred from download phase)
    if pending_db_writes:
        print(f"Writing {len(pending_db_writes)} DataFrames to DB in parallel...")
        def write_one(args):
            df, fname = args
            try:
                save_df_to_db(df, fname)
            except Exception as e:
                print(f"Error writing {fname} to DB: {e}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as db_executor:
            list(db_executor.map(write_one, pending_db_writes))
        print("DB writes complete.")
        try:
            split_raw_tren10kg()
        except Exception as e:
            print(f"Error splitting raw_tren10kg: {e}")
        
    return True, f"Đã tải thành công {success_count} files."

def async_sync_task(is_admin_flag):
    global OPERATIONAL_CACHE, OPR_CACHE, BACKLOG_CACHE_RAW, UNSTABLE_PO_CACHE, OFF_SPE_CACHE, CA_REPORT_CACHE, PRODUCTIVITY_REALTIME_CACHE, SYNC_STATUS
    import time
    sync_start = time.time()
    try:
        if is_admin_flag:
            config = load_config()
            url = config.get("consolidated_url", "")
            if url and url.strip():
                # Phase 1: Download CSVs from Google Sheets
                SYNC_STATUS["progress"] = "Đang tải dữ liệu trực tiếp dưới dạng CSV (Tối ưu)..."
                t0 = time.time()
                
                # Download CA Report Data
                SYNC_STATUS["progress"] = "Đang tải báo cáo Sản lượng Ca..."
                try:
                    import io, requests
                    url_ca = 'https://docs.google.com/spreadsheets/d/1JZ1eRerRqrpwjZ4HBevQunjd8VquM_cvPFz12TaJfMQ/export?format=csv&gid=260711009'
                    r_ca = requests.get(url_ca, headers=get_google_auth_headers(), timeout=30)
                    if r_ca.status_code == 200:
                        content_ca = r_ca.content
                        for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                            try:
                                df_ca = pd.read_csv(io.BytesIO(content_ca), header=1, encoding=enc)
                                filepath = resolve_path('ops_ca_data.csv', write=True)
                                df_ca.to_csv(filepath, index=False)
                                save_df_to_db(df_ca, 'ops_ca_data.csv')
                                print("Successfully downloaded ops_ca_data.csv with header=1")
                                break
                            except Exception:
                                continue
                except Exception as e:
                    print(f"Error downloading CA data: {e}")

                direct_success, direct_msg = sync_sheets_directly_as_csv(url)
                download_elapsed = round(time.time() - t0, 1)
                
                if direct_success:
                    print(f"Direct CSV sync succeeded in {download_elapsed}s: {direct_msg}")
                else:
                    print(f"Direct CSV sync failed ({direct_msg}), trying XLSX fallback...")
                    temp_xlsx = resolve_path('downloaded_consolidated_sheet.xlsx', write=True)
                    success, msg = download_google_sheet(url, temp_xlsx)
                    if success and split_excel_to_csvs(temp_xlsx):
                        print("XLSX fallback download and split succeeded.")
                    else:
                        print(f"Google Sheet download unavailable on server ({direct_msg}), using committed CSV data.")
            else:
                print("No consolidated URL configured, using existing CSV files.")
                
        # Phase 2: Process data and update caches
        SYNC_STATUS["progress"] = "Đang xử lý dữ liệu và cập nhật bộ nhớ đệm..."
        t1 = time.time()
        update_all_caches()
        cache_elapsed = round(time.time() - t1, 1)
        print(f"Cache update completed in {cache_elapsed}s")
        
        if OPERATIONAL_CACHE and "error" in OPERATIONAL_CACHE:
            SYNC_STATUS["status"] = "error"
            SYNC_STATUS["error"] = OPERATIONAL_CACHE["error"]
            return
        if OPR_CACHE and "error" in OPR_CACHE:
            SYNC_STATUS["status"] = "error"
            SYNC_STATUS["error"] = OPR_CACHE["error"]
            return
        if BACKLOG_CACHE_RAW:
            if "error" in BACKLOG_CACHE_RAW["aging"]:
                SYNC_STATUS["status"] = "error"
                SYNC_STATUS["error"] = BACKLOG_CACHE_RAW["aging"]["error"]
                return
            if "error" in BACKLOG_CACHE_RAW["treo"]:
                SYNC_STATUS["status"] = "error"
                SYNC_STATUS["error"] = BACKLOG_CACHE_RAW["treo"]["error"]
                return
        
        ts = add_to_history(BACKLOG_CACHE_RAW["aging"], BACKLOG_CACHE_RAW["treo"])
        
        # Save sync metadata to DB so other serverless instances detect the update
        try:
            import time
            save_json_to_db({"last_sync_time": time.time()}, "sync_metadata.json")
        except Exception as e:
            print(f"Error saving sync metadata to DB: {e}")
            
        total_elapsed = round(time.time() - sync_start, 1)
        SYNC_STATUS["status"] = "success"
        SYNC_STATUS["timestamp"] = ts
        SYNC_STATUS["progress"] = f"Đồng bộ hoàn tất! ({total_elapsed}s)"
        print(f"=== SYNC COMPLETED in {total_elapsed}s ===")
        
    except Exception as e:
        total_elapsed = round(time.time() - sync_start, 1)
        SYNC_STATUS["status"] = "error"
        SYNC_STATUS["error"] = f"Lỗi hệ thống khi đồng bộ ({total_elapsed}s): {str(e)}"

@app.route('/api/sync', methods=['GET', 'POST'])
def trigger_sync():
    global SYNC_STATUS
    
    is_cron = False
    auth_header = request.headers.get('Authorization')
    cron_secret = os.environ.get('CRON_SECRET')
    if request.method == 'GET' and cron_secret and auth_header == f"Bearer {cron_secret}":
        is_cron = True
        
    if request.method == 'GET' and not is_cron:
        return jsonify({"error": "Phương thức GET chỉ dành cho Vercel Cron tự động."}), 405
        
    if not is_cron:
        auth = request.authorization
        if auth and check_auth(auth.username, auth.password):
            session['username'] = auth.username
            users = load_users()
            user = users.get(auth.username, {})
            session['role'] = user.get("role", "staff")
            session['permissions'] = user.get("permissions", [])
            
        if 'username' not in session:
            return jsonify({"error": "Yêu cầu đăng nhập để truy cập hệ thống."}), 401
        role = session.get('role')
        perms = session.get('permissions', [])
        if role != 'admin' and 'tab-sync' not in perms:
            return jsonify({"error": "Quyền truy cập bị từ chối."}), 403
            
    ip = request.remote_addr
    is_ok, retry_after = check_rate_limit(f"{ip}_sync", limit=3, period=60)
    if not is_ok:
        return jsonify({"error": f"Yêu cầu đồng bộ quá nhanh. Vui lòng thử lại sau {retry_after} giây."}), 429
        
    if SYNC_STATUS["status"] == "processing":
        return jsonify({"error": "Đang có quá trình đồng bộ đang chạy."}), 400
        
    SYNC_STATUS["status"] = "processing"
    SYNC_STATUS["error"] = None
    SYNC_STATUS["progress"] = "Đang khởi tạo đồng bộ..."
    
    admin_flag = is_admin() or is_cron
    
    is_vercel = os.environ.get("VERCEL") or (request.host and "vercel.app" in request.host) or (request.headers.get("Host") and "vercel.app" in request.headers.get("Host"))
    if is_vercel:
        async_sync_task(admin_flag)
        if SYNC_STATUS["status"] == "error":
            return jsonify({"error": SYNC_STATUS["error"]}), 500
        return jsonify({"success": True, "status": "success", "message": "Đồng bộ hoàn tất!"})
    else:
        threading.Thread(target=async_sync_task, args=(admin_flag,), daemon=True).start()
        return jsonify({"success": True, "status": "started"})

@app.route('/api/sync/status', methods=['GET'])
@requires_permission('tab-sync')
def get_sync_status():
    global SYNC_STATUS
    return jsonify(SYNC_STATUS)


@app.route('/api/nhan-su', methods=['GET'])
@requires_permission('tab-nhan-su')
def api_nhan_su():
    try:
        am = request.args.get('am')
        province = request.args.get('province')
        post_office = request.args.get('post_office')
        
        if session.get('am_name'):
            am = session.get('am_name')
            
        ns_path = resolve_path('ops_nhan_su.csv', write=False)
        df_ns = safe_read_csv(ns_path)
        if df_ns is None or df_ns.empty:
            return jsonify({"error": "Không tìm thấy dữ liệu nhân sự (ops_nhan_su.csv). Vui lòng thực hiện Đồng bộ dữ liệu."}), 404
            
        df_ns = apply_filters(df_ns, am=am, province=province, post_office=post_office)
        df_ns.columns = [c.strip() for c in df_ns.columns]
        
        def check_sp_team(x):
            val_str = str(x).strip().lower()
            return val_str in ['true', '1', 'yes', 't']
            
        ns_status_col = next((c for c in df_ns.columns if str(c).strip().lower() in ['trạng thái', 'trang thai', 'status']), None)
        ns_status_series = df_ns[ns_status_col].astype(str).str.strip() if ns_status_col else pd.Series("Đang làm việc", index=df_ns.index)

        active_mask = (
            (ns_status_series.isin(["Đang làm việc", "dang lam viec"])) &
            (df_ns['Vùng'].astype(str).str.strip() == "NTB") &
            (df_ns['Chức vụ'].astype(str).str.strip() == "Business Development Field Executive") &
            (~df_ns['SP Team?'].apply(check_sp_team))
        )
        active_df = df_ns[active_mask].copy()
        
        resigned_mask = (
            (ns_status_series.isin(["Đã nghỉ", "da nghi"])) &
            (df_ns['Vùng'].astype(str).str.strip() == "NTB")
        )
        resigned_count = len(df_ns[resigned_mask])
        
        def parse_warehouse_id(bc_str):
            if pd.isna(bc_str):
                return None
            parts = str(bc_str).split(" - ", 1)
            if len(parts) == 2:
                try:
                    return int(parts[0].strip())
                except:
                    return parts[0].strip()
            return None
            
        active_df['warehouse_id'] = active_df['Bưu cục'].apply(parse_warehouse_id)
        
        cc_path = resolve_path('ops_co_cau.csv', write=False)
        df_cc = safe_read_csv(cc_path)
        if df_cc is None or df_cc.empty:
            return jsonify({"error": "Không tìm thấy dữ liệu cơ cấu (ops_co_cau.csv)."}), 404
            
        df_cc = apply_filters(df_cc, am=am, province=province, post_office=post_office)
        df_cc.columns = [c.strip() for c in df_cc.columns]
        
        def clean_id(x):
            try:
                return int(float(x))
            except:
                return str(x).strip()
        df_cc['warehouse_id_clean'] = df_cc['warehouse_id'].apply(clean_id)
        active_df['warehouse_id_clean'] = active_df['warehouse_id'].apply(clean_id)
        
        vol_path = resolve_path('vols_tao_don.csv', write=False)
        po_vols = {}
        unique_dates_count = 1
        df_vol = safe_read_csv(vol_path)
        if df_vol is not None and not df_vol.empty:
            df_vol.columns = [c.strip() for c in df_vol.columns]
            df_vol_ntb = df_vol[df_vol['Vùng'].astype(str).str.strip() == 'NTB'].copy()
            unique_dates_count = len(df_vol_ntb['Date'].unique()) if 'Date' in df_vol_ntb.columns else 1
            if unique_dates_count == 0:
                unique_dates_count = 1
            df_vol_ntb['warehouse_id_clean'] = df_vol_ntb['warehouse_id'].apply(clean_id)
            vol_sums = df_vol_ntb.groupby('warehouse_id_clean')['Volume'].sum()
            for wh_id, v_sum in vol_sums.items():
                po_vols[wh_id] = round(v_sum / unique_dates_count)
                    
        hc_counts = active_df.groupby('warehouse_id_clean').size().to_dict()
        
        po_list = []
        for _, r in df_cc.iterrows():
            wh_id = r.get('warehouse_id')
            wh_id_clean = clean_id(wh_id)
            bc_name = r.get('Bưu cục', '')
            province = r.get('Tỉnh', '')
            am = r.get('AM', '')
            
            hc = hc_counts.get(wh_id_clean, 0)
            vol = po_vols.get(wh_id_clean, 0)
            
            po_list.append({
                "warehouse_id": str(wh_id),
                "name": str(bc_name),
                "province": str(province),
                "am": str(am),
                "hc_current": hc,
                "vol_2025": vol
            })
            
        active_pos_count = len([x for x in po_list if x["hc_current"] > 0 or x["vol_2025"] > 0])
        
        return jsonify({
            "active_headcount": len(active_df),
            "resigned_headcount": resigned_count,
            "po_count": active_pos_count,
            "pos": po_list
        })
    except Exception as e:
        print(f"Error in api_nhan_su: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500


@app.route('/api/summary-dashboard')
@requires_permission('tab-dashboard')
def api_summary_dashboard():
    try:
        df_gtc, df_ltc, df_aging, df_treo = get_dataframes()
        
        # Filters from query params
        am = request.args.get('am')
        province = request.args.get('province')
        post_office = request.args.get('post_office')
        selected_date = request.args.get('date')
        
        # Find latest date dynamically
        all_times = set(df_gtc['Time'].dropna().unique()).union(set(df_ltc['Time'].dropna().unique()))
        dates_sorted = sorted(list(all_times), key=lambda x: pd.to_datetime(x.split(' - ')[0]))
        if not dates_sorted:
            return jsonify({"error": "Không có dữ liệu ngày trong Datagtc hoặc Dataltc"})
            
        if selected_date and selected_date in dates_sorted:
            latest_date = selected_date
        else:
            latest_date = dates_sorted[-1]
        
        prev_date = dates_sorted[-2] if len(dates_sorted) >= 2 else None
        
        latest_idx = dates_sorted.index(latest_date) if latest_date in dates_sorted else len(dates_sorted) - 1
        n3_date = dates_sorted[latest_idx - 3] if latest_idx >= 3 else None
        
        # Find same day of week last week (7 days ago)
        latest_dt = pd.to_datetime(latest_date.split(' - ')[0])
        last_week_date = None
        for d in dates_sorted:
            dt = pd.to_datetime(d.split(' - ')[0])
            if (latest_dt - dt).days == 7:
                last_week_date = d
                break
                
        def compute_kpi_for_date(date_str, filter_am=None, filter_prov=None, filter_po=None):
            if not date_str:
                return None
            gtc_d = df_gtc[df_gtc['Time'] == date_str]
            
            # Fallback if date is not present in df_ltc
            if date_str in df_ltc['Time'].values:
                ltc_d = df_ltc[df_ltc['Time'] == date_str]
            else:
                ltc_times = df_ltc['Time'].dropna().unique()
                if len(ltc_times) > 0:
                    ltc_dates_sorted = sorted(list(ltc_times), key=lambda x: pd.to_datetime(x.split(' - ')[0]))
                    ltc_d = df_ltc[df_ltc['Time'] == ltc_dates_sorted[-1]]
                else:
                    ltc_d = df_ltc[df_ltc['Time'] == date_str]
            
            gtc_d = apply_filters(gtc_d, filter_am, filter_prov, filter_po)
            ltc_d = apply_filters(ltc_d, filter_am, filter_prov, filter_po)
            
            if 'ltc_vol' not in ltc_d.columns:
                if 'Sản Lượng Lấy Thành Công' in ltc_d.columns:
                    ltc_d['ltc_vol'] = safe_to_numeric(ltc_d['Sản Lượng Lấy Thành Công'])
                elif '%LTC' in ltc_d.columns:
                    ltc_d['ltc_vol'] = safe_to_numeric(ltc_d['Volume']) * normalize_pct_col(ltc_d['%LTC'])
                else:
                    ltc_d['ltc_vol'] = 0.0

            ltc_vol = ltc_d['Volume'].sum()
            ltc_done = ltc_d['ltc_vol'].sum()
            gtc_vol = gtc_d['Volume'].sum()
            gtc_done = gtc_d['delivered_vol'].sum()
            ttc_done = gtc_d['ttc_vol'].sum()
            
            return {
                'ltc': round((ltc_done / ltc_vol * 100), 2) if ltc_vol > 0 else 0.0,
                'gtc': round((gtc_done / gtc_vol * 100), 2) if gtc_vol > 0 else 0.0,
                'ttc': round((ttc_done / gtc_vol * 100), 2) if gtc_vol > 0 else 0.0,
                'vol_ltc': int(ltc_done),
                'vol_gtc': int(gtc_vol)
            }
        
        # Filter for latest date
        today_gtc = df_gtc[df_gtc['Time'] == latest_date]
        
        # Fallback for today_ltc if latest_date not in df_ltc['Time'].values
        if latest_date in df_ltc['Time'].values:
            today_ltc = df_ltc[df_ltc['Time'] == latest_date]
        else:
            ltc_times = df_ltc['Time'].dropna().unique()
            if len(ltc_times) > 0:
                ltc_dates_sorted = sorted(list(ltc_times), key=lambda x: pd.to_datetime(x.split(' - ')[0]))
                today_ltc = df_ltc[df_ltc['Time'] == ltc_dates_sorted[-1]]
            else:
                today_ltc = df_ltc[df_ltc['Time'] == latest_date]
        
        # Apply filters to today's data
        today_gtc = apply_filters(today_gtc, am, province, post_office)
        today_ltc = apply_filters(today_ltc, am, province, post_office)
        
        # Apply filters to backlog datasets
        curr_aging = apply_filters(df_aging, am, province, post_office)
        curr_treo = apply_filters(df_treo, am, province, post_office)
        
        # 1. Completed Volume Grouped by Province
        gtc_prov = today_gtc.groupby('mapped_prov').agg({'Volume': 'sum', 'delivered_vol': 'sum', 'ttc_vol': 'sum'}).reset_index()
        ltc_prov = today_ltc.groupby('mapped_prov').agg({'Volume': 'sum', 'ltc_vol': 'sum'}).reset_index()
        
        merged_prov = pd.merge(gtc_prov, ltc_prov, on='mapped_prov', suffixes=('_gtc', '_ltc'), how='outer').fillna(0)
        completed_vols = []
        for _, r in merged_prov.iterrows():
            prov_name = r['mapped_prov']
            completed_vols.append({
                'province': prov_name,
                'LTC': int(r['ltc_vol']),
                'GTC': int(r['delivered_vol']),
                'TTC': int(r['ttc_vol']),
                'LTC_pct': round((r['ltc_vol'] / r['Volume_ltc'] * 100), 2) if r['Volume_ltc'] > 0 else 0.0,
                'GTC_pct': round((r['delivered_vol'] / r['Volume_gtc'] * 100), 2) if r['Volume_gtc'] > 0 else 0.0,
                'TTC_pct': round((r['ttc_vol'] / r['Volume_gtc'] * 100), 2) if r['Volume_gtc'] > 0 else 0.0,
                'Volume_gtc': int(r['Volume_gtc']),
                'Volume_ltc': int(r['ltc_vol'])
            })
            
        # 2. Backlog by AM
        treo_giao = curr_treo[curr_treo['Loại đơn'] == 'Luân chuyển giao']
        treo_tra = curr_treo[curr_treo['Loại đơn'] == 'Luân chuyển trả']
        
        aging_am = curr_aging.groupby('mapped_am').size().reset_index(name='chua_giao')
        treo_giao_am = treo_giao.groupby('mapped_am').size().reset_index(name='chua_lay')
        treo_tra_am = treo_tra.groupby('mapped_am').size().reset_index(name='chua_tra')
        
        backlog_am = pd.merge(treo_giao_am, aging_am, on='mapped_am', how='outer')
        backlog_am = pd.merge(backlog_am, treo_tra_am, on='mapped_am', how='outer').fillna(0)
        
        backlog_by_am = []
        for _, r in backlog_am.iterrows():
            backlog_by_am.append({
                'am': r['mapped_am'],
                'chua_lay': int(r['chua_lay']),
                'chua_giao': int(r['chua_giao']),
                'chua_tra': int(r['chua_tra'])
            })
            
        # 3. Overall & Province-specific KPIs
        kpis = {}
        
        def format_kpi_dict(latest_kpi, prev_kpi, lw_kpi, n3_kpi=None):
            res = {
                'ltc': latest_kpi['ltc'] if latest_kpi else 0.0,
                'gtc': latest_kpi['gtc'] if latest_kpi else 0.0,
                'ttc': latest_kpi['ttc'] if latest_kpi else 0.0,
                'vol_ltc': latest_kpi['vol_ltc'] if latest_kpi else 0,
                'vol_gtc': latest_kpi['vol_gtc'] if latest_kpi else 0
            }
            if latest_kpi:
                if prev_kpi:
                    res['dod'] = {
                        'ltc': round(latest_kpi['ltc'] - prev_kpi['ltc'], 2),
                        'gtc': round(latest_kpi['gtc'] - prev_kpi['gtc'], 2),
                        'ttc': round(latest_kpi['ttc'] - prev_kpi['ttc'], 2)
                    }
                else:
                    res['dod'] = None
                
                if lw_kpi:
                    res['wow'] = {
                        'ltc': round(latest_kpi['ltc'] - lw_kpi['ltc'], 2),
                        'gtc': round(latest_kpi['gtc'] - lw_kpi['gtc'], 2),
                        'ttc': round(latest_kpi['ttc'] - lw_kpi['ttc'], 2)
                    }
                else:
                    res['wow'] = None

                if n3_kpi:
                    res['n3'] = {
                        'ltc': round(latest_kpi['ltc'] - n3_kpi['ltc'], 2),
                        'gtc': round(latest_kpi['gtc'] - n3_kpi['gtc'], 2),
                        'ttc': round(latest_kpi['ttc'] - n3_kpi['ttc'], 2)
                    }
                else:
                    res['n3'] = None
            else:
                res['dod'] = None
                res['wow'] = None
                res['n3'] = None
            return res
            
        overall_latest = compute_kpi_for_date(latest_date, am, province, post_office)
        overall_prev = compute_kpi_for_date(prev_date, am, province, post_office) if prev_date else None
        overall_lw = compute_kpi_for_date(last_week_date, am, province, post_office) if last_week_date else None
        overall_n3 = compute_kpi_for_date(n3_date, am, province, post_office) if n3_date else None
        
        kpis['overall'] = format_kpi_dict(overall_latest, overall_prev, overall_lw, overall_n3)
        
        # Compute for each province
        all_provinces = set(df_ltc['mapped_prov'].unique()).union(set(df_gtc['mapped_prov'].unique()))
        for prov_name in all_provinces:
            if prov_name == "Không xác định":
                continue
            prov_latest = compute_kpi_for_date(latest_date, am, prov_name, post_office)
            prov_prev = compute_kpi_for_date(prev_date, am, prov_name, post_office) if prev_date else None
            prov_lw = compute_kpi_for_date(last_week_date, am, prov_name, post_office) if last_week_date else None
            prov_n3 = compute_kpi_for_date(n3_date, am, prov_name, post_office) if n3_date else None
            
            clean_key = clean_str_key(prov_name)
            kpis[clean_key] = format_kpi_dict(prov_latest, prov_prev, prov_lw, prov_n3)
            kpis[clean_key]['name'] = prov_name
            
        return jsonify(clean_nan({
            'latest_date': latest_date,
            'all_dates': dates_sorted[::-1],
            'completed_vols': completed_vols,
            'backlog_by_am': backlog_by_am,
            'kpis': kpis
        }))
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": f"Lỗi tính toán summary: {str(e)}"}), 500

@app.route('/api/trends-dashboard')
@requires_permission('tab-dashboard')
def api_trends_dashboard():
    try:
        df_gtc, df_ltc, _, _ = get_dataframes()
        
        am = request.args.get('am')
        province = request.args.get('province')
        post_office = request.args.get('post_office')
        
        # Apply filters
        df_gtc = apply_filters(df_gtc, am, province, post_office)
        df_ltc = apply_filters(df_ltc, am, province, post_office)
        
        # Find last 7 dates sorted chronologically
        all_times = set(df_gtc['Time'].dropna().unique()).union(set(df_ltc['Time'].dropna().unique()))
        dates_sorted = sorted(list(all_times), key=lambda x: pd.to_datetime(x.split(' - ')[0]))
        last_7_dates = dates_sorted[-7:]
        
        # Filter both dataframes to last 7 dates
        df_gtc_7 = df_gtc[df_gtc['Time'].isin(last_7_dates)]
        df_ltc_7 = df_ltc[df_ltc['Time'].isin(last_7_dates)]
        
        # Group by mapped_prov and Time
        gtc_grouped = df_gtc_7.groupby(['mapped_prov', 'Time']).agg({'Volume': 'sum', 'delivered_vol': 'sum'}).reset_index()
        ltc_grouped = df_ltc_7.groupby(['mapped_prov', 'Time']).agg({'Volume': 'sum', 'ltc_vol': 'sum'}).reset_index()
        
        # Overall trends
        gtc_overall = df_gtc_7.groupby('Time').agg({'Volume': 'sum', 'delivered_vol': 'sum'}).reset_index()
        ltc_overall = df_ltc_7.groupby('Time').agg({'Volume': 'sum', 'ltc_vol': 'sum'}).reset_index()
        
        res_dates = last_7_dates
        
        trends = {}
        all_provinces = set(df_ltc_7['mapped_prov'].unique()).union(set(df_gtc_7['mapped_prov'].unique()))
        
        for prov in all_provinces:
            if prov == "Không xác định":
                continue
            prov_ltc = []
            prov_gtc = []
            
            p_ltc_df = ltc_grouped[ltc_grouped['mapped_prov'] == prov]
            p_gtc_df = gtc_grouped[gtc_grouped['mapped_prov'] == prov]
            
            for d in res_dates:
                # LTC
                d_ltc = p_ltc_df[p_ltc_df['Time'] == d]
                if len(d_ltc) > 0 and d_ltc['Volume'].iloc[0] > 0:
                    prov_ltc.append(round((d_ltc['ltc_vol'].iloc[0] / d_ltc['Volume'].iloc[0] * 100), 2))
                else:
                    prov_ltc.append(None)
                # GTC
                d_gtc = p_gtc_df[p_gtc_df['Time'] == d]
                if len(d_gtc) > 0 and d_gtc['Volume'].iloc[0] > 0:
                    prov_gtc.append(round((d_gtc['delivered_vol'].iloc[0] / d_gtc['Volume'].iloc[0] * 100), 2))
                else:
                    prov_gtc.append(None)
                    
            clean_prov = str(prov).strip()
            trend_data = {
                'ltc': prov_ltc,
                'gtc': prov_gtc
            }
            # Add multiple key formats so frontend can access by 'lam_dong', 'lâm_đồng', or 'Lâm Đồng'
            trends[clean_prov] = trend_data
            trends[clean_prov.lower().replace(" ", "_")] = trend_data
            
            # Unaccented key (e.g. 'lam_dong' for 'Lâm Đồng')
            import unicodedata
            nfkd_form = unicodedata.normalize('NFKD', clean_prov)
            unaccented = "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D').lower().replace(" ", "_")
            trends[unaccented] = trend_data
            
        # Overall
        overall_ltc = []
        overall_gtc = []
        for d in res_dates:
            d_ltc = ltc_overall[ltc_overall['Time'] == d]
            if len(d_ltc) > 0 and d_ltc['Volume'].iloc[0] > 0:
                overall_ltc.append(round((d_ltc['ltc_vol'].iloc[0] / d_ltc['Volume'].iloc[0] * 100), 2))
            else:
                overall_ltc.append(None)
                
            d_gtc = gtc_overall[gtc_overall['Time'] == d]
            if len(d_gtc) > 0 and d_gtc['Volume'].iloc[0] > 0:
                overall_gtc.append(round((d_gtc['delivered_vol'].iloc[0] / d_gtc['Volume'].iloc[0] * 100), 2))
            else:
                overall_gtc.append(None)
                
        trends['overall'] = {
            'ltc': overall_ltc,
            'gtc': overall_gtc
        }
        
        return jsonify(clean_nan({
            'dates': res_dates,
            'trends': trends
        }))
        
    except Exception as e:
        return jsonify({"error": f"Lỗi tính toán xu hướng: {str(e)}"}), 500

@app.route('/api/matrix-tables')
@requires_permission('tab-volume-creation')
def api_matrix_tables():
    try:
        df_gtc, df_ltc, _, _ = get_dataframes()
        
        am_filter = request.args.get('am')
        province_filter = request.args.get('province')
        post_office_filter = request.args.get('post_office')
        
        # Apply filters
        df_gtc_f = apply_filters(df_gtc, am_filter, province_filter, post_office_filter)
        df_ltc_f = apply_filters(df_ltc, am_filter, province_filter, post_office_filter)
        
        # Find last 6 dates available
        all_times = set(df_gtc['Time'].dropna().unique()).union(set(df_ltc['Time'].dropna().unique()))
        dates_sorted = sorted(list(all_times), key=lambda x: pd.to_datetime(x.split(' - ')[0]))
        last_6_dates = dates_sorted[-6:][::-1]
        
        def build_matrix_data(df, vol_col, target_val_col):
            df_6 = df[df['Time'].isin(last_6_dates)].copy()
            if len(df_6) == 0:
                return {'dates': last_6_dates, 'rows': []}
                
            # Group by AM, Chi tiết, Time
            grouped = df_6.groupby(['mapped_am', 'Chi tiết', 'Time']).agg({'Volume': 'sum', target_val_col: 'sum'}).reset_index()
            
            # AM overall totals for each date
            am_totals = df_6.groupby(['mapped_am', 'Time']).agg({'Volume': 'sum', target_val_col: 'sum'}).reset_index()
            
            rows = []
            unique_ams = sorted(df_6['mapped_am'].unique())
            
            for am in unique_ams:
                if am == "Không xác định":
                    continue
                
                am_time_df = am_totals[am_totals['mapped_am'] == am]
                totals_dict = {}
                for d in last_6_dates:
                    d_row = am_time_df[am_time_df['Time'] == d]
                    if len(d_row) > 0:
                        vol = float(d_row['Volume'].iloc[0])
                        target_val = float(d_row[target_val_col].iloc[0])
                        pct = round((target_val / vol * 100), 2) if vol > 0 else 0.0
                        totals_dict[d] = {'vol': int(vol), 'pct': pct}
                    else:
                        totals_dict[d] = {'vol': 0, 'pct': 0.0}
                        
                am_details_df = grouped[grouped['mapped_am'] == am]
                unique_pos = sorted(am_details_df['Chi tiết'].unique())
                pos_list = []
                
                for po in unique_pos:
                    po_time_df = am_details_df[am_details_df['Chi tiết'] == po]
                    po_data_dict = {}
                    for d in last_6_dates:
                        d_row = po_time_df[po_time_df['Time'] == d]
                        if len(d_row) > 0:
                            vol = float(d_row['Volume'].iloc[0])
                            target_val = float(d_row[target_val_col].iloc[0])
                            pct = round((target_val / vol * 100), 2) if vol > 0 else 0.0
                            po_data_dict[d] = {'vol': int(vol), 'pct': pct}
                        else:
                            po_data_dict[d] = {'vol': 0, 'pct': 0.0}
                    pos_list.append({
                        'bc': po,
                        'data': po_data_dict
                    })
                    
                rows.append({
                    'am': am,
                    'is_header': True,
                    'totals': totals_dict,
                    'pos': pos_list
                })
                
            return {
                'dates': last_6_dates,
                'rows': rows
            }
            
        ltc_matrix = build_matrix_data(df_ltc_f, 'Volume', 'ltc_vol')
        gtc_matrix = build_matrix_data(df_gtc_f, 'Volume', 'delivered_vol')
        
        return jsonify(clean_nan({
            'ltc': ltc_matrix,
            'gtc': gtc_matrix
        }))
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": f"Lỗi tính toán matrix tables: {str(e)}"}), 500

@app.route('/api/heavy-10kg')
@requires_auth
def api_heavy_10kg():
    try:
        am = request.args.get('am')
        province = request.args.get('province')
        post_office = request.args.get('post_office')
        date = request.args.get('date')
        ck_only = request.args.get('ck_only', 'false').lower() in ['true', '1', 'yes']
        spike_level = request.args.get('spike_level')

        if am or province or post_office or date or ck_only or spike_level:
            data = process_heavy_10kg_report(
                am=am, 
                province=province, 
                post_office=post_office, 
                date=date, 
                ck_only=ck_only, 
                spike_level=spike_level
            )
        else:
            global HEAVY_10KG_CACHE
            if (HEAVY_10KG_CACHE is None or 
                (isinstance(HEAVY_10KG_CACHE, dict) and ("error" in HEAVY_10KG_CACHE or HEAVY_10KG_CACHE.get('total_ops_vol', 0) == 0 or HEAVY_10KG_CACHE.get('total_created_vol', 0) == 0))):
                HEAVY_10KG_CACHE = process_heavy_10kg_report()
            data = HEAVY_10KG_CACHE

        return jsonify(clean_nan(data))
    except Exception as e:
        return jsonify({"error": f"Lỗi lấy dữ liệu hàng nặng >10kg: {str(e)}"}), 500

@app.route('/api/chat', methods=['POST'])
@requires_auth
def api_chat():
    try:
        data = request.json or {}
        message = data.get('message', '').strip().lower()
        
        if not message:
            return jsonify({"reply": "Chào bạn! Mình có thể giúp gì cho bạn hôm nay?"})
            
        global OPERATIONAL_CACHE, OPR_CACHE
        # Ensure caches are loaded
        with CACHE_LOCK:
            if OPERATIONAL_CACHE is None:
                try:
                    OPERATIONAL_CACHE = process_operational_report()
                except Exception as e:
                    print(f"Error loading ops cache for chat: {e}")
            if OPR_CACHE is None:
                try:
                    OPR_CACHE = process_opr_report()
                except Exception as e:
                    print(f"Error loading opr cache for chat: {e}")
                    
        # Parse queries
        # Specific rankings and metrics queries first
        if 'gtc tốt nhất' in message or 'gtc tot nhat' in message or 'gtc tốt' in message or 'gtc tot' in message or ('gtc' in message and 'tốt' in message) or ('gtc' in message and 'tot' in message):
            if OPERATIONAL_CACHE and 'top_10_gtc' in OPERATIONAL_CACHE and OPERATIONAL_CACHE['top_10_gtc']:
                reply = "🏆 **Top 10 Bưu cục GTC Tốt nhất**:<br>"
                for idx, r in enumerate(OPERATIONAL_CACHE['top_10_gtc'][:10], 1):
                    reply += f"{idx}. <strong>{r['Chi tiết']}</strong>: {r['% GTC']:.2f}% (Sản lượng: {int(r['Volume'])} đơn)<br>"
            else:
                reply = "🏆 Không tìm thấy dữ liệu bưu cục GTC tốt nhất."
            return jsonify({"reply": reply})

        elif 'gtc tệ nhất' in message or 'gtc te nhat' in message or 'gtc tệ' in message or 'gtc te' in message or ('gtc' in message and 'tệ' in message) or ('gtc' in message and 'te' in message):
            if OPERATIONAL_CACHE and 'worst_10_gtc' in OPERATIONAL_CACHE and OPERATIONAL_CACHE['worst_10_gtc']:
                reply = "⚠️ **Top 10 Bưu cục GTC Tệ nhất**:<br>"
                for idx, r in enumerate(OPERATIONAL_CACHE['worst_10_gtc'][:10], 1):
                    reply += f"{idx}. <strong>{r['Chi tiết']}</strong>: {r['% GTC']:.2f}% (Sản lượng: {int(r['Volume'])} đơn)<br>"
            else:
                reply = "⚠️ Không tìm thấy dữ liệu bưu cục GTC tệ nhất."
            return jsonify({"reply": reply})

        elif 'fd tệ nhất' in message or 'fd te nhat' in message or ('fd' in message and 'tệ' in message) or ('fd' in message and 'te' in message):
            try:
                fd_rep = process_fd_report()
                if fd_rep and 'po' in fd_rep and fd_rep['po']:
                    worst_fd_list = sorted(fd_rep['po'], key=lambda x: x.get('fd_n', 0), reverse=True)[:10]
                    reply = "🚨 **Top 10 Bưu cục %FD Tệ nhất (FD cao nhất - Target < 4.5%)**:<br>"
                    for idx, r in enumerate(worst_fd_list, 1):
                        reply += f"{idx}. <strong>{r['post_office']}</strong>: {r['fd_n']:.2f}% (Vol Giao: {int(r['vol_giao'])})<br>"
                else:
                    reply = "🚨 Không tìm thấy dữ liệu %FD bưu cục."
            except Exception as e:
                reply = f"🚨 Lỗi tính toán %FD bưu cục: {str(e)}"
            return jsonify({"reply": reply})

        elif 'fd' in message or 'tỷ lệ fd' in message or 'ty le fd' in message:
            try:
                fd_rep = process_fd_report()
                if fd_rep and 'kpi' in fd_rep and fd_rep['kpi']:
                    kpi = fd_rep['kpi']
                    fd_n = kpi.get('fd_n', 0)
                    fd_n1 = kpi.get('fd_n1', 0)
                    fd_n7 = kpi.get('fd_n7', 0)
                    status_text = "✅ **Đạt mục tiêu**" if fd_n < 4.5 else "❌ **Không đạt mục tiêu**"
                    reply = f"📊 **Tỷ lệ %FD hôm nay (Tổng NTB)**: đạt <strong>{fd_n:.2f}%</strong>.<br>"
                    reply += f"- So với N-1: <strong>{fd_n1:.2f}%</strong> (Chênh lệch: {kpi.get('vs_n1', 0):+.2f}%)<br>"
                    reply += f"- So với N-7: <strong>{fd_n7:.2f}%</strong> (Chênh lệch: {kpi.get('vs_n7', 0):+.2f}%)<br>"
                    reply += f"- Đánh giá: {status_text} (Target yêu cầu: < 4.5%)"
                else:
                    reply = "📊 Hiện tại hệ thống chưa cập nhật đủ dữ liệu %FD hôm nay."
            except Exception as e:
                reply = f"📊 Lỗi tính toán tỷ lệ %FD: {str(e)}"
            return jsonify({"reply": reply})

        # 1. Bưu cục tệ nhất (Worst Post Office) - general check
        elif 'tệ nhất' in message or 'te nhat' in message or 'kém nhất' in message or 'kem nhat' in message:
            reply = "Dựa trên dữ liệu vận hành mới nhất:<br>"
            # GTC Worst
            if OPERATIONAL_CACHE and 'worst_10_gtc' in OPERATIONAL_CACHE and OPERATIONAL_CACHE['worst_10_gtc']:
                worst_gtc = OPERATIONAL_CACHE['worst_10_gtc'][0]
                reply += f"📍 **Bưu cục có tỷ lệ Giao thành công (GTC) thấp nhất**: <br><strong>{worst_gtc['Chi tiết']}</strong> với tỷ lệ GTC chỉ đạt <strong>{worst_gtc['% GTC']:.2f}%</strong> (Sản lượng: {int(worst_gtc['Volume'])} đơn).<br>"
            else:
                reply += "📍 Không tìm thấy dữ liệu bưu cục GTC.<br>"
                
            # LTC Worst
            if OPERATIONAL_CACHE and 'worst_10_ltc' in OPERATIONAL_CACHE and OPERATIONAL_CACHE['worst_10_ltc']:
                worst_ltc = OPERATIONAL_CACHE['worst_10_ltc'][0]
                reply += f"📍 **Bưu cục có tỷ lệ Giao lần đầu (LTC) thấp nhất**: <br><strong>{worst_ltc['Chi tiết']}</strong> với tỷ lệ LTC đạt <strong>{worst_ltc['% LTC']:.2f}%</strong> (Sản lượng: {int(worst_ltc['Volume'])} đơn).<br>"
                
            # Worst ODR (Ontime Delivery) from ODR TTS.csv
            try:
                odr_path = resolve_path('ODR TTS.csv', write=False)
                if os.path.exists(odr_path):
                    df_odr = pd.read_csv(odr_path)
                    df_odr['GTC'] = pd.to_numeric(df_odr['GTC'], errors='coerce')
                    df_odr['%Ontime'] = normalize_pct_col(df_odr['%Ontime'])
                    latest_date = df_odr['Time'].max()
                    df_latest = df_odr[(df_odr['Time'] == latest_date) & (df_odr['GTC'] >= 10)] # filter at least 10 orders
                    if not df_latest.empty:
                        worst_odr_row = df_latest.sort_values(by='%Ontime', ascending=True).iloc[0]
                        reply += f"📍 **Bưu cục trễ hẹn (ODR thấp nhất) ngày {latest_date}**: <br><strong>{worst_odr_row['Chi tiết']}</strong> với tỷ lệ Đúng giờ chỉ đạt <strong>{worst_odr_row['%Ontime']*100:.2f}%</strong> (Sản lượng: {int(worst_odr_row['GTC'])} đơn)."
            except Exception as e:
                print(f"Error computing worst ODR for chat: {e}")
                
            return jsonify({"reply": reply})

        # 2. OPR (Operational Performance Rate)
        elif 'opr' in message:
            if OPR_CACHE and 'overall_opr' in OPR_CACHE:
                opr_val = OPR_CACHE['overall_opr']
                reply = f"📊 **Tỷ lệ hiệu suất OPR ngày hôm nay**: đạt <strong>{opr_val}%</strong>.<br>"
                try:
                    val_float = float(str(opr_val).replace('%', ''))
                    if val_float >= 80:
                        reply += "✅ Hiệu suất OPR đạt mục tiêu tối thiểu (Target: >= 80%). Các bưu cục đang vận hành khá tốt!"
                    else:
                        reply += "⚠️ Hiệu suất OPR hiện tại dưới mục tiêu tối thiểu (Target: >= 80%). Cần tập trung cải thiện thời gian xử lý đơn hàng."
                except:
                    pass
            else:
                reply = "📊 Hiện tại hệ thống chưa cập nhật đủ dữ liệu OPR hôm nay."
            return jsonify({"reply": reply})
            
        # 3. ODR (Ontime Delivery Rate)
        elif 'odr' in message or 'đúng giờ' in message or 'trễ' in message or 'tre' in message or 'dung gio' in message:
            try:
                odr_path = resolve_path('ODR TTS.csv', write=False)
                if os.path.exists(odr_path):
                    df_odr = pd.read_csv(odr_path)
                    df_odr['GTC'] = pd.to_numeric(df_odr['GTC'], errors='coerce')
                    df_odr['%Ontime'] = normalize_pct_col(df_odr['%Ontime'])
                    df_odr['ontime_vol'] = df_odr['GTC'] * df_odr['%Ontime']
                    latest_date = df_odr['Time'].max()
                    df_latest = df_odr[df_odr['Time'] == latest_date]
                    if not df_latest.empty:
                        overall_odr = (df_latest['ontime_vol'].sum() / df_latest['GTC'].sum()) * 100
                        total_vol = df_latest['GTC'].sum()
                        reply = f"🚚 **Tỷ lệ Giao hàng đúng giờ (ODR) ngày {latest_date}**: đạt <strong>{overall_odr:.2f}%</strong> (Trên tổng sản lượng {int(total_vol):,} đơn giao).<br>"
                        if overall_odr >= 90:
                            reply += "🎉 Tỷ lệ giao hàng đúng giờ duy trì ở mức cao và đạt chuẩn chất lượng dịch vụ của GHN!"
                        else:
                            reply += "⚠️ Tỷ lệ giao đúng giờ đang giảm, vui lòng kiểm tra các tuyến luân chuyển bị nghẽn."
                    else:
                        reply = "🚚 Chưa có dữ liệu ODR cho ngày hôm nay."
                else:
                    reply = "🚚 Không tìm thấy file dữ liệu ODR TTS.csv để tính toán."
            except Exception as e:
                reply = f"🚚 Lỗi tính toán tỷ lệ ODR: {str(e)}"
            return jsonify({"reply": reply})

        # 4. GTC / LTC / Tổng quan
        elif 'gtc' in message or 'giao thành công' in message:
            if OPERATIONAL_CACHE and 'overall_gtc' in OPERATIONAL_CACHE:
                gtc_val = OPERATIONAL_CACHE['overall_gtc']
                reply = f"✅ **Tỷ lệ Giao thành công (GTC) hôm nay**: đạt <strong>{gtc_val}%</strong>.<br>(Target đề ra: >= 60.0%)"
            else:
                reply = "✅ Chưa có dữ liệu Giao thành công hôm nay."
            return jsonify({"reply": reply})

        elif 'ltc' in message or 'giao lần đầu' in message:
            if OPERATIONAL_CACHE and 'overall_ltc' in OPERATIONAL_CACHE:
                ltc_val = OPERATIONAL_CACHE['overall_ltc']
                reply = f"✈️ **Tỷ lệ Giao lần đầu thành công (LTC) hôm nay**: đạt <strong>{ltc_val}%</strong>."
            else:
                reply = "✈️ Chưa có dữ liệu Giao lần đầu thành công hôm nay."
            return jsonify({"reply": reply})

        # 5. Backlog / Tồn đọng
        elif 'backlog' in message or 'tồn' in message or 'chưa giao' in message:
            try:
                df_gtc, df_ltc, df_aging, df_treo = get_dataframes()
                total_aging = len(df_aging) if df_aging is not None else 0
                total_treo = len(df_treo) if df_treo is not None else 0
                reply = f"📦 **Tổng đơn tồn đọng (Backlog) hiện tại**: <strong>{total_aging + total_treo:,} đơn</strong>.<br>"
                reply += f"- Đơn giao trễ (Aging > 5 ngày): <strong>{total_aging:,} đơn</strong>.<br>"
                reply += f"- Đơn bị treo luân chuyển stuck: <strong>{total_treo:,} đơn</strong>."
            except Exception as e:
                reply = f"📦 Lỗi tính toán đơn backlog: {str(e)}"
            return jsonify({"reply": reply})
            
        else:
            # Help reply
            reply = "🤖 **Trợ lý NTB** xin chào!<br>Mình hỗ trợ trả lời nhanh các câu hỏi vận hành. Bạn có thể hỏi:<br>"
            reply += "- 📍 Bưu cục nào vận hành **tệ nhất**?<br>"
            reply += "- 📊 Tỷ lệ hiệu suất **OPR** hôm nay?<br>"
            reply += "- 🚚 Tỷ lệ giao hàng đúng giờ **ODR**?<br>"
            reply += "- 📦 Tổng số đơn **backlog** tồn đọng?<br>"
            reply += "- ✅ Tỷ lệ **GTC** hoặc **LTC** hiện tại?"
            return jsonify({"reply": reply})
            
    except Exception as ex:
        return jsonify({"reply": f"🤖 Đã xảy ra lỗi hệ thống: {str(ex)}"}), 500
@app.route('/api/ntb-structure')
@requires_permission('tab-introduction')
def get_ntb_structure():
    try:
        path = resolve_path('co_cau_ntb.csv', write=False)
        df = safe_read_csv(path)
        if df is None or df.empty:
            return jsonify({"error": "Không tìm thấy dữ liệu cơ cấu vùng (co_cau_ntb.csv)."}), 404
            
        df['Tỉnh'] = df['Tỉnh'].replace({'Khánh Hoà': 'Khánh Hòa', 'Bình Phước': 'Lâm Đồng'}).fillna("Chưa xác định").str.strip()
        df['AM'] = df['AM'].fillna("Chưa có AM").str.strip()
        df['Bưu cục'] = df['Bưu cục'].fillna("Chưa xác định").str.strip()
        
        structure = {}
        for prov, p_df in df.groupby('Tỉnh'):
            structure[prov] = {}
            for am, a_df in p_df.groupby('AM'):
                structure[prov][am] = sorted(list(a_df['Bưu cục'].unique()))
                
        return jsonify(structure)
    except Exception as e:
        return jsonify({"error": f"Lỗi đọc file cơ cấu: {str(e)}"}), 500

def load_khach_hang_a():
    try:
        kh_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratch', 'khach_hang_a.json')
        if os.path.exists(kh_p):
            with open(kh_p, 'r', encoding='utf-8') as f_kh:
                return json.load(f_kh)
    except Exception as e:
        print(f"Error loading khach_hang_a.json: {e}")
    return {}

@app.route('/api/khach-hang-a')
def get_khach_hang_a():
    data = load_khach_hang_a()
    if data:
        return jsonify(data)
    return jsonify({"error": "Chưa có dữ liệu khách hàng nhóm A"}), 404

def load_transport_costs():
    try:
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratch', 'transport_costs.json'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transport_costs.json'),
            resolve_path('transport_costs.json', write=False)
        ]
        for p in candidates:
            if p and os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f_tc:
                    return json.load(f_tc)
    except Exception as e:
        print(f"Error loading transport_costs.json: {e}")
    return {}

@app.route('/api/transport-costs')
def get_transport_costs():
    data = load_transport_costs()
    if data:
        return jsonify(data)
    return jsonify({"error": "Chưa có dữ liệu chi phí vận tải"}), 404

@app.route('/api/sync-transport-costs', methods=['POST', 'GET'])
def api_sync_transport_costs():
    try:
        # Kiểm tra môi trường Vercel hoặc thiếu authorized_user.json
        has_credentials = os.path.exists('authorized_user.json') or os.path.exists(os.path.join(os.path.dirname(__file__), 'authorized_user.json'))
        is_vercel = os.environ.get('VERCEL') == '1' or not has_credentials
        
        if is_vercel:
            return jsonify({
                "status": "notice",
                "message": "Web Vercel hoạt động ở chế độ bảo mật Serverless (không chứa token Google cá nhân). Để đồng bộ số liệu mới nhất từ 7 Google Sheets NCC, bạn hãy chạy file 'DONG_BO_CHI_PHI_NCC.bat' trên máy tính, hệ thống sẽ tự động quét và đẩy số liệu mới lên web!"
            }), 200

        sync_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratch', 'sync_ncc_transport_costs.py')
        if os.path.exists(sync_script):
            res = subprocess.run([sys.executable, sync_script], capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                data = load_transport_costs()
                return jsonify({"status": "success", "message": "Đã đồng bộ chi phí vận tải từ 7 NCC thành công!", "data": data})
            else:
                return jsonify({"status": "error", "message": res.stderr or res.stdout}), 500
        return jsonify({"status": "error", "message": "Không tìm thấy sync_ncc_transport_costs.py"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/batch-data')
@requires_auth
def get_batch_data():
    """
    Load all report data in a single request.
    Critical for Vercel: avoids multiple separate API calls hitting different cold instances.
    Each separate API call on Vercel could hit a new serverless instance with empty caches,
    but this single call ensures all data is loaded from the same warm instance.
    """
    result = {}
    username = session.get('username', '')
    user_perms = get_user_permissions(username)
    role = session.get('role', 'staff')
    is_admin_user = (role == 'admin')
    
    def has_perm(tab):
        if is_admin_user:
            return True
        p = user_perms.get(tab, {})
        return p.get('view', False) if isinstance(p, dict) else False
    
    # Operational
    if has_perm('tab-operational'):
        try:
            global OPERATIONAL_CACHE, DF_GTC_CACHE, DF_LTC_CACHE, DF_TTS_CACHE
            am = None
            if session.get('am_name'):
                am = session.get('am_name')
            if am:
                ops = process_operational_report(df_gtc=DF_GTC_CACHE, df_ltc=DF_LTC_CACHE, df_tts=DF_TTS_CACHE, am=am)
            else:
                with CACHE_LOCK:
                    if OPERATIONAL_CACHE is None:
                        OPERATIONAL_CACHE = process_operational_report()
                ops = OPERATIONAL_CACHE
            result['operational'] = clean_nan(ops)
        except Exception as e:
            result['operational'] = {"error": str(e)}
    else:
        result['operational'] = {"error": "No permission"}

    # OPR
    if has_perm('tab-opr'):
        try:
            global OPR_CACHE
            am = None
            if session.get('am_name'):
                am = session.get('am_name')
            if am:
                result['opr'] = clean_nan(process_opr_report(am=am))
            else:
                with CACHE_LOCK:
                    if OPR_CACHE is None:
                        OPR_CACHE = process_opr_report()
                result['opr'] = clean_nan(OPR_CACHE)
        except Exception as e:
            result['opr'] = {"error": str(e)}
    else:
        result['opr'] = {"error": "No permission"}

    # Backlog
    if has_perm('tab-backlog'):
        try:
            global BACKLOG_CACHE_RAW
            am = None
            if session.get('am_name'):
                am = session.get('am_name')
            if am:
                aging = process_aging_backlog(am=am)
                treo = process_treo_backlog(am=am)
                current_data = {"aging": aging, "treo": treo}
            else:
                with CACHE_LOCK:
                    if BACKLOG_CACHE_RAW is None:
                        aging = process_aging_backlog()
                        treo = process_treo_backlog()
                        BACKLOG_CACHE_RAW = {"aging": aging, "treo": treo}
                import copy
                current_data = copy.deepcopy(BACKLOG_CACHE_RAW)
            
            if "error" not in current_data.get("aging", {}) and "error" not in current_data.get("treo", {}):
                history = load_history()
                baseline_entry = None
                if history:
                    if len(history) >= 2:
                        baseline_entry = history[-2]
                    else:
                        baseline_entry = history[-1]
                current_data["baseline_timestamp"] = baseline_entry["timestamp"] if baseline_entry else None
                current_data = calculate_trend(current_data, baseline_entry)
            result['backlog'] = clean_nan(current_data)
        except Exception as e:
            result['backlog'] = {"error": str(e)}
    else:
        result['backlog'] = {"error": "No permission"}

    # Unstable PO
    if has_perm('tab-unstable-po'):
        try:
            global UNSTABLE_PO_CACHE
            am = None
            if session.get('am_name'):
                am = session.get('am_name')
            if am:
                result['unstablePo'] = process_unstable_po(am=am)
            else:
                with CACHE_LOCK:
                    if UNSTABLE_PO_CACHE is None:
                        UNSTABLE_PO_CACHE = process_unstable_po()
                result['unstablePo'] = UNSTABLE_PO_CACHE
        except Exception as e:
            result['unstablePo'] = {"error": str(e)}
    else:
        result['unstablePo'] = {"error": "No permission"}

    # OFF SPE
    if has_perm('tab-off-spe'):
        try:
            global OFF_SPE_CACHE
            am = None
            if session.get('am_name'):
                am = session.get('am_name')
            if am:
                result['offSpe'] = process_off_spe(am=am)
            else:
                with CACHE_LOCK:
                    if OFF_SPE_CACHE is None:
                        OFF_SPE_CACHE = process_off_spe()
                result['offSpe'] = OFF_SPE_CACHE
        except Exception as e:
            result['offSpe'] = {"error": str(e)}
    else:
        result['offSpe'] = {"error": "No permission"}

    # Volume Creation
    if has_perm('tab-volume-creation'):
        try:
            global DF_TAO_DON_CACHE, DF_BUU_CUC_TYPE_MAP
            with CACHE_LOCK:
                if DF_TAO_DON_CACHE is None:
                    DF_TAO_DON_CACHE = load_vols_tao_don_df()
                if DF_BUU_CUC_TYPE_MAP is None:
                    DF_BUU_CUC_TYPE_MAP = load_buu_cuc_type_map()
            if DF_TAO_DON_CACHE is not None:
                # Delegate to the existing endpoint logic via internal call
                # Use a simplified version here
                result['volumeCreation'] = {"loaded": True}
            else:
                result['volumeCreation'] = {"error": "No vols_tao_don.csv"}
        except Exception as e:
            result['volumeCreation'] = {"error": str(e)}
    else:
        result['volumeCreation'] = {"error": "No permission"}

    # FD
    if has_perm('tab-fd'):
        try:
            global FD_CACHE
            am = None
            if session.get('am_name'):
                am = session.get('am_name')
            if am:
                result['fd'] = clean_nan(process_fd_report(am=am))
            else:
                with CACHE_LOCK:
                    if FD_CACHE is None:
                        FD_CACHE = process_fd_report()
                result['fd'] = clean_nan(FD_CACHE)
        except Exception as e:
            result['fd'] = {"error": str(e)}
    else:
        result['fd'] = {"error": "No permission"}

    # Khach Hang Nhom A
    result['khach_hang_a'] = load_khach_hang_a()

    # Chi Phi Van Tai NCC & KTC
    result['transport_costs'] = load_transport_costs()

    return jsonify(result)

@app.route('/api/files-status')
@requires_permission('tab-sync')
def get_files_status():

    files = [
        'ops_gtc.csv',
        'ops_ltc.csv',
        'ops_co_cau.csv',
        'ops_tts.csv',
        'opr_opr.csv',
        'opr_oe.csv',
        'opr_raw.csv',
        'aging_raw.csv',
        'treo_stuck.csv',
        'buu_cuc_bat_on.csv',
        'off_tuyen_spe.csv',
        'vols_tao_don.csv',
        'co_cau_ntb.csv',
        'ODR TTS.csv',
        'ops_fd.csv',
        'ops_productivity_realtime.csv',
        'ops_nhan_su.csv'
    ]
    status = []
    for f in files:
        path = resolve_path(f, write=False)
        if os.path.exists(path):
            stat = os.stat(path)
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            size_mb = round(stat.st_size / (1024 * 1024), 2)
            status.append({"name": f, "exists": True, "mtime": mtime, "size_mb": size_mb})
        else:
            status.append({"name": f, "exists": False, "mtime": "-", "size_mb": 0})
    return jsonify(status)
@app.route('/api/volume-creation')
@requires_permission('tab-volume-creation')
def get_volume_creation():
    global DF_TAO_DON_CACHE, DF_BUU_CUC_TYPE_MAP
    
    with CACHE_LOCK:
        if DF_TAO_DON_CACHE is None:
            DF_TAO_DON_CACHE = load_vols_tao_don_df()
        if DF_BUU_CUC_TYPE_MAP is None:
            DF_BUU_CUC_TYPE_MAP = load_buu_cuc_type_map()
            
    if DF_TAO_DON_CACHE is None:
        return jsonify({"error": "Không tìm thấy file vols_tao_don.csv. Vui lòng cấu hình Google Sheet và đồng bộ!"}), 404
        
    try:
        df = DF_TAO_DON_CACHE.copy()
        
        province = request.args.get('province')
        district = request.args.get('district')
        ward = request.args.get('ward')
        post_office = request.args.get('post_office')
        customer = request.args.get('customer')
        po_type = request.args.get('po_type')
        date_range = request.args.get('date_range', '7d')
        am = request.args.get('am')
        
        if session.get('am_name'):
            am = session.get('am_name')
            
        df = apply_filters(df, am=am, province=None, post_office=None)
        
        # 1. Compute dynamic dropdown options based on cascaded filtering
        provinces_opt = sorted([str(x) for x in df['Tỉnh'].dropna().unique()])
        
        df_dist = df
        if province:
            df_dist = df_dist[df_dist['Tỉnh'] == province]
        districts_opt = sorted([str(x) for x in df_dist['Quận/Huyện'].dropna().unique()])
        
        df_ward = df_dist
        if district:
            df_ward = df_ward[df_ward['Quận/Huyện'] == district]
        wards_opt = sorted([str(x) for x in df_ward['Phường/Xã'].dropna().unique()])
        
        df_po = df_ward
        if ward:
            df_po = df_po[df_po['Phường/Xã'] == ward]
        post_offices_opt = sorted([str(x) for x in df_po['Bưu cục'].dropna().unique()])
        
        customers_opt = sorted([str(x) for x in df['Khách hàng'].dropna().unique()])
        po_types_opt = ['BC', 'GXT']
        
        # 2. Apply dropdown filters to our dataframe copies
        df_filtered = df.copy()
        if province:
            df_filtered = df_filtered[df_filtered['Tỉnh'] == province]
        if district:
            df_filtered = df_filtered[df_filtered['Quận/Huyện'] == district]
        if ward:
            df_filtered = df_filtered[df_filtered['Phường/Xã'] == ward]
        if post_office:
            df_filtered = df_filtered[df_filtered['Bưu cục'] == post_office]
        if customer:
            df_filtered = df_filtered[df_filtered['Khách hàng'] == customer]
        if po_type:
            if DF_BUU_CUC_TYPE_MAP:
                df_filtered['po_type_mapped'] = df_filtered['warehouse_id'].map(DF_BUU_CUC_TYPE_MAP).fillna('BC')
                df_filtered = df_filtered[df_filtered['po_type_mapped'] == po_type]
            else:
                # Fallback if map not loaded
                pass
                
        latest_dt = df_filtered['Date'].max()
        if pd.isna(latest_dt):
            return jsonify({"error": "Không tìm thấy dữ liệu ngày hợp lệ sau khi lọc."}), 400
            
        # WTD & comparison calculations based on filtered dataset (before date range filter)
        weekday = latest_dt.weekday()
        wtd_start = latest_dt - pd.Timedelta(days=weekday)
        wtd_end = latest_dt
        
        wtd1_start = wtd_start - pd.Timedelta(days=7)
        wtd1_end = latest_dt - pd.Timedelta(days=7)
        
        wtd2_start = wtd_start - pd.Timedelta(days=14)
        wtd2_end = latest_dt - pd.Timedelta(days=14)
        
        def sum_range(df_sub, start, end):
            mask = (df_sub['Date'] >= start) & (df_sub['Date'] <= end)
            return df_sub[mask].groupby('Tỉnh')['Volume'].sum()
            
        wtd_sums = sum_range(df_filtered, wtd_start, wtd_end)
        wtd1_sums = sum_range(df_filtered, wtd1_start, wtd1_end)
        wtd2_sums = sum_range(df_filtered, wtd2_start, wtd2_end)
        
        d_dt = latest_dt
        d1_dt = latest_dt - pd.Timedelta(days=1)
        d2_dt = latest_dt - pd.Timedelta(days=2)
        d7_dt = latest_dt - pd.Timedelta(days=7)
        
        def sum_day(df_sub, dt):
            return df_sub[df_sub['Date'] == dt].groupby('Tỉnh')['Volume'].sum()
            
        d_sums = sum_day(df_filtered, d_dt)
        d1_sums = sum_day(df_filtered, d1_dt)
        d2_sums = sum_day(df_filtered, d2_dt)
        d7_sums = sum_day(df_filtered, d7_dt)
        
        provinces_list = ['Bình Thuận', 'Khánh Hòa', 'Lâm Đồng', 'Ninh Thuận', 'Đắk Nông']
        pivot_rows = []
        
        for p in provinces_list:
            wtd = float(wtd_sums.get(p, 0))
            wtd1 = float(wtd1_sums.get(p, 0))
            wtd2 = float(wtd2_sums.get(p, 0))
            
            d_val = float(d_sums.get(p, 0))
            d1_val = float(d1_sums.get(p, 0))
            d2_val = float(d2_sums.get(p, 0))
            d7_val = float(d7_sums.get(p, 0))
            
            wtd_wtd2 = ((wtd - wtd2) / wtd2 * 100) if wtd2 > 0 else 0.0
            wtd_wtd1 = ((wtd - wtd1) / wtd1 * 100) if wtd1 > 0 else 0.0
            d_d7 = ((d_val - d7_val) / d7_val * 100) if d7_val > 0 else 0.0
            d_d1 = ((d_val - d1_val) / d1_val * 100) if d1_val > 0 else 0.0
            
            pivot_rows.append({
                'province': p,
                'wtd2': int(wtd2),
                'wtd1': int(wtd1),
                'wtd': int(wtd),
                'wtd_wtd2': round(wtd_wtd2, 1),
                'wtd_wtd1': round(wtd_wtd1, 1),
                'd_d7': round(d_d7, 1),
                'd_d1': round(d_d1, 1),
                'd7': int(d7_val),
                'd2': int(d2_val),
                'd1': int(d1_val),
                'd': int(d_val)
            })
            
        total_wtd = sum(r['wtd'] for r in pivot_rows)
        total_wtd1 = sum(r['wtd1'] for r in pivot_rows)
        total_wtd2 = sum(r['wtd2'] for r in pivot_rows)
        total_d = sum(r['d'] for r in pivot_rows)
        total_d1 = sum(r['d1'] for r in pivot_rows)
        total_d2 = sum(r['d2'] for r in pivot_rows)
        total_d7 = sum(r['d7'] for r in pivot_rows)
        
        total_row = {
            'province': 'Tổng cộng',
            'wtd2': int(total_wtd2),
            'wtd1': int(total_wtd1),
            'wtd': int(total_wtd),
            'wtd_wtd2': round(((total_wtd - total_wtd2) / total_wtd2 * 100) if total_wtd2 > 0 else 0.0, 1),
            'wtd_wtd1': round(((total_wtd - total_wtd1) / total_wtd1 * 100) if total_wtd1 > 0 else 0.0, 1),
            'd_d7': round(((total_d - total_d7) / total_d7 * 100) if total_d7 > 0 else 0.0, 1),
            'd_d1': round(((total_d - total_d1) / total_d1 * 100) if total_d1 > 0 else 0.0, 1),
            'd7': int(total_d7),
            'd2': int(total_d2),
            'd1': int(total_d1),
            'd': int(total_d)
        }
        
        kpi_card_data = {
            'latest_date': latest_dt.strftime('%d-%m-%Y'),
            'today_vol': int(total_d),
            'd_d1': round(((total_d - total_d1) / total_d1 * 100) if total_d1 > 0 else 0.0, 1),
            'd_d7': round(((total_d - total_d7) / total_d7 * 100) if total_d7 > 0 else 0.0, 1)
        }
        
        # 3. Apply Date Range filter for the matrix and charts
        df_date_filtered = df_filtered.copy()
        if date_range == '7d':
            start_date = latest_dt - pd.Timedelta(days=6)
            df_date_filtered = df_date_filtered[(df_date_filtered['Date'] >= start_date) & (df_date_filtered['Date'] <= latest_dt)]
        elif date_range == '14d':
            start_date = latest_dt - pd.Timedelta(days=13)
            df_date_filtered = df_date_filtered[(df_date_filtered['Date'] >= start_date) & (df_date_filtered['Date'] <= latest_dt)]
        elif date_range == '30d':
            start_date = latest_dt - pd.Timedelta(days=29)
            df_date_filtered = df_date_filtered[(df_date_filtered['Date'] >= start_date) & (df_date_filtered['Date'] <= latest_dt)]
            
        # Get list of unique dates for matrix and charts
        matrix_dates = sorted(df_date_filtered['Date'].dt.strftime('%Y-%m-%d').unique())
        
        # 4. Compute Matrix Heatmap Data
        matrix_rows = []
        if len(matrix_dates) > 0 and len(df_date_filtered) > 0:
            prov_date_vol = df_date_filtered.groupby(['Tỉnh', df_date_filtered['Date'].dt.strftime('%Y-%m-%d')])['Volume'].sum().unstack(fill_value=0)
            po_date_vol = df_date_filtered.groupby(['Tỉnh', 'Bưu cục', df_date_filtered['Date'].dt.strftime('%Y-%m-%d')])['Volume'].sum().unstack(fill_value=0)
            
            # Ensure all columns exist for all dates
            for d in matrix_dates:
                if d not in prov_date_vol.columns:
                    prov_date_vol[d] = 0
                if d not in po_date_vol.columns:
                    po_date_vol[d] = 0
                    
            for p in sorted(df_date_filtered['Tỉnh'].dropna().unique()):
                p_vols = prov_date_vol.loc[p].to_dict() if p in prov_date_vol.index else {}
                p_total = int(sum(p_vols.values()))
                
                pos_list = []
                if p in po_date_vol.index:
                    p_po_df = po_date_vol.loc[p]
                    for po in sorted(p_po_df.index):
                        po_vols = p_po_df.loc[po].to_dict()
                        po_total = int(sum(po_vols.values()))
                        pos_list.append({
                            'bc': po,
                            'data': {d: int(po_vols.get(d, 0)) for d in matrix_dates},
                            'total': po_total
                        })
                
                matrix_rows.append({
                    'province': p,
                    'data': {d: int(p_vols.get(d, 0)) for d in matrix_dates},
                    'total': p_total,
                    'pos': pos_list
                })
                
        # 5. Customer Group Line Chart Series
        line_series = []
        if len(matrix_dates) > 0 and len(df_date_filtered) > 0:
            cust_daily = df_date_filtered.groupby([df_date_filtered['Date'].dt.strftime('%Y-%m-%d'), 'Khách hàng'])['Volume'].sum().unstack(fill_value=0)
            standard_customers = ['SME', 'Shopee-nhỏ', 'TTS-nhỏ', 'Shopee-Bulky', 'Khác']
            for c in standard_customers:
                if c in cust_daily.columns:
                    c_data = [int(x) for x in cust_daily[c].tolist()]
                else:
                    c_data = [0] * len(matrix_dates)
                line_series.append({
                    'name': c,
                    'data': c_data
                })
                
        # 6. Grouped Bar Chart by Province Series
        bar_series = []
        if len(matrix_dates) > 0 and len(df_date_filtered) > 0:
            prov_daily = df_date_filtered.groupby([df_date_filtered['Date'].dt.strftime('%Y-%m-%d'), 'Tỉnh'])['Volume'].sum().unstack(fill_value=0)
            for p in provinces_list:
                if p in prov_daily.columns:
                    p_data = [int(x) for x in prov_daily[p].tolist()]
                else:
                    p_data = [0] * len(matrix_dates)
                bar_series.append({
                    'name': p,
                    'data': p_data
                })
                
        # 7. Treemap Data sorted by Absolute 7D Growth
        treemap_list = []
        # We compute D vs D-7. D is the latest date in df_filtered, D-7 is latest_dt - 7 days.
        df_d = df_filtered[df_filtered['Date'] == latest_dt]
        df_d7 = df_filtered[df_filtered['Date'] == (latest_dt - pd.Timedelta(days=7))]
        
        if len(df_d) > 0:
            vol_d = df_d.groupby(['Tỉnh', 'Bưu cục'])['Volume'].sum().reset_index()
            vol_d7 = df_d7.groupby('Bưu cục')['Volume'].sum().reset_index()
            
            merged_growth = pd.merge(vol_d, vol_d7, on='Bưu cục', suffixes=('_d', '_d7'), how='left').fillna(0)
            merged_growth['growth_abs'] = merged_growth['Volume_d'] - merged_growth['Volume_d7']
            merged_growth['growth_pct'] = (merged_growth['growth_abs'] / merged_growth['Volume_d7'] * 100).replace(np.inf, 100.0).replace(-np.inf, -100.0).fillna(0)
            
            # Sort by absolute growth descending
            merged_growth = merged_growth.sort_values(by='growth_abs', ascending=False)
            
            for _, row in merged_growth.iterrows():
                treemap_list.append({
                    'name': row['Bưu cục'],
                    'value': int(row['Volume_d']),
                    'province': row['Tỉnh'],
                    'growth_abs': int(row['growth_abs']),
                    'growth_pct': round(float(row['growth_pct']), 1)
                })
                
        return jsonify(clean_nan({
            "kpi": kpi_card_data,
            "table": pivot_rows,
            "total": total_row,
            "filters": {
                "provinces": provinces_opt,
                "districts": districts_opt,
                "wards": wards_opt,
                "post_offices": post_offices_opt,
                "customers": customers_opt,
                "po_types": po_types_opt
            },
            "matrix": {
                "dates": matrix_dates,
                "rows": matrix_rows
            },
            "charts": {
                "line": {
                    "dates": matrix_dates,
                    "series": line_series
                },
                "bar": {
                    "dates": matrix_dates,
                    "series": bar_series
                },
                "treemap": treemap_list
            }
        }))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Lỗi xử lý báo cáo volume tạo đơn: {str(e)}"}), 500

def startup_cache_init():
    update_all_caches()
    try:
        # Initialize history with a sync if it is empty
        history = load_history()
        if not history and BACKLOG_CACHE_RAW:
            aging = BACKLOG_CACHE_RAW["aging"]
            treo = BACKLOG_CACHE_RAW["treo"]
            if "error" not in aging and "error" not in treo:
                add_to_history(aging, treo)
    except Exception as e:
        print(f"Error initializing history: {e}")

# Optimize to run cache initialization on startup thread upon import (for Gunicorn)
# But in local debug mode, only run it once to prevent double execution
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    threading.Thread(target=startup_cache_init, daemon=True).start()

def get_spiking_post_offices():
    global DF_TAO_DON_CACHE
    with CACHE_LOCK:
        if DF_TAO_DON_CACHE is None:
            DF_TAO_DON_CACHE = load_vols_tao_don_df()
    if DF_TAO_DON_CACHE is None:
        return []
        
    df = DF_TAO_DON_CACHE.copy()
    latest_dt = df['Date'].max()
    
    df_d = df[df['Date'] == latest_dt]
    df_d7 = df[df['Date'] == (latest_dt - pd.Timedelta(days=7))]
    
    if len(df_d) == 0 or len(df_d7) == 0:
        return []
        
    vol_d = df_d.groupby(['Tỉnh', 'Bưu cục'])['Volume'].sum().reset_index()
    vol_d7 = df_d7.groupby('Bưu cục')['Volume'].sum().reset_index()
    
    merged_growth = pd.merge(vol_d, vol_d7, on='Bưu cục', suffixes=('_d', '_d7'), how='left').fillna(0)
    merged_growth['growth_abs'] = merged_growth['Volume_d'] - merged_growth['Volume_d7']
    merged_growth['growth_pct'] = (merged_growth['growth_abs'] / merged_growth['Volume_d7'] * 100).replace(np.inf, 100.0).replace(-np.inf, -100.0).fillna(0)
    
    # Filter spikes: growth_abs >= 50 AND growth_pct >= 30%
    spikes = merged_growth[(merged_growth['growth_abs'] >= 50) & (merged_growth['growth_pct'] >= 30.0)]
    spikes = spikes.sort_values(by='growth_abs', ascending=False)
    
    spike_list = []
    for _, row in spikes.iterrows():
        spike_list.append({
            'name': row['Bưu cục'],
            'value': int(row['Volume_d']),
            'province': row['Tỉnh'],
            'growth_abs': int(row['growth_abs']),
            'growth_pct': round(float(row['growth_pct']), 1)
        })
    return spike_list

def send_to_gtalk_bot(message):
    import time
    config = load_config()
    oa_token = config.get("gtalk_oa_token", "").strip()
    channel_id = config.get("gtalk_channel_id", "").strip()
    if not oa_token or not channel_id:
        return False, "Chưa cấu hình GTalk OA Token hoặc Channel ID."
        
    url = "https://mbff.ghn.vn/api/gtalk/send-message"
    client_msg_id = str(int(time.time() * 1000))
    payload = {
        "channelId": channel_id,
        "clientMsgId": client_msg_id,
        "content": {
            "text": message,
            "parseMode": "MARKDOWN"
        },
        "oaToken": oa_token
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15, verify=False)
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get("errorCode") == "success":
                return True, "success"
            return False, res_data.get("error", {}).get("errorMessage", "Unknown error")
        return False, f"HTTP {res.status_code}: {res.text}"
    except Exception as e:
        return False, str(e)

@app.route('/api/send-telegram-warning', methods=['POST'])
@requires_permission('tab-volume-creation')
def send_telegram_warning():
    try:
        config = load_config()
        bot_token = config.get("telegram_bot_token", "").strip()
        chat_id = config.get("telegram_chat_id", "").strip()
        
        # Accept updated config values in body to allow saving & sending at the same time
        data = request.json or {}
        req_token = data.get("telegram_bot_token", "").strip()
        req_chat_id = data.get("telegram_chat_id", "").strip()
        
        if req_token and not ("*" in req_token or "hidden" in req_token.lower()):
            bot_token = req_token
            # Also save it permanently
            save_config({
                "consolidated_url": config.get("consolidated_url", ""),
                "telegram_bot_token": req_token,
                "telegram_chat_id": req_chat_id if req_chat_id else chat_id
            })
        elif req_chat_id and req_chat_id != chat_id:
            chat_id = req_chat_id
            save_config({
                "consolidated_url": config.get("consolidated_url", ""),
                "telegram_bot_token": config.get("telegram_bot_token", ""),
                "telegram_chat_id": req_chat_id
            })
            
        spikes = get_spiking_post_offices()
        
        if spikes:
            items_str = ""
            for idx, item in enumerate(spikes):
                items_str += f"{idx + 1}. *{item['name']}* ({item['province']})\n"
                items_str += f"   - Sản lượng hôm nay: *{item['value']:,}* đơn\n"
                items_str += f"   - Tăng trưởng 7D: *+{item['growth_abs']:,}* đơn (*+{item['growth_pct']}%*)\n\n"
                
            message = (
                f"🚨 *CẢNH BÁO SẢN LƯỢNG TẠO ĐƠN TĂNG ĐỘT BIẾN* 🚨\n"
                f"(So sánh sản lượng hôm nay với 7 ngày trước)\n\n"
                f"Danh sách bưu cục có sản lượng tăng đột biến (>30% và >50 đơn):\n\n"
                f"{items_str}"
                f"📊 *Tổng quan:* Phát hiện {len(spikes)} bưu cục tăng đột biến trong Vùng."
            )
        else:
            message = (
                f"ℹ️ *BÁO CÁO SẢN LƯỢNG TẠO ĐƠN VÙNG* ℹ️\n"
                f"Không phát hiện bưu cục nào có sản lượng tăng đột biến (>30% và >50 đơn) trong 7 ngày qua."
            )
            
        # Send to Telegram if configured
        tele_ok = False
        tele_err = None
        if bot_token and chat_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            try:
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200:
                    tele_ok = True
                else:
                    tele_err = f"Telegram HTTP {res.status_code}"
            except Exception as e:
                tele_err = str(e)
        else:
            tele_err = "Chưa cấu hình Telegram"
                
        # Send to GTalk if configured
        gtalk_ok, gtalk_err = send_to_gtalk_bot(message)
        
        if tele_ok or gtalk_ok:
            msg = "Gửi cảnh báo thành công!"
            if tele_ok and gtalk_ok:
                msg = "Gửi cảnh báo qua Telegram và GTalk thành công!"
            elif tele_ok:
                msg = f"Gửi cảnh báo qua Telegram thành công! (GTalk: {gtalk_err})"
            else:
                msg = f"Gửi cảnh báo qua GTalk thành công! (Telegram: {tele_err})"
            return jsonify({"success": True, "message": msg})
        else:
            return jsonify({"error": f"Gửi thất bại. Telegram: {tele_err} | GTalk: {gtalk_err}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Lỗi gửi tin nhắn: {str(e)}"}), 500

def get_overall_metrics_summary():
    try:
        df_gtc, df_ltc, df_aging, df_treo = get_dataframes(force=True)
        if df_gtc is None or df_ltc is None:
            return None
            
        all_times = set(df_gtc['Time'].dropna().unique()).union(set(df_ltc['Time'].dropna().unique()))
        dates_sorted = sorted(list(all_times), key=lambda x: pd.to_datetime(x.split(' - ')[0]))
        if not dates_sorted:
            return None
            
        latest_date = dates_sorted[-1]
        latest_idx = dates_sorted.index(latest_date)
        n3_date = dates_sorted[latest_idx - 3] if latest_idx >= 3 else None
        
        latest_dt = pd.to_datetime(latest_date.split(' - ')[0])
        lw_date = None
        for d in dates_sorted:
            dt = pd.to_datetime(d.split(' - ')[0])
            if (latest_dt - dt).days == 7:
                lw_date = d
                break
        
        def get_kpi_for_day(date_str):
            if not date_str:
                return None
            gtc_d = df_gtc[df_gtc['Time'] == date_str]
            ltc_d = df_ltc[df_ltc['Time'] == date_str] if date_str in df_ltc['Time'].values else df_ltc[df_ltc['Time'] == df_ltc['Time'].max()]
            
            gtc_vol = gtc_d['Volume'].sum()
            gtc_del = gtc_d['delivered_vol'].sum()
            ltc_vol = ltc_d['Volume'].sum()
            ltc_ltc = ltc_d['ltc_vol'].sum()
            
            return {
                'gtc_pct': round((gtc_del / gtc_vol * 100), 2) if gtc_vol > 0 else 0.0,
                'ltc_pct': round((ltc_ltc / ltc_vol * 100), 2) if ltc_vol > 0 else 0.0,
                'gtc_vol': int(gtc_vol),
                'ltc_vol': int(ltc_vol)
            }
            
        today_kpi = get_kpi_for_day(latest_date)
        n3_kpi = get_kpi_for_day(n3_date) if n3_date else None
        lw_kpi = get_kpi_for_day(lw_date) if lw_date else None
        
        chua_giao = len(df_aging)
        chua_lay = len(df_treo[df_treo['Loại đơn'] == 'Luân chuyển giao'])
        chua_tra = len(df_treo[df_treo['Loại đơn'] == 'Luân chuyển trả'])
        backlog_total = chua_giao + chua_lay + chua_tra
        
        today_gtc_po = df_gtc[df_gtc['Time'] == latest_date].copy()
        today_gtc_po['% GTC'] = (today_gtc_po['delivered_vol'] / today_gtc_po['Volume'] * 100).fillna(0)
        worst_gtc_po = today_gtc_po[today_gtc_po['Volume'] >= 10].sort_values(by='% GTC').head(3)
        
        today_ltc_po = df_ltc[df_ltc['Time'] == latest_date].copy()
        today_ltc_po['% LTC'] = (today_ltc_po['ltc_vol'] / today_ltc_po['Volume'] * 100).fillna(0)
        worst_ltc_po = today_ltc_po[today_ltc_po['Volume'] >= 10].sort_values(by='% LTC').head(3)
        
        worst_gtc_list = []
        for _, r in worst_gtc_po.iterrows():
            worst_gtc_list.append({
                'name': r.get('Chi tiết', 'N/A'),
                'province': r.get('mapped_prov', 'N/A'),
                'vol': int(r.get('Volume', 0)),
                'pct': float(r.get('% GTC', 0.0))
            })
            
        worst_ltc_list = []
        for _, r in worst_ltc_po.iterrows():
            worst_ltc_list.append({
                'name': r.get('Chi tiết', 'N/A'),
                'province': r.get('mapped_prov', 'N/A'),
                'vol': int(r.get('Volume', 0)),
                'pct': float(r.get('% LTC', 0.0))
            })
            
        spikes = get_spiking_post_offices()
        
        return {
            'date': latest_date,
            'today': today_kpi,
            'n3': n3_kpi,
            'lw': lw_kpi,
            'backlog': {
                'total': backlog_total,
                'chua_giao': chua_giao,
                'chua_lay': chua_lay,
                'chua_tra': chua_tra
            },
            'worst_gtc': worst_gtc_list,
            'worst_ltc': worst_ltc_list,
            'spikes': spikes[:5]
        }
    except Exception as e:
        print(f"Error in get_overall_metrics_summary: {e}")
        return None

@app.route('/api/send-telegram-ai-briefing', methods=['POST'])
@requires_permission('tab-volume-creation')
def send_telegram_ai_briefing():
    try:
        config = load_config()
        bot_token = config.get("telegram_bot_token", "").strip()
        chat_id = config.get("telegram_chat_id", "").strip()
        gemini_api_key = config.get("gemini_api_key", "").strip()
        
        print(f"DEBUG IN SERVER BRIEFING: bot_token={bot_token[:10] if bot_token else None}... chat_id={chat_id} gemini_api_key={gemini_api_key[:10] if gemini_api_key else None}...")
        data = request.json or {}
        req_token = data.get("telegram_bot_token", "").strip()
        req_chat_id = data.get("telegram_chat_id", "").strip()
        req_gemini_key = data.get("gemini_api_key", "").strip()
        
        # Save config if changed and not masked
        should_save = False
        updated_config = {
            "consolidated_url": config.get("consolidated_url", ""),
            "telegram_bot_token": config.get("telegram_bot_token", ""),
            "telegram_chat_id": config.get("telegram_chat_id", ""),
            "gemini_api_key": config.get("gemini_api_key", "")
        }
        
        if req_token and not ("*" in req_token or "hidden" in req_token.lower()):
            bot_token = req_token
            updated_config["telegram_bot_token"] = req_token
            should_save = True
            
        if req_chat_id and req_chat_id != chat_id:
            chat_id = req_chat_id
            updated_config["telegram_chat_id"] = req_chat_id
            should_save = True
            
        if req_gemini_key and not ("*" in req_gemini_key or "hidden" in req_gemini_key.lower()):
            gemini_api_key = req_gemini_key
            updated_config["gemini_api_key"] = req_gemini_key
            should_save = True
            
        if should_save:
            save_config(updated_config)
            
        oa_token = config.get("gtalk_oa_token", "").strip()
        channel_id = config.get("gtalk_channel_id", "").strip()
        has_telegram = bool(bot_token and chat_id)
        has_gtalk = bool(oa_token and channel_id)
        
        if not has_telegram and not has_gtalk:
            return jsonify({"error": "Chưa cấu hình Telegram Bot Token hoặc GTalk OA Token."}), 400
            
        if not gemini_api_key:
            return jsonify({"error": "Chưa cấu hình Gemini API Key."}), 400
            
        summary = get_overall_metrics_summary()
        if not summary:
            return jsonify({"error": "Không thể tổng hợp chỉ số vận hành."}), 500
            
        # Format worst post offices strings
        worst_gtc_str = ", ".join([f"{item['name']} ({item['province']}): {item['pct']:.1f}% GTC" for item in summary['worst_gtc']])
        worst_ltc_str = ", ".join([f"{item['name']} ({item['province']}): {item['pct']:.1f}% LTC" for item in summary['worst_ltc']])
        
        # Format volume spikes
        if summary['spikes']:
            spikes_str = "\n".join([f"- {s['name']} ({s['province']}): +{s['growth_abs']:,} đơn (+{s['growth_pct']}%)" for s in summary['spikes']])
        else:
            spikes_str = "Không phát hiện bưu cục tăng đơn đột biến."
            
        # Construct the Prompt for Gemini
        prompt = (
            f"Bạn là một AI Trợ lý Vận hành cao cấp phụ trách Vùng NTB của hệ thống Giao Hàng Nhanh (GHN).\n"
            f"Hãy phân tích dữ liệu vận hành tổng thể ngày {summary['date']} dưới đây và viết một bản tin phân tích cảnh báo đầu ngày gửi cho Group Telegram của Ban điều hành.\n\n"
            f"Dữ liệu vận hành ngày {summary['date']}:\n"
            f"1. Các chỉ số chính (KPI) hôm nay:\n"
            f"   - Giao thành công (% GTC): {summary['today']['gtc_pct']}%\n"
            f"   - Lưu kho thành công (% LTC): {summary['today']['ltc_pct']}%\n"
            f"   - Tổng sản lượng GTC: {summary['today']['gtc_vol']:,} đơn\n"
            f"   - Tổng sản lượng LTC: {summary['today']['ltc_vol']:,} đơn\n\n"
            f"2. So sánh hiệu suất (Tỷ lệ tăng/giảm %):\n"
            f"   - So với 3 ngày trước:\n"
            f"     + GTC: {round(summary['today']['gtc_pct'] - (summary['n3']['gtc_pct'] if summary['n3'] else 0), 2):+}% \n"
            f"     + LTC: {round(summary['today']['ltc_pct'] - (summary['n3']['ltc_pct'] if summary['n3'] else 0), 2):+}% \n"
            f"   - So với tuần trước:\n"
            f"     + GTC: {round(summary['today']['gtc_pct'] - (summary['lw']['gtc_pct'] if summary['lw'] else 0), 2):+}% \n"
            f"     + LTC: {round(summary['today']['ltc_pct'] - (summary['lw']['ltc_pct'] if summary['lw'] else 0), 2):+}% \n\n"
            f"3. Đơn tồn đọng (Backlog):\n"
            f"   - Tổng tồn đọng: {summary['backlog']['total']:,} đơn\n"
            f"     + Chưa giao (Aging): {summary['backlog']['chua_giao']:,} đơn\n"
            f"     + Chưa lấy (Treo giao): {summary['backlog']['chua_lay']:,} đơn\n"
            f"     + Chưa trả (Treo trả): {summary['backlog']['chua_tra']:,} đơn\n\n"
            f"4. Bưu cục cần đặc biệt lưu ý hôm nay (Hiệu suất tệ nhất):\n"
            f"   - Top GTC thấp nhất: {worst_gtc_str}\n"
            f"   - Top LTC thấp nhất: {worst_ltc_str}\n\n"
            f"5. Cảnh báo sản lượng tạo đơn tăng đột biến:\n"
            f"   {spikes_str}\n\n"
            f"Yêu cầu định dạng bản tin gửi Telegram:\n"
            f"- Định dạng Markdown chuẩn của Telegram (sử dụng *chữ đậm*, `chữ code`, biểu tượng emoji thích hợp).\n"
            f"- Tránh sử dụng các ký tự đặc biệt làm lỗi bộ phân tích cú pháp Markdown của Telegram (như dấu ngoặc vuông hoặc dấu gạch dưới đơn lẻ không đóng cặp). Hãy giữ Markdown đơn giản bằng cách dùng dấu * cho chữ đậm và không lồng ghép định dạng.\n"
            f"- Phong cách viết: Chuyên nghiệp, nghiêm túc, tập trung vào hành động nhanh và chỉ rõ các điểm nóng cần khắc phục (đặc biệt lưu ý bưu cục hiệu suất thấp hoặc có sản lượng tăng đột biến).\n"
            f"- Hãy chia rõ 4 phần sau:\n"
            f"  * 📊 *BẢN TIN VẬN HÀNH ĐẦU NGÀY VÙNG NTB* ({summary['date']})\n"
            f"  * ⚠️ *CẢNH BÁO ĐIỂM NÓNG* (Bưu cục yếu kém và backlog cao)\n"
            f"  * 🚨 *CẢNH BÁO SẢN LƯỢNG ĐỘT BIẾN*\n"
            f"  * 💡 *HÀNH ĐỘNG KHUYẾN NGHỊ* (Gợi ý hành động thực tế cho AM và Bưu cục trưởng)"
        )
        
        # Call Gemini REST API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={gemini_api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        res_gemini = None
        try:
            res_gemini = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        except Exception as e:
            print(f"Primary Gemini model failed with exception: {e}. Trying fallback...")
            
        # Fallback to gemini-3.1-flash-lite if primary is unavailable or timed out
        if res_gemini is None or res_gemini.status_code != 200:
            url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={gemini_api_key}"
            try:
                res_gemini = requests.post(url_fallback, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            except Exception as e:
                return jsonify({"error": f"Lỗi từ Gemini API (Fallback cũng thất bại): {str(e)}"}), 500
                
        if res_gemini and res_gemini.status_code == 200:
            gemini_data = res_gemini.json()
            message = gemini_data['candidates'][0]['content']['parts'][0]['text']
        else:
            err_text = res_gemini.text if res_gemini else "No response"
            return jsonify({"error": f"Lỗi từ Gemini API: {err_text}"}), 500
            
        # Send message to Telegram
        url_tele = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload_tele = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        res_tele = requests.post(url_tele, json=payload_tele, timeout=10)
        
        if res_tele.status_code == 200:
            return jsonify({"success": True, "message": "Gửi bản tin phân tích AI đầu ngày thành công!"})
        else:
            # Fallback to plain text if Markdown fails
            payload_tele["parse_mode"] = ""
            res_tele_plain = requests.post(url_tele, json=payload_tele, timeout=10)
            if res_tele_plain.status_code == 200:
                return jsonify({"success": True, "message": "Gửi bản tin phân tích AI thành công (chế độ plain-text do lỗi định dạng Markdown)!"})
            return jsonify({"error": f"Lỗi từ Telegram API: {res_tele.text}"}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Lỗi gửi bản tin AI: {str(e)}"}), 500

@app.route('/api/sync-bc-canh-bao', methods=['GET', 'POST'])
def api_sync_bc_canh_bao():
    try:
        import gspread
        from google.oauth2.credentials import Credentials
        import csv

        root_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = r'C:\Users\lap4all\Documents\Auto report\authorized_user.json'
        if not os.path.exists(creds_path):
            creds_path = os.path.join(root_dir, 'authorized_user.json')

        creds = Credentials.from_authorized_user_file(creds_path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        gc = gspread.authorize(creds)
        sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
        ws = sh.worksheet('BC_canh_bao')
        all_vals = ws.get_all_values()

        update_time = '26/10/2026 20:00:23'
        for r in all_vals[:5]:
            for c in r:
                if 'Thời gian cập nhật' in c:
                    update_time = c.split('Thời gian cập nhật')[-1].strip()

        id_to_am = {}
        id_to_tinh = {}
        co_cau_path = os.path.join(root_dir, 'co_cau_ntb.csv')
        if os.path.exists(co_cau_path):
            with open(co_cau_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        bid = row[0].strip()
                        id_to_tinh[bid] = row[2].strip()
                        id_to_am[bid] = row[3].strip()

        def parse_pct(s):
            try: return float(str(s).replace('%', '').strip())
            except: return 0.0
            
        def parse_int(s):
            try: return int(float(str(s).replace(',', '').strip()))
            except: return 0

        records = []
        for r in all_vals[5:]:
            if len(r) > 4 and r[2].strip():
                bc_id = r[2].strip()
                name = r[3].strip()
                tinh = r[1].strip() or id_to_tinh.get(bc_id, '')
                am = id_to_am.get(bc_id, '')
                
                gtc_7d = parse_pct(r[4])
                gtc_best = parse_pct(r[5])
                gtc_n1 = parse_pct(r[7])
                gtc_n2 = parse_pct(r[9]) if len(r) > 9 else 0.0
                diff = round(gtc_n1 - gtc_n2, 1)
                
                warn_type = r[18].strip() if len(r) > 18 and r[18].strip() else ('Cảnh báo GTC < 45%' if gtc_7d < 45 else 'Cảnh báo GTC < 70% lịch sử')
                days_warn = parse_int(r[19]) if len(r) > 19 else 0
                clear_days = parse_int(r[20]) if len(r) > 20 else 0
                backlog = parse_int(r[23]) if len(r) > 23 else 0
                backlog_5d = parse_int(r[25]) if len(r) > 25 else 0

                records.append({
                    'id': bc_id,
                    'bc': name,
                    'tinh': tinh,
                    'am': am,
                    'gtc_w36': gtc_n2,
                    'gtc_w37': gtc_n1,
                    'diff': diff,
                    'gtc_best': gtc_best,
                    'warn_type': warn_type,
                    'days_warn': days_warn,
                    'backlog': backlog,
                    'backlog_5d': backlog_5d,
                    'clear_days': clear_days
                })

        d_json_p = os.path.join(root_dir, 'data.json')
        d_js_p = os.path.join(root_dir, 'data.js')

        with open(d_json_p, 'r', encoding='utf-8') as f:
            d_all = json.load(f)

        d_all['bc_canh_bao'] = records
        d_all['bc_canh_bao_meta'] = {
            'update_time': update_time,
            'count': len(records),
            'sheet_title': 'NTB - BƯU CỤC BẤT ỔN',
            'worksheet': 'BC_canh_bao',
            'sheet_id': '1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec'
        }

        with open(d_json_p, 'w', encoding='utf-8') as f:
            json.dump(d_all, f, ensure_ascii=False, indent=2)

        with open(d_js_p, 'w', encoding='utf-8') as f:
            f.write('window.DASHBOARD_DATA = ' + json.dumps(d_all, ensure_ascii=False) + ';\n')
            f.write('window.DATA = window.DASHBOARD_DATA;\n')
            f.write('const REPORT_DATA = window.DASHBOARD_DATA;\n')

        return jsonify({
            'success': True,
            'message': f'Đồng bộ thành công {len(records)} bưu cục cảnh báo từ Google Sheets!',
            'records': records,
            'update_time': update_time,
            'count': len(records)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sync-ntbo', methods=['GET', 'POST'])
def sync_ntbo_api():
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        import gspread
        from google.oauth2.credentials import Credentials
        import datetime
        creds_path = r'C:\Users\lap4all\Documents\Auto report\authorized_user.json'
        creds = Credentials.from_authorized_user_file(creds_path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        gc = gspread.authorize(creds)
        sh = gc.open_by_key('1lmQv8KwHJzDFs_RMz64ydu4SOmG3M1YAzILNFGtzFec')
        ws = sh.worksheet('NTBo')
        data = ws.get_all_values()
        
        # update time from row 0
        update_time_str = data[0][2].strip() if len(data[0]) > 2 and data[0][2].strip() else datetime.datetime.now().strftime('%d/%m/%Y')
        
        headers = data[4] if len(data) > 4 else []
        n1_col_name = headers[9].strip() if len(headers) > 9 else 'N-1'

        # Load AM mapping from co_cau_ntb.csv
        id_to_am = {}
        co_cau_path = os.path.join(root_dir, 'co_cau_ntb.csv')
        if os.path.exists(co_cau_path):
            import csv
            with open(co_cau_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        id_to_am[row[0].strip()] = row[3].strip()

        parsed = []
        for r in data[5:]:
            if len(r) >= 15 and r[2].strip():
                bc_id = r[1].strip()
                ten_bc = r[2].strip()
                am = r[0].strip()
                if am == '#N/A' or not am:
                    am = id_to_am.get(bc_id, '---')
                d_latest = r[9].strip() if len(r) > 9 else ''
                gtc_7d_str = r[10].strip()
                gtc_best_str = r[11].strip()
                ratio_str = r[12].strip()
                trang_thai = r[13].strip()
                nguyen_nhan = r[14].strip()

                try: gtc_7d = float(gtc_7d_str.replace('%', ''))
                except: gtc_7d = 0.0
                try: gtc_best = float(gtc_best_str.replace('%', ''))
                except: gtc_best = 0.0
                try: ratio = float(ratio_str.replace('%', ''))
                except: ratio = 0.0
                try: d11_val = float(d_latest.replace('%', ''))
                except: d11_val = 0.0

                gap = round(gtc_best - gtc_7d, 1)

                parsed.append({
                    'am': am, 'id': bc_id, 'ten_bc': ten_bc,
                    'd11': d_latest, 'd11_val': d11_val,
                    'gtc_7d': gtc_7d, 'gtc_7d_str': gtc_7d_str,
                    'gtc_best': gtc_best, 'gtc_best_str': gtc_best_str,
                    'ratio': ratio, 'ratio_str': ratio_str,
                    'gap': gap, 'trang_thai': trang_thai, 'nguyen_nhan': nguyen_nhan
                })

        root_dir = os.path.dirname(os.path.abspath(__file__))
        d_json_p = os.path.join(root_dir, 'data.json')
        d_js_p = os.path.join(root_dir, 'data.js')

        with open(d_json_p, 'r', encoding='utf-8') as f:
            d_all = json.load(f)

        if 'gtc_tong' not in d_all: d_all['gtc_tong'] = {}
        d_all['gtc_tong']['buu_cuc_bat_on'] = parsed
        d_all['gtc_tong']['ntbo_update_time'] = update_time_str
        d_all['gtc_tong']['n1_date_label'] = n1_col_name

        with open(d_json_p, 'w', encoding='utf-8') as f:
            json.dump(d_all, f, ensure_ascii=False, indent=2)

        with open(d_js_p, 'w', encoding='utf-8') as f:
            f.write('window.DASHBOARD_DATA = ' + json.dumps(d_all, ensure_ascii=False) + ';\n')
            f.write('window.DATA = window.DASHBOARD_DATA;\n')
            f.write('const REPORT_DATA = window.DASHBOARD_DATA;\n')

        return jsonify({
            'success': True,
            'message': f'Đồng bộ realtime thành công {len(parsed)} bưu cục từ Sheet NTBo!',
            'update_time': update_time_str,
            'n1_label': n1_col_name,
            'count': len(parsed),
            'bcs': parsed
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/kichban')
def serve_kichban():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, 'KICH_BAN_THUYET_TRINH_W43_NAM_TRUNG_BO.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f"Dashboard server starts on http://0.0.0.0:{port}/")
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=port)



# Trigger rebuild for Kinh Doanh tab in templates/index.html: 2026-09-09

# Trigger rebuild premium KD UI: 1788973037.3088765

# Trigger rebuild Khach Hang A UI v2: 1788973970.3328724

# Trigger rebuild final fix: 1788974309.6102428

# Trigger clean UI items: 1788975027.6002846

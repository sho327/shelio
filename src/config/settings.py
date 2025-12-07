"""
Django settings for src project.
"""

import os
from datetime import datetime
from pathlib import Path

import environ

# ==============================================================================
# SETTINGS FILE INDEX (設定ファイル目次)
# ==============================================================================
# 1. CORE CONFIGURATION           : シークレットキー、デバッグモード、アプリ名などの基本設定
# 2. SECURITY & AUTH FLOW         : ALLOWED_HOSTS、クッキー設定、認証関連URLなどのセキュリティ設定
# 3. APPLICATION DEFINITION       : INSTALLED_APPS、MIDDLEWARE、URLconfなどのアプリ定義
# 4. DATABASE & AUTHENTICATION    : データベース接続、カスタムユーザーモデル、パスワード検証ルール
# 5. TEMPLATES                    : テンプレートエンジンの設定、コンテキストプロセッサ
# 6. I18N & FILE STORAGE          : 国際化、静的ファイル (STATIC)、ユーザーアップロードファイル (MEDIA)
# 7. EXTERNAL SERVICES            : Cloudinary, メール送信設定など外部サービス連携
# 8. LOGGING                      : ロガー、ハンドラ、フォーマット設定
# ==============================================================================


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# env設定
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, ".env"))

# ==============================================================================
# 1. CORE CONFIGURATION
# ==============================================================================
# 基本的なコア設定
SECRET_KEY: str = env("SECRET_KEY")
DEBUG: bool = env.bool("DEBUG", default=False)
APP_NAME = "Loclil"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# 2. SECURITY & AUTH FLOW
# ==============================================================================
# ホスト/プロキシ設定
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"  # クリックジャッキング対策

# セッション/クッキー設定
SESSION_COOKIE_SECURE: bool = env.bool("SESSION_COOKIE_SECURE", default=False)
SESSION_COOKIE_AGE: int = 3660
CSRF_COOKIE_SECURE: bool = env.bool("CSRF_COOKIE_SECURE", default=False)

# 認証フローとトークン設定
LOGIN_URL = "/account/login/"
INITIAL_SETUP_URL = "/account/initial_setup/"
MIN_PASSWORD_LENGTH: int = 8
TOKEN_EXPIRY_SECONDS = {
    "activation": int(os.environ.get("TOKEN_EXPIRY_ACTIVATION_SECONDS", 86400)),
    "password_reset": int(os.environ.get("TOKEN_EXPIRY_PASSWORD_RESET_SECONDS", 3600)),
    # ... 他のトークン種別も追加 ...
}

# ==============================================================================
# 3. APPLICATION DEFINITION
# ==============================================================================
INSTALLED_APPS = [
    # Django 標準 Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # Siteフレームワークの追加
    # 外部パッケージ
    "simple_history",
    # プロジェクト固有 Apps (新しい構成)
    "core",  # 共通機能
    "account",  # アカウント認証・プロフィール機能
    "dashboard",  # ダッシュボード機能
    # "product",
    # "article",
    # "message",
]
SITE_ID = 1

MIDDLEWARE = [
    # 独自ミドルウェア (SameSiteMiddlewareはCSRF/SessionMiddlewareより前に配置)
    "core.middlewares.same_site_middleware.SameSiteMiddleware",
    # Django標準のミドルウェア
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    # --- 認証とセッション ---
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # --- カスタムミドルウェア ---
    # 初期設定ミドルウェア(環境変数の必須チェック等)
    "core.middlewares.initial_setup_required_middleware.InitialSetupRequiredMiddleware",
    # アクセスログ設定ミドルウェア
    "core.middlewares.logging_middleware.LoggingMiddleware",
    # --- その他 ---
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# 特定のシステムチェック警告を非表示にする
SILENCED_SYSTEM_CHECKS = [
    "auth.W004",
]

# ==============================================================================
# 4. DATABASE & AUTHENTICATION
# ==============================================================================
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": BASE_DIR / env("DB_NAME"),
        "ATOMIC_REQUESTS": env.bool("ATOMIC_REQUESTS"),
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE"),
    },
}
# ユーザー認証モデルの設定
AUTH_USER_MODEL = "account.M_User"
AUTHENTICATION_BACKENDS = [
    "core.auth_scheme.user_auth_backend.UserAuthBackend",  # カスタム認証バックエンド
]
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ==============================================================================
# 5. TEMPLATES
# ==============================================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # プロジェクトレベルのtemplatesを登録
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # 共通データのためのカスタムコンテキストプロセッサ
                "core.context_processors.global_data.global_settings",
            ],
        },
    },
]

# ==============================================================================
# 6. I18N & FILE STORAGE
# ==============================================================================
# Internationalization
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# STATIC_URL (必須)
# ブラウザからアクセスする際のURLパス
STATIC_URL = "static/"
# STATICFILES_DIRS (任意)
# アプリケーションフォルダとは別に、静的ファイルを置く場所を指定
# os.path.join(BASE_DIR, 'static') のように記述することが多い
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # 例: プロジェクト直下の assets フォルダ
    # 'C:/Users/user/project/common_static' # 必要に応じて絶対パスも可
]
# STATIC_ROOT (本番運用で必須)
# collectstatic コマンドの出力先ディレクトリ
# STATICFILES_DIRS や アプリケーション内の static フォルダにある全てのファイルがここにコピーされる
STATIC_ROOT = BASE_DIR / "staticfiles"  # デプロイ時に必要

# Media files (ユーザーアップロードファイル)
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# ==============================================================================
# 7. EXTERNAL SERVICES
# ==============================================================================
# Cloudinary (画像アップロードサービス)
USE_CLOUD_STORAGE = False  # ローカルストレージを使うか外部ストレージを使うかのフラグ
CLOUDINARY_CLOUD_NAME: str = env("CLOUDINARY_CLOUD_NAME", default="")
CLOUDINARY_API_KEY: str = env("CLOUDINARY_API_KEY", default="")
CLOUDINARY_API_SECRET: str = env("CLOUDINARY_API_SECRET", default="")
CLOUDINARY_UPLOAD_BASE_PATH: str = env("CLOUDINARY_UPLOAD_BASE_PATH", default="")

# Email
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_FROM = env("EMAIL_FROM", default="noreply@example.com")

# ==============================================================================
# 8. LOGGING
# ==============================================================================
# デバッグログ出力設定フラグ
IS_DEBUG_LOG_OUTPUT: bool = env.bool("IS_DEBUG_LOG_OUTPUT", default=False)

# ファイル名を読み込み時に固定
DEBUG_SQL_LOG_FILENAME = (
    f"{BASE_DIR}/logs/debug/{datetime.now():%Y%m%d}_sql_debug_access.log"
)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    # フォーマットの設定
    "formatters": {
        "access": {
            "format": "[{asctime}] {levelname} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "application": {
            "format": "[{asctime}] {levelname} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    # ハンドラ設定
    "handlers": {
        "handler_access": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/access/access.log",
            "formatter": "access",
            "encoding": "utf-8",
            "when": "MIDNIGHT",
            "backupCount": env.int("ACCESS_LOG_BACKUP_COUNT"),
        },
        "handler_application": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/application/application.log",
            "formatter": "application",
            "encoding": "utf-8",
            "when": "MIDNIGHT",
            "backupCount": env.int("APPLICATION_LOG_BACKUP_COUNT"),
        },
        "handler_debug_db_access": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": DEBUG_SQL_LOG_FILENAME,
            "formatter": "access",
            "encoding": "utf-8",
        },
    },
    # ロガー設定
    "loggers": {
        "logger_access": {
            "handlers": ["handler_access"],
            "level": "DEBUG",
            "propagate": True,
        },
        "logger_application": {
            "handlers": ["handler_application"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.db.backends": {
            # DEBUGモードかつIS_DEBUG_LOG_OUTPUTがTrueの場合のみハンドラを設定
            "handlers": (
                ["handler_debug_db_access"] if DEBUG and IS_DEBUG_LOG_OUTPUT else []
            ),
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

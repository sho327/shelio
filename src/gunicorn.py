import logging
from logging.handlers import TimedRotatingFileHandler

#
# Gunicorn config file
#
wsgi_app = "config.wsgi:application"

# Server Mechanics
# ========================================
# daemon mode
daemon = True

# current directory
# chdir = ''

# Server Socket
# ========================================
bind = "0.0.0.0:8000"

# Worker Processes((CPUコア数×2)+1)
# ========================================
workers = 3

# Thread(1だとファイル通信処理で詰まる可能性もあるので2に設定)
# ========================================
threads = 2

# Logging Handler Configuration
# ========================================
# ローテーションの仕組みを簡単に入れたいので、Gunicorn本来の設定でなく、Pythonの標準ロギング機能に依存した設定とする
# => 将来のGunicornのバージョンアップや、デプロイ環境の変更に伴い、予期せぬタイミングで動かなくなるリスクは存在(その際は本来の設定に戻してローテーションを設定した上で使う)

# --------------- 本来の設定 ---------------
# 1. エラーログの出力先ファイル
# Gunicornが標準エラー出力に書き込んだ内容がここに出力されます。
# errorlog = "logs/gunicorn/app_server_error.log"
# 2. ログレベルの設定
# WARNING以上のメッセージ（サーバー起動エラー、ワーカーエラーなど）のみを出力したい場合
# loglevel = "error"
# 3. アクセスログの無効化 (エラーログのみ必要な場合)
# accesslog = None
# 4. ログフォーマット (オプション: デフォルトで十分なことが多い)※このままコメントでOK
# log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# --------------- 現在の設定 ---------------
# Gunicornのerrorlogディレクティブは無効化（競合を避ける）
errorlog = "-"  # 標準エラー出力に出力（またはNone）
accesslog = None
# Gunicorn内部ロガーの取得
error_logger = logging.getLogger("gunicorn.error")
# DEBUGレベルでログを出力（loglevelディレクティブの代わりにここで設定）
error_logger.setLevel(logging.DEBUG)
# フォーマッタの定義
log_format = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
# TimedRotatingFileHandlerの登録
error_log_handler = TimedRotatingFileHandler(
    filename="logs/gunicorn/error.log",
    when="MIDNIGHT",  # 毎日0時にローテーション
    interval=1,  # 1日ごと
    backupCount=7,  # 7世代保持
    encoding="utf-8",
)
error_log_handler.setFormatter(log_format)
error_logger.addHandler(error_log_handler)

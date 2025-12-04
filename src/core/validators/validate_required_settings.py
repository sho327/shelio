from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

REQUIRED_SETTINGS = [
    "EMAIL_FROM",
    "TOKEN_EXPIRY_SECONDS",
    "INITIAL_SETUP_URL",
    # 他の必須設定もここに追加
]


def validate_required_settings():
    """
    REQUIRED_SETTINGSリストに含まれる設定がsettings.pyで定義されているかチェックする。
    """
    missing_settings = []

    for setting_name in REQUIRED_SETTINGS:
        if not hasattr(settings, setting_name):
            missing_settings.append(setting_name)

    if missing_settings:
        raise ImproperlyConfigured(
            f"以下の必須設定がsettings.pyに定義されていません: {', '.join(missing_settings)}"
        )

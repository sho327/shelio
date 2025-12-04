from django.conf import settings


# --------------------------------------------------
# Context Processor 関数本体(テンプレートに共通的に渡すパラメータ)
# --------------------------------------------------
def global_settings(request):
    """
    全てのテンプレートにサイト共通の定数や設定値を渡すコンテキストプロセッサ。
    """
    user = request.user
    is_authenticated = user.is_authenticated
    # settings.pyで定義した TOKEN_EXPIRY_SECONDS を参照する
    token_expiry = getattr(settings, "TOKEN_EXPIRY_SECONDS", {})
    # ユーザーがログインしているかどうかにかかわらず、全テンプレートで参照可能
    return {
        "SITE_NAME": settings.APP_NAME,
        # メンテナンスモードなどのアプリケーション設定
        "MAINTENANCE_MODE": False,
        # トークン有効期限などの定数
        "TOKEN_EXPIRY": token_expiry,
        # サーバー設定 (本番ではFalse)
        "APP_DEBUG_MODE": settings.DEBUG,
        # ユーザー権限 (管理者か否か)
        "IS_ADMIN": is_authenticated and user.is_superuser,
        # IS_AUTHENTICATEDはテンプレートからも簡単に確認可能(テンプレート変数を使っても冗長にならないのでここに含めない)
    }

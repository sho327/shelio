from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

INITIAL_SETUP_URL = settings.INITIAL_SETUP_URL
# 初回設定チェックから除外するURLの'name'を定義
# (URLパスではなく、urls.pyで定義したURL名)
EXEMPT_URL_NAMES = [
    "login",
    "logout",
    "account:initial_setup",  # 初回設定画面自体は必ず除外
    # 'admin:index',         # 管理画面を除外する場合
]


class InitialSetupRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.initial_setup_url = INITIAL_SETUP_URL

    def __call__(self, request):
        # 処理は process_view で行うため、ここでは get_response を呼ぶだけ
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user

        # 1. 未認証ユーザーは処理しない (LoginRequiredMixinが別途処理するため)
        if not user.is_authenticated:
            return None

        # 2. 初回設定が完了している場合は処理しない
        if not user.is_first_login:
            return None

        # 3. 除外パスのチェック (ミドルウェアが無限ループを防ぐ最重要ロジック)
        try:
            # 現在のURLを解決し、URL名を取得
            resolved = resolve(request.path)
            current_url_name = resolved.url_name

            # URL名が除外リストに含まれているか、またはパスが静的ファイルでないかチェック
            if resolved.view_name in EXEMPT_URL_NAMES or request.path.startswith(
                "/static/"
            ):
                return None  # 除外パスなので処理を続行

        except Resolver404:
            # 存在しないパス（404）の場合は処理を続行
            return None
        except AttributeError:
            # 名前付きURLでない場合 (resolved.url_name がない場合) はスキップ
            # 例外的なケースなので、基本は None を返す
            return None

        # 4. 初回設定が必要 (is_first_login=True) で、かつ除外パスではない場合
        # 強制的に初回設定画面へリダイレクト
        return redirect(self.initial_setup_url)

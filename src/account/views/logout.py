from audioop import reverse

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View


class LogoutView(View):
    """
    ユーザーをログアウトさせ、ログインページにリダイレクトするビュー。
    """

    # ログアウト後のリダイレクト先 (通常はログインページ)
    # reverse_lazy を使うことで、URLがまだ読み込まれていなくても安全に参照できます
    redirect_url = reverse_lazy("account:login")

    def get(self, request):
        try:
            # Django標準のログアウト関数を呼び出す
            logout(request)
            messages.success(request, "ログアウトしました。")

        except Exception:
            # ログアウト処理中のシステムエラー（セッション削除失敗など）
            messages.error(request, "ログアウト処理中にエラーが発生しました。")
            # ログ記録推奨

        return redirect(reverse("account:login"))

    # ユーザーが誤ってログアウトリンクを画像として貼った場合のセキュリティ対策
    def post(self, request):
        return self.get(request)

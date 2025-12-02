# LoginView ではなく FormView をインポート
from django.conf import settings
from django.contrib.auth import login
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from account.exceptions import AccountLockedException, AuthenticationFailedException
from account.forms.login import CustomAuthenticationForm

# AuthServiceとカスタム例外をインポート
from account.services.auth_service import AuthService
from core.decorators.logging_sql_queries import logging_sql_queries


class CustomLoginView(FormView):
    form_class = CustomAuthenticationForm
    template_name = "account/login.html"
    success_url = reverse_lazy("dashboard")

    # FormViewが持つ成功時のURL取得メソッドを利用
    def get_success_url(self):
        # ログイン成功後のリダイレクト先を返す
        return self.success_url

    # 認証成功時に呼び出されるメソッドをオーバーライド
    @logging_sql_queries(process_name="login")
    def form_valid(self, form: CustomAuthenticationForm) -> HttpResponseRedirect:
        """
        フォームのバリデーションが成功した後、AuthServiceを使用して認証を試みる。
        """
        email = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        auth_service = AuthService()

        try:
            # 1. AuthServiceのカスタムログインロジックを実行
            user = auth_service.login(email=email, password=password)

            # 2. 認証成功: Django標準のlogin関数でセッションを確立
            login(self.request, user)

            # 3. remember_me のセッション制御
            remember_me = form.cleaned_data.get("remember_me")
            if not remember_me:
                self.request.session.set_expiry(0)
            else:
                self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)

            # 4. 成功後のリダイレクト処理 (FormViewの標準動作)
            # return super().form_valid(form) の代わりに、直接リダイレクトを返す
            return redirect(self.get_success_url())

        except (AuthenticationFailedException, AccountLockedException) as e:
            # 5. 認証失敗: エラーメッセージをフォームに追加し、再レンダリング

            error_message = "メールアドレスまたはパスワードが正しくありません。"
            if isinstance(e, AccountLockedException):
                error_message = "アカウントはロックされているか、無効化されています。"

            # フォーム全体のエラーとして追加
            form.add_error(None, error_message)

            # form_invalidを呼び出し、エラーメッセージとともにテンプレートを再レンダリング
            # return self.form_invalid(form) は FormView の標準的なエラー処理
            return self.form_invalid(form)

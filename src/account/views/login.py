# LoginView ではなく FormView をインポート
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from account.exceptions import AccountLockedException, AuthenticationFailedException
from account.forms.login import AuthenticationForm

# AuthServiceとカスタム例外をインポート
from account.services.auth_service import AuthService
from core.decorators.logging_sql_queries import logging_sql_queries
from core.exceptions import IntegrityError

process_name = "LoginView"


class LoginView(FormView):
    form_class = AuthenticationForm
    template_name = "account/login.html"
    success_url = reverse_lazy("dashboard")
    INITIAL_SETUP_URL = reverse_lazy("account:initial_setup")

    # FormViewが持つ成功時のURL取得メソッドを利用
    def get_success_url(self):
        # ログイン成功後のリダイレクト先を返す
        return self.success_url

    # 認証成功時に呼び出されるメソッドをオーバーライド
    @logging_sql_queries(process_name=process_name)
    def form_valid(self, form: AuthenticationForm) -> HttpResponseRedirect:
        """
        フォームのバリデーションが成功した後、AuthServiceを使用して認証を試みる。
        """
        email = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        auth_service = AuthService()

        try:
            # 1. AuthServiceのカスタムログインロジックを実行
            user = auth_service.login(email=email, password=password)
            is_first_login = user.is_first_login

            # 2. 認証成功: Django標準のlogin関数でセッションを確立
            login(self.request, user)
            if is_first_login:
                final_redirect_url = self.INITIAL_SETUP_URL  # 初期設定URLへ
            else:
                final_redirect_url = self.get_success_url()  # 通常のダッシュボードへ

            # 3. remember_me のセッション制御
            remember_me = form.cleaned_data.get("remember_me")
            if not remember_me:
                self.request.session.set_expiry(0)
            else:
                self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)

            # 4. 成功後のリダイレクト処理 (FormViewの標準動作)
            # return super().form_valid(form) の代わりに、直接リダイレクトを返す
            return redirect(final_redirect_url)

        except AuthenticationFailedException:
            # ユーザーフレンドリーなエラーメッセージをフォームに付加
            form.add_error(None, "メールアドレスまたはパスワードが正しくありません。")
            return self.form_invalid(form)  # フォーム再表示

        except AccountLockedException:
            form.add_error(
                None,
                "このアカウントは現在利用できません。管理者にお問い合わせください。",
            )
            return self.form_invalid(form)  # フォーム再表示

        except IntegrityError:
            form.add_error(
                None,
                "システムエラーが発生しました。時間をおいて再度お試しください。",
            )
            return self.form_invalid(form)  # フォーム再表示

        except Exception:
            # ログ記録推奨
            form.add_error(None, "予期せぬエラーが発生しました。")
            return self.form_invalid(form)  # フォーム再表示

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
from core.consts import LOG_METHOD
from core.decorators.logging_sql_queries import logging_sql_queries
from core.exceptions import IntegrityError
from core.utils.log_helpers import log_output_by_msg_id

process_name = "LoginView"


class LoginView(FormView):
    form_class = AuthenticationForm
    template_name = "account/login.html"
    success_url = reverse_lazy("dashboard:dashboard")
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

        except AuthenticationFailedException as e:
            # ログ出力: 認証失敗を記録
            log_output_by_msg_id(
                log_id="MSGE201",
                params=[email, e.message_id, e.message],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            # 例外クラスで定義されたメッセージを使用
            form.add_error(None, e.message)
            return self.form_invalid(form)  # フォーム再表示

        except AccountLockedException as e:
            # ログ出力: アカウントロックを記録
            log_output_by_msg_id(
                log_id="MSGE202",
                params=[email, e.message_id],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            # 例外クラスで定義されたメッセージを使用
            form.add_error(None, e.message)
            return self.form_invalid(form)  # フォーム再表示

        except IntegrityError as e:
            # ログ出力: データベース整合性エラーを記録
            log_output_by_msg_id(
                log_id="MSGE203",
                params=[email, e.message_id, str(e.details)],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            # 例外クラスで定義されたメッセージを使用
            form.add_error(None, e.message)
            return self.form_invalid(form)  # フォーム再表示

        except Exception as e:
            # ログ出力: 予期せぬエラーを記録（スタックトレースを含む）
            error_detail = f"ログイン処理中にエラーが発生しました。メールアドレス: {email} エラー: {str(e)}"
            log_output_by_msg_id(
                log_id="MSGE002",
                params=[error_detail],
                logger_name=LOG_METHOD.APPLICATION.value,
                exc_info=True,  # 予測不可能なエラーのためスタックトレースを含める
            )
            form.add_error(None, "予期せぬエラーが発生しました。")
            return self.form_invalid(form)  # フォーム再表示

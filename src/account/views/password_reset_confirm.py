from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView

from account.exceptions import PasswordResetTokenInvalidException
from account.forms.password_reset_confirm import PasswordResetConfirmForm
from account.services.auth_service import AuthService
from core.exceptions import IntegrityError


# パスワードリセット確認＆実行ビュー(トークン検証とパスワード設定)
class PasswordResetConfirmView(FormView):
    template_name = "account/password_reset_confirm.html"
    form_class = PasswordResetConfirmForm
    # 成功後はログイン画面へリダイレクト
    success_url = reverse_lazy("account:login")

    def dispatch(self, request, *args, **kwargs):
        # URLからトークンを取得し、このビューインスタンスに保存
        self.token_value = kwargs.get("token_value")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレートにトークンを渡す（例: フォームのhiddenフィールドなど）
        context["token_value"] = self.token_value
        return context

    def form_valid(self, form):
        new_password = form.cleaned_data["new_password1"]
        auth_service = AuthService()

        try:
            # サービス層でトークン検証とパスワード更新を実行
            auth_service.reset_password(self.token_value, new_password)

            # 成功メッセージを設定し、ログイン画面へリダイレクト
            # messages.success(
            #     self.request,
            #     "パスワードが正常にリセットされました。新しいパスワードでログインしてください。",
            # )
            return super().form_valid(form)

        except PasswordResetTokenInvalidException:
            # トークンが無効または期限切れの場合
            # messages.error(
            #     self.request,
            #     "このリセットリンクは無効か、または期限が切れています。お手数ですが、再度パスワードリセットを要求してください。",
            # )
            form.add_error(
                None,
                "このリセットリンクは無効か、または期限が切れています。お手数ですが、再度パスワードリセットを要求してください。",
            )

            # エラー発生時はリセット要求画面に戻す
            return redirect(reverse("account:password_reset_request"))

        except IntegrityError:  # ⭐ 追加で捕捉 ⭐
            # messages.error(
            #     self.request,
            #     "システム処理中にエラーが発生しました。時間をおいて再度お試しください。",
            # )
            form.add_error(
                None,
                "システム処理中にエラーが発生しました。時間をおいて再度お試しください。",
            )
            return redirect(reverse("account:login"))  # またはエラー画面へリダイレクト

        except Exception as e:
            # 予期せぬエラー (DBエラーなど)
            # messages.error(
            #     self.request,
            #     "パスワードリセット中にシステムエラーが発生しました。時間をおいて再度お試しください。",
            # )
            # ログ記録推奨
            form.add_error(
                None,
                "パスワードリセット中に予期せぬエラーが発生しました。時間をおいて再度お試しください。",
            )
            # log_output_by_msg_id(...)
            return redirect(reverse("account:login"))  # 安全のためログイン画面に戻す

from audioop import reverse

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from account.forms.password_reset_request import PasswordResetRequestForm
from account.services.auth_service import AuthService
from core.exceptions import ExternalServiceError, IntegrityError


# パスワードリセット要求ビュー (メールアドレス入力)
class PasswordResetRequestView(FormView):
    template_name = "account/password_reset_request.html"
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy("account:password_reset_pending")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        auth_service = AuthService()

        try:
            # サービスに処理を委譲。ユーザーの有無にかかわらず成功を返す（列挙攻撃対策）。
            auth_service.request_password_reset(email)

            # 成功メッセージを設定（ユーザーがメールをチェックすべきことを通知）
            # messages.info(self.request, "パスワード再設定用のメールを送信しました。")

            return super().form_valid(form)

        except IntegrityError:
            # DB関連のシステムエラー
            # messages.error(
            #     self.request,
            #     "システムエラーが発生しました。時間をおいて再度お試しください。",
            # )
            form.add_error(
                None,
                "システムエラーが発生しました。時間をおいて再度お試しください。",
            )
            return redirect(
                reverse("account:login")
            )  # ユーザーを安全な場所へリダイレクト

        except ExternalServiceError:
            # メール送信に失敗した場合のエラー
            # messages.error(
            #     self.request,
            #     "メール送信サービスに問題が発生しました。時間をおいて再度お試しください。",
            # )
            form.add_error(
                None,
                "メール送信サービスに問題が発生しました。時間をおいて再度お試しください。",
            )
            return redirect(reverse("account:login"))

        except Exception:
            # 予期せぬ全てのエラー
            # messages.error(self.request, "予期せぬエラーが発生しました。")
            form.add_error(
                None,
                "予期せぬエラーが発生しました。",
            )
            return redirect(reverse("account:login"))

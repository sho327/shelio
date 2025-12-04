from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from account.exceptions import (
    TokenExpiredOrNotFoundException,
    UserAlreadyActiveException,
)
from account.services.auth_service import AuthService


class ActivateUserView(View):
    """
    メールに記載されたトークンを使ってユーザーアカウントを有効化する。
    """

    def get(self, request, token_value):
        auth_service = AuthService()

        try:
            # サービス層でアカウントを有効化
            user = auth_service.activate_user(raw_token_value=token_value)

            # 成功: ユーザーを強制的にログインさせる (UX向上のためオプション)
            login(self.request, user)

            # 成功画面へリダイレクト
            return redirect(reverse("dashboard:dashboard"))

        except TokenExpiredOrNotFoundException:
            # トークンが無効または期限切れの場合
            context = {
                "error_title": "無効なリンク",
                "error_message": "このアクティベーションリンクは無効か、期限が切れています。",
                "can_retry": True,
            }
            return render(
                request, "account/activate_user_failed.html", context, status=400
            )

        except UserAlreadyActiveException:
            # 既に有効化済みの場合
            context = {
                "message_title": "既に有効化済み",
                "message_body": "このアカウントは既に有効化されています。ログインしてください。",
            }
            # 既にログイン済みの可能性もあるため、200 OK でメッセージを返す
            return render(
                request, "account/activate_user_success.html", context, status=200
            )

        except Exception:
            # その他のシステムエラー
            context = {
                "error_title": "システムエラー",
                "error_message": "アカウントの有効化中に予期せぬエラーが発生しました。",
                "can_retry": False,
            }
            return render(
                request, "account/activate_user_failed.html", context, status=500
            )

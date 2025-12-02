from core.exceptions import ApplicationError


class AccountError(ApplicationError):
    """
    ユーザーアカウント（Account）ドメインにおける全てのビジネス例外の基底クラス。
    """

    default_message = "アカウント関連の処理中にエラーが発生しました。"
    message_id = "ERR_ACC_000"


class UserNotFoundException(AccountError):
    """
    指定されたユーザーが見つからない場合に発生。
    例: 存在しないIDでプロフィールを取得しようとした場合など。
    """

    default_message = "指定されたユーザーアカウントが見つかりません。"
    message_id = "ERR_ACC_101"


class TokenExpiredOrNotFoundException(AccountError):
    """
    アクティベーショントークンが無効である、または期限が切れている場合に発生。
    """

    default_message = "無効または期限切れのアクティベーション・トークンです。"
    message_id = "ERR_ACC_102"


class UserAlreadyActiveException(AccountError):
    """
    既に有効化済みのユーザーに対して、再度アクティベーションを行おうとした場合に発生。
    """

    default_message = "このアカウントは既に有効化されています。"
    message_id = "ERR_ACC_103"


class EmailDuplicationError(AccountError):
    """メールアドレスが既に登録されている場合に発生"""

    default_message = "このメールアドレスは既に登録されています。"
    message_id = "ERR_ACC_104"


class AuthenticationFailedException(AccountError):
    """メールアドレスまたはパスワードが誤っている場合"""

    default_message = "メールアドレスまたはパスワードが正しくありません。"
    message_id = "ERR_AUTH_001"


class AccountLockedException(AccountError):
    """アカウントがロックまたは凍結されている場合"""

    default_message = "このアカウントは現在利用できません。"
    message_id = "ERR_AUTH_002"


class PasswordResetTokenInvalidException(AccountError):
    """パスワードリセットトークンが無効または期限切れの場合"""

    default_message = (
        "無効なパスワードリセットリンクです。もう一度手続きを行ってください。"
    )
    message_id = "ERR_AUTH_003"


# サービス層での利用
# raise TokenExpiredOrNotFoundException(details={"token": raw_token_value})


# Django REST FrameworkのAPIViewのイメージ
# from django.http import JsonResponse, Http404
# # 例外のインポートを仮定
# from account.exceptions import TokenExpiredOrNotFoundException, UserAlreadyActiveException

# class UserActivationAPIView(APIView):
#     def post(self, request, token_value):
#         user_service = M_UserService()

#         try:
#             # サービスメソッドを呼び出す
#             user = user_service.activate_user(raw_token_value=token_value)

#             return JsonResponse({
#                 "message": f"ユーザー {user.email} は正常にアクティブ化されました。",
#                 "status": "success"
#             }, status=200)

#         except TokenExpiredOrNotFoundException:
#             # 404/400として処理
#             return JsonResponse({
#                 "message": "無効または期限切れのトークンです。",
#                 "status": "error"
#             }, status=400)

#         except UserAlreadyActiveException:
#             return JsonResponse({
#                 "message": "アカウントは既に有効化されています。",
#                 "status": "warning"
#             }, status=200)

#         except Exception as e:
#             # その他の予期せぬエラー
#             return JsonResponse({
#                 "message": "サーバーエラーが発生しました。",
#                 "error": str(e)
#             }, status=500)

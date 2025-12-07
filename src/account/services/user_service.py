from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from account.repositories.m_user_profile_repository import M_UserProfileRepository
from account.repositories.m_user_repository import M_UserRepository
from account.repositories.t_user_token_repository import T_UserTokenRepository
from core.consts import LOG_METHOD
from core.exceptions import ExternalServiceError, IntegrityError
from core.services.storage_service import StorageService

# import cloudinary.uploader # ⚠️ 本番環境でのみ有効化/呼び出しを検討

User = get_user_model()


class UserService:
    """
    ユーザーのライフサイクル（作成、有効化、更新、退会）に関する
    ビジネスロジックを担うクラス
    """

    def __init__(self):
        # 必要なRepositoryを依存性注入
        self.user_repo = M_UserRepository()
        self.profile_repo = M_UserProfileRepository()
        self.token_repo = T_UserTokenRepository()
        self.storage_service = StorageService()

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------
    def _handle_icon_upload(
        self, user_instance: User, uploaded_file: Optional[UploadedFile]
    ) -> Optional[str]:
        """
        ファイルを環境に応じて処理し、DBに格納すべきパスまたはURL/IDを返す。
        """
        if not uploaded_file:
            return None

        if settings.USE_CLOUD_STORAGE:
            # 1. 本番環境 (Cloudinary/S3へのアップロード処理)
            # StorageServiceを使用（ExternalServiceErrorを直接投げる）
            folder_path = f"user_icons/{user_instance.pk}"
            filename = uploaded_file.name
            file_url = self.storage_service.upload_file(
                uploaded_file, folder_path, filename
            )
            return file_url

        else:
            # 2. 開発環境 (ローカルストレージに任せる)
            # FileFieldがローカルに保存できるよう、ファイルオブジェクトをそのまま返す
            return uploaded_file

    # ------------------------------------------------------------------
    # ユーザ初回ログイン時初期設定
    # ------------------------------------------------------------------
    @transaction.atomic
    def initial_setup(
        self,
        user: User,
        display_name: str,
        is_public: bool,
        is_email_notify_enabled: bool,
        icon_file: Optional[UploadedFile] = None,
    ) -> User:
        """
        ユーザーの初回設定を更新し、is_first_loginフラグをFalseに設定する。
        """
        try:
            # 1. UserProfileの存在チェックと取得 (シグナルで作成されている前提だが安全策)
            profile = self.profile_repo.get_alive_one_or_none(m_user=user.pk)
            if not profile:
                # ユーザーに関連付けられたプロフィールがない場合、作成
                profile = self.profile_repo.create(m_user=user)

            # 2. アイコンファイルの処理: DBに格納すべき値を取得
            icon_value = self._handle_icon_upload(user, icon_file)

            # 3. UserProfileの更新データ辞書を作成
            update_data = {
                "display_name": display_name,
                "is_public": is_public,
                "is_email_notify_enabled": is_email_notify_enabled,
                # 個別通知フラグ名もモデルに合わせる
                "is_notify_like": is_email_notify_enabled,
                "is_notify_comment": is_email_notify_enabled,
                "is_notify_follow": is_email_notify_enabled,
            }

            # アイコンが設定された場合のみ追加
            if icon_value is not None:
                update_data["icon"] = icon_value

            # 4. UserProfileの更新実行
            self.profile_repo.update(profile, **update_data)

            # 5. is_first_loginフラグの更新
            if user.is_first_login:
                updated_user = self.user_repo.update(
                    user,
                    is_first_login=False,
                    # M_Userのupdated_methodフィールドを設定
                    updated_method="INITIAL_SETUP",  # LOG_METHOD.INITIAL_SETUPが存在しないため文字列を直接指定
                )
            else:
                updated_user = user

            return updated_user

        except ExternalServiceError:
            raise
        except Exception as e:
            # サービス層ではログ出力せず、例外を投げるだけ（ビュー層でログ出力）
            # より詳細なエラー情報を含める
            raise IntegrityError(
                message="初回設定の更新中に予期せぬエラーが発生しました。",
                details={
                    "internal_message": str(e),
                    "error_type": type(e).__name__,
                    "user_id": str(user.pk) if user else "unknown",
                },
            )

    # ------------------------------------------------------------------
    # プロフィール更新処理
    # ------------------------------------------------------------------
    @transaction.atomic
    def update_profile(
        self,
        user: User,
        display_name: Optional[str] = None,
        bio: Optional[str] = None,
        career_history: Optional[str] = None,
        location: Optional[str] = None,
        skill_tags_raw: Optional[str] = None,
        github_link: Optional[str] = None,
        x_link: Optional[str] = None,
        portfolio_blog_link: Optional[str] = None,
        is_public: Optional[bool] = None,
        is_email_notify_enabled: Optional[bool] = None,
        is_notify_like: Optional[bool] = None,
        is_notify_comment: Optional[bool] = None,
        is_notify_follow: Optional[bool] = None,
        icon_file: Optional[UploadedFile] = None,
    ) -> User:
        """
        ユーザープロフィールを更新する。
        """
        try:
            # 1. UserProfileの存在チェックと取得
            profile = self.profile_repo.get_alive_one_or_none(m_user=user.pk)
            if not profile:
                # ユーザーに関連付けられたプロフィールがない場合、作成
                profile = self.profile_repo.create(m_user=user)

            # 2. アイコンファイルの処理: DBに格納すべき値を取得
            icon_value = self._handle_icon_upload(user, icon_file)

            # 3. UserProfileの更新データ辞書を作成（Noneでない値のみ更新）
            update_data = {}
            if display_name is not None:
                update_data["display_name"] = display_name
            if bio is not None:
                update_data["bio"] = bio
            if career_history is not None:
                update_data["career_history"] = career_history
            if location is not None:
                update_data["location"] = location
            if skill_tags_raw is not None:
                update_data["skill_tags_raw"] = skill_tags_raw
            if github_link is not None:
                update_data["github_link"] = github_link
            if x_link is not None:
                update_data["x_link"] = x_link
            if portfolio_blog_link is not None:
                update_data["portfolio_blog_link"] = portfolio_blog_link
            if is_public is not None:
                update_data["is_public"] = is_public
            if is_email_notify_enabled is not None:
                update_data["is_email_notify_enabled"] = is_email_notify_enabled
            if is_notify_like is not None:
                update_data["is_notify_like"] = is_notify_like
            if is_notify_comment is not None:
                update_data["is_notify_comment"] = is_notify_comment
            if is_notify_follow is not None:
                update_data["is_notify_follow"] = is_notify_follow

            # アイコンが設定された場合のみ追加
            if icon_value is not None:
                update_data["icon"] = icon_value

            # 4. UserProfileの更新実行
            if update_data:
                self.profile_repo.update(profile, **update_data)

            return user

        except ExternalServiceError:
            raise
        except Exception as e:
            # サービス層ではログ出力せず、例外を投げるだけ（ビュー層でログ出力）
            raise IntegrityError(
                message="プロフィールの更新中に予期せぬエラーが発生しました。",
                details={
                    "internal_message": str(e),
                    "error_type": type(e).__name__,
                    "user_id": str(user.pk) if user else "unknown",
                },
            )

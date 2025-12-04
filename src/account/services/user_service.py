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
from core.utils.log_helpers import log_output_by_msg_id

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

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------
    # ※ このヘルパーメソッドは、DBに格納すべき値を返す役割に特化させます
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
            try:
                # ⚠️ 実際にはここで Cloudinary API を叩き、ファイルを送信する
                # 例: result = cloudinary.uploader.upload(uploaded_file)
                #     return result['secure_url']

                # DBにはその参照IDやURLを格納する
                cloud_id = f"cloudinary_id/{user_instance.pk}_{uploaded_file.name}"
                return cloud_id

            except Exception as e:
                # アップロード失敗時のエラー処理
                # ログ記録推奨
                raise ExternalServiceError(message=f"Cloudinaryアップロード失敗: {e}")

        else:
            # 2. 開発環境 (Djangoのデフォルトストレージに任せる)
            # ModelForm経由で渡されたUploadedFileオブジェクト自体を返します。
            # profile.icon = uploaded_file とすることで、後続の profile.save() が
            # ローカルストレージへの保存を自動で処理します。
            return uploaded_file  # ファイルオブジェクトをそのまま返す

    # ------------------------------------------------------------------
    # ユーザ初回ログイン時初期設定
    # ------------------------------------------------------------------
    @transaction.atomic
    def initial_setup(
        self,
        user: User,
        profile_data: Dict[str, Any],
        icon_file: Optional[UploadedFile] = None,
    ) -> User:
        """
        ユーザーの初回設定を更新し、is_first_loginフラグをFalseに設定する。
        Args:
            user (User): 更新対象のユーザーインスタンス
            profile_data (Dict[str, Any]): プロフィールと設定データ
            icon_file (Optional[UploadedFile]): アップロードされたアイコンファイル
        Returns:
            User: 更新されたユーザーインスタンス
        Raises:
            IntegrityError: データベース操作中にエラーが発生した場合
        """
        try:
            # 1. UserProfileの存在チェックと取得
            # OneToOneFieldのため、通常はユーザー作成時に紐づくプロフィールも作成されているはず
            # ModelFormを使う場合、user.user_profile は存在することが前提
            profile = self.profile_repo.get_alive_one_or_none(m_user=user.pk)
            if not profile:
                # プロフィールが存在しない場合は、ここで強制的に作成します
                profile = self.profile_repo.create(m_user=user)

            # 2. アイコンファイルの処理とデータへの追加
            icon_value = self._handle_icon_upload(user, icon_file)

            if icon_value is not None:
                # ModelFormのcleaned_dataのように扱えるよう、辞書に追加
                profile_data["icon"] = icon_value
            elif icon_file is False:
                # フォームでクリア（削除）の意図があった場合（今回は未実装だが、一般的に必要）
                profile_data["icon"] = None

            # 3. UserProfileの全更新
            self.profile_repo.update(
                profile,
                # 辞書の要素を展開して更新メソッドに渡す
                **profile_data,
            )

            # 4. is_first_loginフラグの更新
            if user.is_first_login:
                updated_user = self.user_repo.update(
                    user,
                    is_first_login=False,
                    # 初回設定時の更新日時も記録する
                    updated_method=LOG_METHOD.INITIAL_SETUP.value,
                )
            else:
                updated_user = user

            return updated_user

        except IntegrityError:
            # Repositoryから伝播したIntegrityErrorを再送
            raise
        except ExternalServiceError:
            # _handle_icon_uploadから伝播したExternalServiceErrorを再送
            raise
        except Exception as e:
            # その他予期せぬエラー
            log_output_by_msg_id(
                log_id="MSGE002",
                params=[f"Error updating initial setup for user {user.pk}: {e}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            # 外部に公開するエラーとして変換して送出
            raise IntegrityError(
                message="初回設定の更新中に予期せぬエラーが発生しました。",
                details={"internal_message": str(e)},
            )

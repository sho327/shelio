import hashlib
import os

from django.conf import settings
from django.contrib.auth import get_user_model

# 必要なDjango標準認証関数をインポート
# セッション管理のためにSessionモデルをインポート（強制ログアウト用）
from django.contrib.sessions.models import Session
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import IntegrityError as DjangoIntegrityError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from account.exceptions import (
    AccountLockedException,
    AuthenticationFailedException,
    PasswordResetTokenInvalidException,
    TokenExpiredOrNotFoundException,
    UserAlreadyActiveException,
)
from account.models.t_user_token import TokenTypes
from account.repositories.m_user_profile_repository import M_UserProfileRepository
from account.repositories.m_user_repository import M_UserRepository
from account.repositories.t_user_token_repository import T_UserTokenRepository
from core.auth_scheme.user_auth_backend import UserAuthBackend
from core.consts import LOG_METHOD
from core.exceptions import DuplicationError, ExternalServiceError, IntegrityError
from core.utils.log_helpers import log_output_by_msg_id

User = get_user_model()


class AuthService:
    """
    認証（ログイン、ログアウト）、認可、
    およびクレデンシャル管理（パスワードリセット等）を担うサービスクラス
    """

    def __init__(self):
        self.user_auth_backend = UserAuthBackend()
        self.user_repo = M_UserRepository()
        self.profile_repo = M_UserProfileRepository()
        self.token_repo = T_UserTokenRepository()

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------
    def send_activation_email(self, m_user_instance: User, token_value: str):
        """
        アクティベーションメールの送信処理 (Siteフレームワーク使用例)
        """

        # 1. Siteフレームワークからドメインを取得
        current_site = Site.objects.get_current()
        domain = current_site.domain

        # 2. Viewからスキーム（http/https）を取得し View から渡すのがベストですが、
        #    Siteフレームワーク内で完結させるため、ここでは強制的に https とする
        scheme = "https" if not settings.DEBUG else "http"

        # 3. URLパターン名からパスを逆引き (例: /account/user/token/activation/)
        path = reverse("account:activate_user", kwargs={"token_value": token_value})

        # 4. 絶対URLを構築
        activation_url = f"{scheme}://{domain}{path}"

        # 有効期限の表示（secondsをhoursに変換）
        expiry_seconds = settings.TOKEN_EXPIRY_SECONDS.get("activation", 3600)
        expiry_hours = expiry_seconds / 3600

        # メール本文に利用
        subject = f"【{settings.APP_NAME}】仮登録完了のお知らせ"
        message = (
            f"{settings.APP_NAME}にご登録いただきありがとうございます。\n"
            f"次のリンクをクリックしてアカウントを有効化してください（有効期限：{expiry_hours}時間）。\n"
            f"{activation_url}"
        )
        from_email = settings.EMAIL_FROM
        recipient_list = [
            m_user_instance.email,
        ]
        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            # send_mailはSMTP接続失敗など、様々なエラーを投げる可能性がある
            raise ExternalServiceError(
                message="アクティベーションメールの送信に失敗しました。",
                details={"recipient": m_user_instance.email, "internal_error": str(e)},
            )
        return True

    def _send_password_reset_email(self, user: User, token: str):
        """パスワードリセットメール送信の実装"""
        m_user_profile_instance = self.profile_repo.get_alive_one_or_none(
            m_user=user.pk
        )
        reset_url = f"http://localhost:8000/account/password_reset_confirm/{token}/"
        subject = f"【{settings.APP_NAME}】パスワード再設定のご案内"
        message = (
            f"{m_user_profile_instance.display_name} 様\n\n"
            f"パスワード再設定のリクエストを受け付けました。\n"
            f"以下のリンクから新しいパスワードを設定してください（有効期限：1時間）。\n\n"
            f"{reset_url}\n\n"
            f"お心当たりがない場合は、このメールを破棄してください。"
        )
        try:
            send_mail(subject, message, settings.EMAIL_FROM, [user.email])
        except Exception as e:
            # send_mailはSMTP接続失敗など、様々なエラーを投げる可能性がある
            raise ExternalServiceError(
                message="パスワードリセットメールの送信に失敗しました。",
                details={"recipient": user.email, "internal_error": str(e)},
            )

    def _force_logout_all_sessions(self, user: User):
        """
        指定されたユーザーに関連付けられている全ての既存のセッションを強制的に無効化する。
        """
        # Djangoのセッションストアから、現在アクティブなセッションを全て取得
        sessions = Session.objects.filter(expire_date__gte=timezone.now())

        # ユーザーIDに紐づくセッションキーを特定し、削除
        for session in sessions:
            session_data = session.get_decoded()
            # セッションデータ内の認証ユーザーIDが一致するかチェック
            if str(session_data.get("_auth_user_id")) == str(user.pk):
                session.delete()

    # ------------------------------------------------------------------
    # ログイン処理
    # ------------------------------------------------------------------
    def login(self, email: str, password: str) -> User:
        """
        メールアドレスとパスワードで認証済みユーザーインスタンスを返す。
        ビュー層でこのユーザーを使い、セッションを確立する必要がある。
        Args:
            email (str): メールアドレス
            password (str): パスワード
        Returns:
            Dict[str, str]: {"access": "...", "refresh": "..."}
        Raises:
            AuthenticationFailedException: 認証失敗
            AccountLockedException: アカウントが無効（is_active=False）
        """
        # 1. Django標準のauthenticateを使って認証
        # (内部でcheck_passwordが行われる)
        user = self.user_auth_backend.authenticate(
            None, username=email, password=password
        )

        if user is None:
            # ユーザーが存在しないか、パスワードが不一致
            # セキュリティのため、どちらが間違っているかは教えない
            raise AuthenticationFailedException()

        # 2. アカウント状態のチェック (is_active)
        if not user.is_active:
            # 凍結、ロック、または退会済み
            raise AccountLockedException()

        # 3. 最終ログイン日時の更新
        # update_last_login(None, user) # Django標準関数を使う場合
        # またはリポジトリ経由で更新
        self.user_repo.update(user, last_login=timezone.now())

        return user  # 認証済みユーザーを返却

    # ------------------------------------------------------------------
    # ユーザ新規登録処理
    # ------------------------------------------------------------------
    @transaction.atomic
    def register_new_user(self, email: str, password: str, display_name: str) -> User:
        """
        ユーザー新規作成時に必要な一連の処理を実行
        Args:
            email (str): ユーザーのメールアドレス
            password (str): パスワード（ハッシュ化される）
            display_name (str, optional): プロフィール表示名
        Returns:
            User: 作成されたユーザーインスタンス
        """
        try:
            # 1. M_Userの作成 (User.objects.create_userはリポジトリのメソッド経由で呼ぶ)
            m_user_instance = self.user_repo.create_user_with_password(
                email=email, password=password
            )

            # M_UserProfileがシグナルで作成された後、display_nameを更新
            # (シグナルが動かないことは起こり得ないので冗長となる存在しないかのチェックは行わない)
            if display_name:
                # M_UserProfileのリポジトリを使用して更新
                # M_UserとM_UserProfileは1:1のため、M_UserインスタンスからM_UserProfileを取得し更新
                m_user_profile_instance = self.profile_repo.get_alive_one_or_none(
                    m_user=m_user_instance.pk
                )
                if m_user_profile_instance:
                    # profile_repoのupdateメソッドを使用
                    self.profile_repo.update(
                        m_user_profile_instance, display_name=display_name
                    )

            # 2. T_UserToken(アクティベーション)レコードの作成
            raw_token_value = os.urandom(32).hex()
            token_hash = hashlib.sha256(raw_token_value.encode()).hexdigest()
            expiry_seconds = settings.TOKEN_EXPIRY_SECONDS.get("activation")
            expired_at = timezone.now() + timezone.timedelta(hours=expiry_seconds)
            # T_UserTokenRepositoryのcreateメソッドを使用
            self.token_repo.create(
                m_user=m_user_instance,
                token_hash=token_hash,
                token_type=TokenTypes.ACTIVATION,
                expired_at=expired_at,
            )

            # 3. アクティベーションメールの送信
            self.send_activation_email(m_user_instance, raw_token_value)
            return m_user_instance

        except DjangoIntegrityError as e:
            # 既にフォームバリデーションでメール重複をチェックしているはずだが、
            # レースコンディションや他のUNIQUE制約違反が発生した場合の最終防衛線。
            # エラーメッセージやコードに基づき、DuplicationErrorかIntegrityErrorに変換
            if "UNIQUE constraint" in str(e) or "duplicate key" in str(e):
                # ユーザーに見せるエラーメッセージを DuplicationError のデフォルトに任せる
                raise DuplicationError(details={"field": "email"})

            # その他のDB整合性エラー
            raise IntegrityError(details={"db_error": str(e)})

        except ExternalServiceError:
            # send_activation_email内部でExternalServiceErrorが投げられた場合
            raise  # そのまま再送出

        except Exception as e:
            # 予期せぬエラーは、コアのApplicationErrorを投げるか、ログに残してServiceInternalErrorを定義して投げる
            # 今回は、定義済みの IntegrityError を使用しつつログを取るのが安全
            log_output_by_msg_id(
                log_id="MSGE001",
                params=[f"Unexpected error during registration for {email}: {e}"],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            raise IntegrityError(
                message="登録処理中に予期せぬエラーが発生しました。",
                details={"internal_message": str(e)},
            )

    # ------------------------------------------------------------------
    # ユーザアクティベーション処理
    # ------------------------------------------------------------------
    @transaction.atomic
    def activate_user(self, raw_token_value: str) -> User:
        """
        アクティベーションリンクに含まれる生トークンを使用してユーザーを有効化する。
        Args:
            raw_token_value (str): URLから取得した生トークン値
        Returns:
            User: 有効化されたユーザーインスタンス
        Raises:
            TokenExpiredOrNotFoundException: トークンが見つからないか、期限切れの場合
            UserAlreadyActiveException: ユーザーが既に有効な場合
        """
        # 1. 生トークンをDBに保存されている形式（ハッシュ値）に変換
        token_hash = hashlib.sha256(raw_token_value.encode()).hexdigest()
        now = timezone.now()

        # 2. トークンを検索（ハッシュ値、種別、未期限切れ、未削除を条件とする）
        token_instance = self.token_repo.get_alive_one_or_none(
            token_hash=token_hash,
            token_type=TokenTypes.ACTIVATION,
            expired_at__gt=now,  # 現在時刻より期限が未来であること
        )

        if not token_instance:
            # トークンが存在しない、または期限切れ
            raise TokenExpiredOrNotFoundException(
                "有効なアクティベーション・トークンが見つかりません。"
            )

        m_user_instance = token_instance.m_user

        # 3. ユーザーの状態チェック
        if m_user_instance.is_active:
            # トークンが見つかったがユーザーは既にアクティブ
            # この場合も、セキュリティのため使用済みトークンとして無効化する
            self.token_repo.soft_delete(token_instance)
            raise UserAlreadyActiveException("アカウントは既に有効化されています。")

        # 4. ユーザーをシステム的にログイン可能(アクティブ)にする
        # user_repoのupdateメソッドを使用し、is_activeを更新
        updated_user = self.user_repo.update(
            m_user_instance,
            is_active=True,
        )

        # 5. 使用済みのトークンを無効化（論理削除）
        self.token_repo.soft_delete(token_instance)

        return updated_user

    # ------------------------------------------------------------------
    # パスワードリセット要求 (メール送信)
    # ------------------------------------------------------------------
    @transaction.atomic
    def request_password_reset(self, email: str) -> bool:
        """
        パスワードリセットメールを送信する。
        セキュリティ上の理由から、ユーザーが存在しなくてもエラーにはせずTrueを返す（列挙攻撃対策）。
        """
        # 1. ユーザー検索
        user = self.user_repo.get_alive_one_or_none(email=email)

        # ユーザーが存在しない、またはアクティブでない場合は何もしないが、
        # 攻撃者に悟られないよう正常終了を装う
        if not user or not user.is_active:
            return True

        try:
            # 2. リセットトークンの生成 (アクティベーションと同様のロジック)
            raw_token = os.urandom(32).hex()
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            expiry_seconds = settings.TOKEN_EXPIRY_SECONDS.get("password_reset")
            expired_at = timezone.now() + timezone.timedelta(hours=expiry_seconds)

            # 3. 既存のリセットトークンがあれば無効化する（オプション）
            # 【セキュリティ/利便性のトレードオフ】
            # 既存のトークンを無効化することで、ユーザーが誤って何度もリクエストした際に
            # どのメール（どのトークン）が有効か迷うのを防げる。
            # ただし、悪意のあるユーザーが連続リクエストで正規ユーザーの有効トークンを無効化する
            # Denial of Service (DoS) 攻撃の可能性もある。今回はコメントアウト。
            # # self.token_repo.invalidate_tokens_by_user(user, TokenTypes.PASSWORD_RESET)

            # 4. トークン保存
            self.token_repo.create(
                m_user=user,
                token_hash=token_hash,
                token_type=TokenTypes.PASSWORD_RESET,
                expired_at=expired_at,
            )

            # 5. メール送信
            self._send_password_reset_email(user, raw_token)

            return True

        except DjangoIntegrityError as e:
            # トークン保存時に発生しうるDBレベルのエラー（例: 外部キー制約）
            # DuplicationErrorはトークンでは考えにくいが、IntegrityErrorとして捕捉
            # ログ記録推奨
            raise IntegrityError(
                message="リセットトークン生成中にデータベース整合性エラーが発生しました。",
                details={"internal_message": str(e)},
            )
        except ExternalServiceError:
            # メール送信失敗の例外をそのまま View へ再送出
            raise
        except Exception as e:
            # その他の予期せぬエラー（DB接続エラーなど）
            # ログ記録推奨
            raise IntegrityError(
                message="リセット要求処理中に予期せぬエラーが発生しました。",
                details={"internal_message": str(e)},
            )

    # ------------------------------------------------------------------
    # パスワードリセット実行
    # ------------------------------------------------------------------
    @transaction.atomic
    def reset_password(self, raw_token: str, new_password: str) -> User:
        """
        トークンを検証し、パスワードを更新する。
        """
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        now = timezone.now()

        # 1. トークン検証
        token_instance = self.token_repo.get_alive_one_or_none(
            token_hash=token_hash,
            token_type=TokenTypes.PASSWORD_RESET,
            expired_at__gt=now,
        )

        if not token_instance:
            raise PasswordResetTokenInvalidException()

        user = token_instance.m_user

        try:
            # 2. パスワード更新 (ハッシュ化はset_passwordが担う)
            user.set_password(new_password)

            # 3. 情報更新 (パスワード更新日時など)
            self.user_repo.update(
                user,
                password=user.password,  # set_passwordでハッシュ化された値が入っている
                password_updated_at=now,
            )

            # 4. 使用済みトークンを無効化
            self.token_repo.soft_delete(token_instance)

            # 5. 【セキュリティ強化：全デバイスからの強制ログアウト（セッション切断）】
            # セッション認証に基づき、全セッションを削除する
            # SessionモデルにはUserへの直接的なリレーションがないため、セッションデータを解析して削除
            self._force_logout_all_sessions(user)

            return user

        except DjangoIntegrityError as e:
            # パスワード更新時のDBレベルのエラー（外部キーなど）
            # ログ記録推奨
            raise IntegrityError(
                message="パスワード更新中にデータベース整合性エラーが発生しました。",
                details={"internal_message": str(e)},
            )
        except Exception as e:
            # その他の予期せぬエラー（DB接続エラーなど）
            # ログ記録推奨
            raise IntegrityError(
                message="パスワードリセット処理中に予期せぬエラーが発生しました。",
                details={"internal_message": str(e)},
            )

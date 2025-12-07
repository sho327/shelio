from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel


# ユーザプロフィールマスタ
class M_UserProfile(BaseModel):
    # Consts
    # Fields
    # ID (BIGINT PRIMARY KEY) はDjangoが自動で付与

    # ユーザマスタ
    m_user = models.OneToOneField(
        "account.M_User",
        db_column="m_user_id",
        verbose_name="ユーザマスタ",
        db_comment="ユーザマスタ",
        on_delete=models.CASCADE,
        primary_key=True,
        # 逆参照名を定義(例: m_user_instance.user_profile/通常参照はm_user_profile_instance.m_user(_id)で取得可能)
        related_name="user_profile",
    )
    # --- 1. 基本情報 ---
    display_name = models.CharField(
        db_column="display_name",
        verbose_name="表示名",
        db_comment="表示名",
        max_length=64,
        null=True,
        blank=True,
    )
    theme = models.CharField(
        db_column="theme",
        verbose_name="テーマ",
        db_comment="UIテーマ",
        max_length=32,
        default="light",
        blank=True,
    )
    icon = models.ImageField(
        db_column="icon",
        verbose_name="ユーザーアイコン",
        db_comment="ユーザーアイコン",
        upload_to="user_icons/",  # 開発時は MEDIA_ROOT/user_icons に保存される
        max_length=512,  # ImageFieldはパスを格納するため長めに
        null=True,
        blank=True,
    )

    # --- 2. 詳細情報 ---
    bio = models.TextField(
        db_column="bio",
        verbose_name="自己紹介文",
        db_comment="自己紹介文",
        max_length=500,
        null=True,
        blank=True,
    )
    career_history = models.TextField(
        db_column="career_history",
        verbose_name="経歴",
        db_comment="経歴（職務経歴や学歴など）",
        null=True,
        blank=True,
    )
    location = models.CharField(
        db_column="location",
        verbose_name="所在地",
        db_comment="所在地（例：東京都、日本）",
        max_length=100,
        null=True,
        blank=True,
    )
    skill_tags_raw = models.CharField(
        db_column="skill_tags_raw",
        verbose_name="技術タグ（RAW）",
        db_comment="技術タグ（カンマ区切りなどの生データ）",
        max_length=500,
        null=True,
        blank=True,
    )

    # --- 3. リンク情報 ---
    github_link = models.URLField(
        db_column="github_link",
        verbose_name="GitHubリンク",
        db_comment="GitHubプロフィールリンク",
        max_length=255,
        null=True,
        blank=True,
    )
    x_link = models.URLField(
        db_column="x_link",
        verbose_name="X (旧Twitter) リンク",
        db_comment="X (旧Twitter) プロフィールリンク",
        max_length=255,
        null=True,
        blank=True,
    )
    portfolio_blog_link = models.URLField(
        db_column="portfolio_blog_link",
        verbose_name="ポートフォリオ/ブログリンク",
        db_comment="ポートフォリオまたはブログのリンク",
        max_length=255,
        null=True,
        blank=True,
    )

    # --- 4. フラグと設定 ---
    is_public = models.BooleanField(
        db_column="is_public",
        verbose_name="プロフィール公開フラグ",
        db_comment="プロフィール公開フラグ",
        db_default=True,
        default=True,
    )

    # メール通知設定 (notifyで統一)
    is_email_notify_enabled = models.BooleanField(
        db_column="is_email_notify_enabled",
        verbose_name="メール通知一括設定フラグ",
        db_comment="メール通知一括設定フラグ",
        db_default=True,
        default=True,
    )
    # 個別の通知設定
    is_notify_like = models.BooleanField(
        db_column="is_notify_like",
        verbose_name="通知:いいね設定フラグ",
        db_comment="通知:作品に「いいね」がついた時のメール設定フラグ",
        db_default=True,
        default=True,
    )
    is_notify_comment = models.BooleanField(
        db_column="is_notify_comment",
        verbose_name="通知:コメント設定フラグ",
        db_comment="通知:コメントや返信が来た時のメール設定フラグ",
        db_default=True,
        default=True,
    )
    is_notify_follow = models.BooleanField(
        db_column="is_notify_follow",
        verbose_name="通知:フォロー設定フラグ",
        db_comment="通知:誰かにフォローされた時のメール設定フラグ",
        db_default=True,
        default=True,
    )
    # --- 各テーブル共通(AbstractBaseModelは列順が変わってしまうので使用しない) ---
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # M_Userモデルを参照
        db_column="created_by",
        verbose_name="作成者",
        db_comment="作成を行ったユーザー",
        related_name="%(app_label)s_%(class)s_created",  # 関連名の一意性を確保
        on_delete=models.SET_NULL,  # ユーザーが消えてもデータは残す
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        db_column="created_at",
        verbose_name="作成日時",
        db_comment="作成日時",
        null=True,
        blank=True,
        auto_now_add=True,
    )
    created_method = models.CharField(
        db_column="created_method",
        verbose_name="作成処理",
        db_comment="作成処理",
        max_length=128,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="updated_by",
        verbose_name="更新者",
        db_comment="更新を行ったユーザー",
        related_name="%(app_label)s_%(class)s_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(
        db_column="updated_at",
        verbose_name="更新日時",
        db_comment="更新日時",
        null=True,
        blank=True,
        auto_now=True,
    )
    updated_method = models.CharField(
        db_column="updated_method",
        verbose_name="更新処理",
        db_comment="更新処理",
        max_length=128,
        null=True,
        blank=True,
    )
    deleted_at = models.DateTimeField(
        db_column="deleted_at",
        verbose_name="削除日時",
        db_comment="削除日時",
        null=True,
        blank=True,
        db_default=None,
        default=None,
    )
    # --- 各テーブル共通 ---

    # django-simple-historyを使用
    history = HistoricalRecords()

    # テーブル名
    class Meta:
        db_table = "m_user_profile"
        db_table_comment = "ユーザプロフィールマスタ"
        verbose_name = "ユーザプロフィールマスタ"
        verbose_name_plural = "ユーザプロフィールマスタ"

    def __str__(self):
        return f"{self.m_user}"

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
    # 表示名
    display_name = models.CharField(
        db_column="display_name",
        verbose_name="表示名",
        db_comment="表示名",
        max_length=64,
        null=True,
        blank=True,
    )
    # ユーザーアイコン
    # ファイルパスを保存し、ストレージにファイルを配置
    icon = models.ImageField(
        db_column="icon",
        verbose_name="ユーザーアイコン",
        upload_to="user_icons/",  # 開発時は MEDIA_ROOT/user_icons に保存される
        null=True,
        blank=True,
    )

    # 自己紹介
    bio = models.TextField(
        db_column="bio",
        verbose_name="自己紹介",
        db_comment="自己紹介文",
        max_length=500,  # 例: 500文字制限
        null=True,
        blank=True,
    )

    # 経歴 (シンプルな文字列として保持。より複雑な場合は別テーブル化推奨)
    career_history = models.TextField(
        db_column="career_history",
        verbose_name="経歴",
        db_comment="職務経歴や学歴など",
        null=True,
        blank=True,
    )

    # 所在地
    location = models.CharField(
        db_column="location",
        verbose_name="所在地",
        db_comment="所在地（例：東京都、日本）",
        max_length=100,
        null=True,
        blank=True,
    )

    # SNS/ポートフォリオURL
    github_url = models.URLField(
        db_column="github_url",
        verbose_name="GitHub URL",
        db_comment="GitHubプロフィールリンク",
        max_length=255,
        null=True,
        blank=True,
    )
    x_url = models.URLField(
        db_column="x_url",
        verbose_name="X (旧Twitter) URL",
        db_comment="X (旧Twitter) プロフィールリンク",
        max_length=255,
        null=True,
        blank=True,
    )
    portfolio_blog_url = models.URLField(
        db_column="portfolio_blog_url",
        verbose_name="ポートフォリオ/ブログ URL",
        db_comment="個人ポートフォリオまたはブログのリンク",
        max_length=255,
        null=True,
        blank=True,
    )

    # 得意な技術タグ
    skill_tags_raw = models.CharField(
        db_column="skill_tags_raw",
        verbose_name="得意な技術タグ（RAW）",
        db_comment="得意な技術タグ（カンマ区切りなどの生データ）",
        max_length=500,
        null=True,
        blank=True,
    )

    # プロフィール公開設定
    is_public = models.BooleanField(
        db_column="is_public",
        verbose_name="プロフィール公開フラグ",
        db_comment="プロフィールを一般公開するかどうか",
        db_default=True,
        default=True,
    )

    # メール通知設定
    # すべての通知を一括で受け取るかどうかのフラグ
    is_email_notification_enabled = models.BooleanField(
        db_column="is_email_notification_enabled",
        verbose_name="メール通知一括ON/OFF",
        db_comment="すべてのメール通知をONにするか",
        db_default=True,
        default=True,
    )
    # 個別の通知設定
    notify_like = models.BooleanField(
        db_column="notify_like",
        verbose_name="通知:作品いいね",
        db_comment="作品に「いいね」がついた時のメール通知",
        db_default=True,
        default=True,
    )
    notify_comment = models.BooleanField(
        db_column="notify_comment",
        verbose_name="通知:コメント/返信",
        db_comment="コメントや返信が来た時のメール通知",
        db_default=True,
        default=True,
    )
    notify_follow = models.BooleanField(
        db_column="notify_follow",
        verbose_name="通知:フォロー",
        db_comment="誰かにフォローされた時のメール通知",
        db_default=True,
        default=True,
    )
    # --- 各テーブル共通(AbstractBaseModelは列順が変わってしまうので使用しない) ---
    created_by = models.DecimalField(
        db_column="created_by",
        verbose_name="作成者/id",
        db_comment="作成者/id",
        decimal_places=0,
        max_digits=20,
        null=True,
    )
    created_at = models.DateTimeField(
        db_column="created_at",
        verbose_name="作成日時",
        db_comment="作成日時",
        null=True,
        blank=True,
    )
    created_method = models.CharField(
        db_column="created_method",
        verbose_name="作成処理",
        db_comment="作成処理",
        max_length=128,
        null=True,
        blank=True,
    )
    updated_by = models.DecimalField(
        db_column="updated_by",
        verbose_name="更新者/id",
        db_comment="更新者/id",
        decimal_places=0,
        max_digits=20,
        null=True,
    )
    updated_at = models.DateTimeField(
        db_column="updated_at",
        verbose_name="更新日時",
        db_comment="更新日時",
        null=True,
        blank=True,
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

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileEditForm(forms.Form):
    """
    プロフィール編集フォーム。
    """

    # 基本情報
    display_name = forms.CharField(
        label="表示名",
        max_length=64,
        required=True,
        help_text="コミュニティ内であなたを識別するために使用されます。",
    )

    icon = forms.ImageField(
        label="ユーザーアイコン",
        required=False,
        help_text="プロフィールアイコン画像をアップロードしてください。",
    )

    # 詳細情報
    bio = forms.CharField(
        label="自己紹介文",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="自己紹介文を入力してください（最大500文字）。",
    )

    career_history = forms.CharField(
        label="経歴",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="職務経歴や学歴などを入力してください。",
    )

    location = forms.CharField(
        label="所在地",
        max_length=100,
        required=False,
        help_text="例：東京都、日本",
    )

    skill_tags_raw = forms.CharField(
        label="技術タグ",
        max_length=500,
        required=False,
        help_text="カンマ区切りで技術タグを入力してください。例：Python, Django, React",
    )

    # リンク情報
    github_link = forms.URLField(
        label="GitHubリンク",
        max_length=255,
        required=False,
        help_text="GitHubプロフィールのURLを入力してください。",
    )

    x_link = forms.URLField(
        label="X (旧Twitter) リンク",
        max_length=255,
        required=False,
        help_text="X (旧Twitter) プロフィールのURLを入力してください。",
    )

    portfolio_blog_link = forms.URLField(
        label="ポートフォリオ/ブログリンク",
        max_length=255,
        required=False,
        help_text="ポートフォリオまたはブログのURLを入力してください。",
    )

    # フラグと設定
    is_public = forms.BooleanField(
        label="プロフィールを一般公開する",
        required=False,
        help_text="チェックを外すと、プロフィールはログインユーザーにのみ表示されます。",
    )

    is_email_notify_enabled = forms.BooleanField(
        label="メール通知を一括で受け取る",
        required=False,
        help_text="すべてのメール通知の有効/無効を一括で設定します。",
    )

    is_notify_like = forms.BooleanField(
        label="いいね通知を受け取る",
        required=False,
        help_text="作品に「いいね」がついた時のメール通知を受け取ります。",
    )

    is_notify_comment = forms.BooleanField(
        label="コメント通知を受け取る",
        required=False,
        help_text="コメントや返信が来た時のメール通知を受け取ります。",
    )

    is_notify_follow = forms.BooleanField(
        label="フォロー通知を受け取る",
        required=False,
        help_text="誰かにフォローされた時のメール通知を受け取ります。",
    )

    # -------------------------------------------------------------
    # 初期値設定用のフック (ビューで利用)
    # -------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    # -------------------------------------------------------------
    # クリーンメソッド
    # -------------------------------------------------------------
    def clean_display_name(self):
        display_name = self.cleaned_data.get("display_name")

        if not display_name:
            raise forms.ValidationError("表示名は必須です。", code="required")

        return display_name

    def clean_bio(self):
        bio = self.cleaned_data.get("bio")
        if bio and len(bio) > 500:
            raise forms.ValidationError(
                "自己紹介文は500文字以内で入力してください。", code="max_length"
            )
        return bio

    def clean_skill_tags_raw(self):
        skill_tags_raw = self.cleaned_data.get("skill_tags_raw")
        if skill_tags_raw and len(skill_tags_raw) > 500:
            raise forms.ValidationError(
                "技術タグは500文字以内で入力してください。", code="max_length"
            )
        return skill_tags_raw

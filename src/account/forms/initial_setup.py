from django import forms
from django.contrib.auth import get_user_model

from account.models import M_UserProfile

User = get_user_model()


class InitialSetupForm(forms.ModelForm):
    # Userモデルのフィールド
    # username（Userモデルに存在する場合）やemailなどを追加
    # 例: username = forms.CharField(max_length=150, required=True, label="ユーザー名")
    # ここでは例として display_name をM_UserProfileから取得し、Userフォームで表示

    # M_UserProfileのフィールド
    display_name = forms.CharField(
        max_length=100,
        required=False,  # 初期設定で必須にしない場合はFalse
        label="表示名",
        help_text="他のユーザーに表示される名前です。",
    )

    # 必要に応じて、Userモデルの他のフィールドをここに追加
    # 例: first_name = forms.CharField(max_length=30, required=False, label="名")
    # 例: last_name = forms.CharField(max_length=30, required=False, label="姓")

    class Meta:
        model = User
        # Userモデルのどのフィールドをフォームで扱うか指定
        # 今回は is_first_login フラグをUserモデルに持たせているため、
        # Userモデル自体からは更新不要なフィールドのみを指定（例：password以外の共通フィールド）
        # ここではUserモデルからの直接更新は行わない想定でfieldsを空にするか、必要なものだけ
        fields = (
            []
        )  # Userモデルのフィールドはビューで直接更新するか、別のフォームで扱う

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)  # ビューからuserオブジェクトを受け取る
        super().__init__(*args, **kwargs)

        if self.user:
            # 既存のプロフィールデータをフォームに初期値として設定
            try:
                # user.user_profile は OneToOneField の逆参照
                profile = self.user.user_profile
                self.fields["display_name"].initial = profile.display_name
            except M_UserProfile.DoesNotExist:
                # プロフィールが存在しない場合（極めて稀だが念のため）
                pass

    def clean_display_name(self):
        display_name = self.cleaned_data.get("display_name")
        if not display_name:
            # display_name が空の場合でも許容する
            # あるいは、ここで自動生成ロジックを実装することも可能
            # 例: return self.user.email.split('@')[0]
            pass
        return display_name

    def save(self, commit=True):
        # Userモデルのフィールドを保存する場合はここに追加
        # user = super().save(commit=False) # Userモデルの保存はここでは行わない

        # M_UserProfileの更新
        try:
            profile = self.user.user_profile
        except M_UserProfile.DoesNotExist:
            # プロフィールが存在しない場合は新規作成（通常はシグナルで作成済み）
            profile = M_UserProfile(m_user=self.user)

        profile.display_name = self.cleaned_data["display_name"]
        if commit:
            profile.save()

        # Userモデルの is_first_login フラグはビューで更新するため、ここでは扱わない
        return self.user  # userオブジェクトを返す

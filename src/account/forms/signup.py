from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSignupForm(forms.Form):
    # Djangoの標準Userモデルのフィールドを使用
    email = forms.EmailField(
        label="メールアドレス",
        max_length=255,
        widget=forms.EmailInput(attrs={"placeholder": "メールアドレス"}),
    )
    # 必要に応じて表示名などのフィールドを追加
    display_name = forms.CharField(
        label="表示名",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "任意"}),
    )
    password = forms.CharField(
        label="パスワード",
        widget=forms.PasswordInput(attrs={"placeholder": "パスワード"}),
    )
    password_confirm = forms.CharField(
        label="パスワード（確認用）",
        widget=forms.PasswordInput(attrs={"placeholder": "確認のため再入力"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # データベースに同じメールアドレスが存在しないかチェック
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
        return email

    def clean(self):
        """パスワードとパスワード確認の一致をチェック"""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            # フィールド全体のエラーとして追加 (Noneをキーに設定)
            self.add_error("password_confirm", "パスワードが一致しません。")

        return cleaned_data

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView

from account.forms.initial_setup import InitialSetupForm
from account.services.user_service import UserService

User = get_user_model()


class InitialSetupView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = InitialSetupForm
    template_name = "account/initial_setup.html"
    success_url = reverse_lazy("dashboard")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    def get_object(self, queryset=None):
        """現在の認証済みユーザーインスタンスを取得"""
        # LoginRequiredMixinがあるため、request.userは認証済みであることが保証される
        return self.request.user

    def dispatch(self, request, *args, **kwargs):
        # 認証済みで、かつ設定が完了している（is_first_loginがFalse）場合、
        # この画面には用がないため、ダッシュボードへリダイレクトさせる。
        if request.user.is_authenticated and not request.user.is_first_login:
            return redirect(self.get_success_url())

        # それ以外（未認証、または未完了）の場合は処理を続行
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """フォームにuserオブジェクトを渡す"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user  # 現在のユーザーを取得
        # フォームデータを抽出し、ファイルと分けてサービスに渡す
        profile_data = form.cleaned_data.copy()
        icon_file = profile_data.pop("icon", None)  # icon_fileを分離

        try:
            # サービス層を呼び出し、初回設定情報を更新
            self.user_service.initial_setup(
                user=self.request.user, profile_data=profile_data, icon_file=icon_file
            )
            # フォームはUserProfileを更新するだけなので、super().form_validは呼ばない
            # もしUserモデルのフィールドもフォームで更新する場合は super().form_valid(form)を呼ぶ
            # return super().form_valid(form)

            # 更新後のユーザーをセッションに再ロードする必要がある場合 (オプション)
            # from django.contrib.auth import login
            # login(self.request, updated_user)

            return redirect(self.get_success_url())

        except Exception as e:
            # サービス層からの例外を捕捉し、フォームエラーとして表示またはログ出力
            form.add_error(None, f"設定の保存中にエラーが発生しました: {e}")
            return self.form_invalid(form)
            return self.form_invalid(form)

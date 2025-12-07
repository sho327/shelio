from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

process_name = "ProfileView"


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    プロフィール表示画面
    """

    template_name = "account/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # プロフィール情報を取得
        try:
            profile = user.user_profile
            context["profile"] = profile

            # 技術タグをリストに変換（テンプレートで使いやすくするため）
            if profile.skill_tags_raw:
                skill_tags = [
                    tag.strip()
                    for tag in profile.skill_tags_raw.split(",")
                    if tag.strip()
                ]
                context["skill_tags"] = skill_tags
            else:
                context["skill_tags"] = []
        except Exception:
            # プロフィールが存在しない場合はNone
            context["profile"] = None
            context["skill_tags"] = []

        context["user"] = user
        return context

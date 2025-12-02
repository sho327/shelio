from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    ログイン後のダッシュボード（ホーム）画面を表示するビュー。
    LoginRequiredMixinにより、未ログインユーザーはアクセスできません。
    """

    template_name = "dashboard/dashboard.html"

    # 必要に応じて、ここで get_context_data を実装してDBからデータを取得します。
    # 現在は一旦空でOKです。

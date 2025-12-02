from django.views.generic import TemplateView


class ActivatePendingView(TemplateView):
    """
    サインアップ後、ユーザーにメールを確認するように促す画面
    """

    template_name = "account/activate_pending.html"
    # テンプレート内で、登録完了メッセージや再送リンクなどを表示します。

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from account.forms.signup import SignupForm
from account.services.auth_service import AuthService
from core.decorators.logging_sql_queries import logging_sql_queries

process_name = "RegisterView"


class RegisterView(FormView):
    form_class = SignupForm
    template_name = "account/register.html"
    success_url = reverse_lazy("account:register_pending")

    # SQLログデコレータを適用
    @logging_sql_queries(process_name=process_name)
    def form_valid(self, form: SignupForm) -> HttpResponseRedirect:

        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        display_name = form.cleaned_data.get("display_name")

        auth_service = AuthService()

        try:
            # 1. サービスを介してユーザーを作成・保存
            auth_service.register_new_user(
                email=email, password=password, display_name=display_name
            )

            # 2. 成功後のリダイレクト
            return redirect(self.get_success_url())

        except Exception as e:
            # サービス層で発生したエラーを予期せぬエラーとして返す
            form.add_error(
                None,
                "予期せぬエラーが発生しました。",
            )
            return self.form_invalid(form)

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from account.forms.profile import ProfileEditForm
from account.services.user_service import UserService
from core.consts import LOG_METHOD
from core.decorators.logging_sql_queries import logging_sql_queries
from core.exceptions import ExternalServiceError, IntegrityError
from core.utils.log_helpers import log_output_by_msg_id

process_name = "ProfileEditView"


class ProfileEditView(LoginRequiredMixin, FormView):
    """
    プロフィール編集画面
    """

    template_name = "account/profile_edit.html"
    form_class = ProfileEditForm
    success_url = reverse_lazy("account:profile")
    user_service = UserService()

    # SQLログデコレータを適用
    @logging_sql_queries(process_name=process_name)
    def get_initial(self):
        """
        ユーザープロフィールの現在の値を取得してフォームに渡す。
        """
        initial = super().get_initial()
        user = self.request.user

        if user.is_authenticated:
            try:
                profile = user.user_profile
                initial["display_name"] = profile.display_name
                initial["bio"] = profile.bio
                initial["career_history"] = profile.career_history
                initial["location"] = profile.location
                initial["skill_tags_raw"] = profile.skill_tags_raw
                initial["github_link"] = profile.github_link
                initial["x_link"] = profile.x_link
                initial["portfolio_blog_link"] = profile.portfolio_blog_link
                initial["is_public"] = profile.is_public
                initial["is_email_notify_enabled"] = profile.is_email_notify_enabled
                initial["is_notify_like"] = profile.is_notify_like
                initial["is_notify_comment"] = profile.is_notify_comment
                initial["is_notify_follow"] = profile.is_notify_follow
            except Exception:
                pass

        return initial

    # フォームのインスタンス化をオーバーライド (userインスタンスを渡すため)
    def get_form(self, form_class=None):
        form_class = form_class or self.get_form_class()
        # フォームに user インスタンスを渡す
        return form_class(user=self.request.user, **self.get_form_kwargs())

    def form_valid(self, form):
        data = form.cleaned_data
        icon_file = self.request.FILES.get("icon", None)
        user_id = str(self.request.user.pk)

        try:
            # サービス層を呼び出し、プロフィールを更新
            self.user_service.update_profile(
                user=self.request.user,
                display_name=data.get("display_name"),
                bio=data.get("bio") or None,
                career_history=data.get("career_history") or None,
                location=data.get("location") or None,
                skill_tags_raw=data.get("skill_tags_raw") or None,
                github_link=data.get("github_link") or None,
                x_link=data.get("x_link") or None,
                portfolio_blog_link=data.get("portfolio_blog_link") or None,
                is_public=data.get("is_public"),
                is_email_notify_enabled=data.get("is_email_notify_enabled"),
                is_notify_like=data.get("is_notify_like"),
                is_notify_comment=data.get("is_notify_comment"),
                is_notify_follow=data.get("is_notify_follow"),
                icon_file=icon_file,
            )

            messages.success(self.request, "プロフィールを更新しました！")
            return super().form_valid(form)

        except IntegrityError as e:
            # ログ出力: データベース整合性エラーを記録
            log_output_by_msg_id(
                log_id="MSGE801",
                params=[user_id, e.message_id, str(e.details)],
                logger_name=LOG_METHOD.APPLICATION.value,
                exc_info=True,  # スタックトレースを含める
            )
            # 例外クラスで定義されたメッセージを使用
            form.add_error(None, e.message)
            return self.form_invalid(form)

        except ExternalServiceError as e:
            # ログ出力: 外部サービスエラーを記録
            log_output_by_msg_id(
                log_id="MSGE802",
                params=[user_id, e.message_id],
                logger_name=LOG_METHOD.APPLICATION.value,
            )
            # 例外クラスで定義されたメッセージを使用
            form.add_error("icon", e.message)
            return self.form_invalid(form)

        except Exception as e:
            # ログ出力: 予期せぬエラーを記録（スタックトレースを含む）
            error_detail = f"プロフィール更新処理中にエラーが発生しました。ユーザーID: {user_id} エラー: {str(e)}"
            log_output_by_msg_id(
                log_id="MSGE002",
                params=[error_detail],
                logger_name=LOG_METHOD.APPLICATION.value,
                exc_info=True,  # 予測不可能なエラーのためスタックトレースを含める
            )
            messages.error(self.request, "予期せぬシステムエラーが発生しました。")
            return self.form_invalid(form)

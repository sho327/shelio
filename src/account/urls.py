from django.urls import path

from account.views.activate_user import ActivateUserView
from account.views.initial_setup import InitialSetupView
from account.views.login import LoginView
from account.views.logout import LogoutView
from account.views.password_reset_confirm import PasswordResetConfirmView
from account.views.password_reset_pending import PasswordResetPendingView
from account.views.password_reset_request import PasswordResetRequestView
from account.views.profile import ProfileView
from account.views.profile_edit import ProfileEditView
from account.views.register import RegisterView
from account.views.register_pending import RegisterPendingView

# app_nameを設定すると reverse_lazy("account:register_pending") が動作します
app_name = "account"

urlpatterns = [
    # ログイン画面を表示し、POSTで送信されたログイン情報を処理する
    path(
        "activate_user/<str:token_value>/",
        ActivateUserView.as_view(),
        name="activate_user",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("register_pending/", RegisterPendingView.as_view(), name="register_pending"),
    path(
        "password_reset_request/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password_reset_pending",
        PasswordResetPendingView.as_view(),
        name="password_reset_pending",
    ),
    path(
        "password_reset_confirm/<str:token_value>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "initial_setup/",
        InitialSetupView.as_view(),
        name="initial_setup",
    ),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
]

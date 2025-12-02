# from .views.account_create import AccountCreateViewSet
# from .views.login import LoginViewSet

# from .views.current_user_get import CurrentUserGetViewSet
# from .views.token_obtain_pair import TokenObtainPairView
# from .views.refresh_get import RefreshGetViewSet
# from .views.token_refresh import TokenRefreshView
# from .views.user_get import UserGetViewSet
# from .views.user_save import UserSaveViewSet
# from .views.user_delete import UserDeleteViewSet

# router = routers.DefaultRouter()
# router.register('create', AccountCreateViewSet, basename='account-create')
# router.register('activate', AccountCreateViewSet, basename='account-activate')
# router.register("login", LoginViewSet, basename="login")
# router.register("login", LoginViewSet, basename="login")
# router.register("refresh_get", RefreshGetViewSet, basename="refresh-get")
# router.register("current_user_get", CurrentUserGetViewSet, basename="current-user-get")
# router.register('user/get', UserGetViewSet, basename='user-get')
# router.register('user/list', UserListViewSet, basename='user-list')
# router.register('user/save', UserSaveViewSet, basename='user-save')
# router.register('user/delete', UserDeleteViewSet, basename='user-delete')
# urlpatterns = [
#     path("token/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path("token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
# ]

from django.urls import path

from dashboard.views.dashboard import DashboardView

urlpatterns = [
    # ログイン画面を表示し、POSTで送信されたログイン情報を処理する
    path("", DashboardView.as_view(), name="dashboard"),
    # ログアウト用のURLもついでに設定しておくと便利です
    # path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]

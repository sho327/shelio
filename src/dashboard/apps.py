from django.apps import AppConfig


class DashboardConfig(AppConfig):
    # アプリケーションの完全なドット区切りパス
    # プロジェクト名が 'config' だった場合: 'config.[name]'
    name = "dashboard"
    # label = "home"
    # 管理画面での表示名など（任意）
    verbose_name = "ダッシュボード機能"
    # データベースのスケーラビリティを確保するため、BigAutoFieldを明示的に指定
    default_auto_field = "django.db.models.BigAutoField"
    # モデルの定義があるサブモジュールを明示的に指定する
    # Djangoは通常 '[name].models' を探すが、サブモジュール分割時は明示的に指定することで確実になる
    # '[name].models' は '[name]/models/__init__.py' を指す
    # models_module = "[name].models"

    def ready(self):
        # アプリケーションのシグナルなどをロードする必要がある場合に記述します
        pass

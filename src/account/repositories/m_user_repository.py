from typing import overload

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from core.repositories import BaseRepository

User = get_user_model()
M_UserQuerySet = QuerySet[User]


class M_UserRepository(BaseRepository):
    """
    ユーザマスタ(User/M_User)モデル専用のリポジトリクラス。

    データ永続化層へのアクセスを抽象化し、ビジネスロジックから分離する役割を担う。
    論理削除の考慮や基本的なCRUD操作はBaseRepositoryに委譲し、本クラスではユーザー固有の検索条件を定義する。
    """

    # 必須：対象モデルを設定 (BaseRepositoryの初期化で使用される)
    model = User

    # ------------------------------------------------------------------
    # BaseRepositoryから継承される主なメソッド群
    # ------------------------------------------------------------------
    # 【内部QuerySet】
    # * _get_alive_queryset()      # 論理削除されていないレコードのベースQuerySet
    # * _get_deleted_queryset()    # 論理削除されたレコードのベースQuerySet
    # * _get_all_queryset()        # 論理削除済みを含む全てのレコードのベースQuerySet

    # 【主キー検索】
    # * get_alive_by_pk(pk)        # 主キーで「生存している」（論理削除されていない）レコードを取得
    # * get_deleted_by_pk(pk)      # 主キーで「論理削除された」レコードのみを取得
    # * get_all_by_pk(pk)          # 主キーで、論理削除の状態を問わず存在するレコードを取得

    # 【単一取得（条件検索）】
    # * get_alive_one_or_none(**kwargs)  # 論理削除されていないレコードから、条件で1件取得
    # * get_deleted_one_or_none(**kwargs)# 論理削除されたレコードから、条件で1件取得
    # * get_all_one_or_none(**kwargs)    # 論理削除の状態を問わず存在するレコードから、条件で1件取得

    # 【全件検索】
    # * get_alive_records()        # 全ての「生存している」（論理削除されていない）レコードを取得
    # * get_deleted_records()      # 全ての「論理削除された」レコードのみを取得
    # * get_all_records()          # 全ての論理削除の状態を問わず存在するレコードを取得

    # 【データ操作】
    # * create(**kwargs)           # レコードの作成
    # * update(instance, **kwargs) # レコードの更新
    # * soft_delete(instance)      # レコードの論理削除 (deleted_atを設定)
    # * hard_delete(instance)      # レコードの物理削除
    # * restore(instance)          # レコードの復元 (deleted_atをNULLに)

    # ------------------------------------------------------------------
    # 共通で追加されるメソッドの型付けだけ行う
    # ------------------------------------------------------------------
    # 【主キー検索】
    # @overload
    # def get_alive_by_pk(self, pk: int) -> User | None: ...
    # @overload
    # def get_deleted_by_pk(self, pk: int) -> User | None: ...
    # @overload
    # def get_all_by_pk(self, pk: int) -> User | None: ...

    # 【単一取得（条件検索）】
    # @overload
    # def get_alive_one_or_none(self, **kwargs) -> User | None: ...
    # @overload
    # def get_deleted_one_or_none(self, **kwargs) -> User | None: ...
    # @overload
    # def get_all_one_or_none(self, **kwargs) -> User | None: ...

    # 【全件検索】
    # @overload
    # def get_alive_records(self) -> M_UserQuerySet: ...
    # @overload
    # def get_deleted_records(self) -> M_UserQuerySet: ...
    # @overload
    # def get_all_records(self) -> M_UserQuerySet: ...

    # ------------------------------------------------------------------
    # モデルに対する固有のデータ取得処理
    # ------------------------------------------------------------------
    def get_all_active_users(self) -> M_UserQuerySet:
        """
        システムで利用可能な、有効なユーザー（is_active, メール認証済み, ACTIVEステータス）
        を全て取得する。
        """
        # BaseRepositoryの_get_alive_queryset()を利用し、論理削除されたユーザーを除外
        return self._get_alive_queryset().filter(
            # ログイン許可フラグ
            is_active=True,
            # メール認証済みフラグ
            is_email_verified=True,
            # アカウントステータスが「アクティブ」
            status_code=User.AccountStatus.ACTIVE,
        )

    # ------------------------------------------------------------------
    # 特殊処理/カスタムマネージャへの依存の隠蔽等
    # ------------------------------------------------------------------
    def create_user_with_password(self, email: str, password: str) -> User:
        """User.objects.create_user()をラップする（カスタムマネージャへの依存を隠蔽）"""
        return self.model.objects.create_user(email=email, password=password)

from typing import overload

from django.db.models import QuerySet

from account.models import T_UserToken
from core.repositories import BaseRepository

T_UserTokenQuerySet = QuerySet[T_UserToken]


class T_UserTokenRepository(BaseRepository):
    """
    ユーザ発行トークントラン(T_UserToken) モデル専用のリポジトリクラス。

    データ永続化層へのアクセスを抽象化し、ビジネスロジックから分離する役割を担う。
    論理削除の考慮や基本的なCRUD操作はBaseRepositoryに委譲し、本クラスではユーザー固有の検索条件を定義する。
    """

    # 必須：対象モデルを設定 (BaseRepositoryの初期化で使用される)
    model: T_UserToken = T_UserToken

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
    # def get_alive_by_pk(self, pk: int) -> T_UserToken | None: ...
    # @overload
    # def get_deleted_by_pk(self, pk: int) -> T_UserToken | None: ...
    # @overload
    # def get_all_by_pk(self, pk: int) -> T_UserToken | None: ...

    # 【単一取得（条件検索）】
    # @overload
    # def get_alive_one_or_none(self, **kwargs) -> T_UserToken | None: ...
    # @overload
    # def get_deleted_one_or_none(self, **kwargs) -> T_UserToken | None: ...
    # @overload
    # def get_all_one_or_none(self, **kwargs) -> T_UserToken | None: ...

    # 【全件検索】
    # @overload
    # def get_alive_records(self) -> T_UserTokenQuerySet: ...
    # @overload
    # def get_deleted_records(self) -> T_UserTokenQuerySet: ...
    # @overload
    # def get_all_records(self) -> T_UserTokenQuerySet: ...

    # ------------------------------------------------------------------
    # モデルに対する固有のデータ取得処理
    # ------------------------------------------------------------------

# core/scripts/generate_test_user.py

import os
import random
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.db import transaction

# ----------------------------------------------------
# 1. 定数と初期設定
# ----------------------------------------------------
User = get_user_model()
# M_UserProfileRepository は services.py からインポートされることを想定
# from account.repositories.m_user_profile_repository import M_UserProfileRepository
# profile_repo = M_UserProfileRepository()

# ----------------------------------------------------
# 2. メインロジック
# ----------------------------------------------------


@transaction.atomic
def generate_test_users(count: int, password: str = "testpass", is_staff: bool = False):
    """
    指定された数のテストユーザーを生成する。

    Args:
        count (int): 作成するユーザー数。
        password (str): 設定するパスワード。
        is_staff (bool): 管理者権限（is_staff, is_superuser）を付与するか。
    """
    if count <= 0:
        print("作成するユーザー数は1以上である必要があります。")
        return

    print(f"--- テストユーザー生成開始 (目標: {count}名) ---")
    created_count = 0

    try:
        for i in range(1, count + 1):
            unique_id = f"testuser_{random.randint(10000, 99999)}_{i}"
            email = f"{unique_id}@example.com"
            display_name = f"テストユーザー {i}"

            # 1. M_Userの作成 (user_idはUUIDなどでリポジトリ側で生成されることを想定)
            # ここでは、簡略化のためUser.objects.create_userを直接使用
            # 💡 本来は UserService.register_new_user() を使うべき
            user = User.objects.create_user(
                # user_id が必須の場合、ここで生成する必要がある
                user_id=unique_id,
                email=email,
                password=password,
                is_active=True,  # テスト用なのでアクティベーションはスキップ
                is_staff=is_staff,
                is_superuser=is_staff,
            )

            # 2. M_UserProfileの更新 (シグナルで作成される前提)
            # profile_repo.update(user.m_user_profile, display_name=display_name)

            created_count += 1
            print(f"  [+] ユーザー作成: {email} (PW: {password})")

        print(f"\n-> 成功: {created_count} 件のテストユーザーを作成しました。")

    except Exception as e:
        print(f"\n致命的なエラーが発生し、処理を中断しました: {e}")
        # transaction.atomic() により、例外発生時はロールバックされます
        raise


# ----------------------------------------------------
# 3. 実行エントリポイント
# ----------------------------------------------------
if __name__ == "__main__":
    # 実行引数のパース（簡易版）
    try:
        if len(sys.argv) < 2:
            print(
                "使用方法: python generate_test_user.py <作成数> [管理者フラグ: --admin]"
            )
            sys.exit(1)

        # 第1引数をユーザー数として取得
        user_count = int(sys.argv[1])

        # --admin フラグのチェック
        is_admin = "--admin" in sys.argv

        # 実行
        generate_test_users(user_count, is_staff=is_admin)

    except ValueError:
        print("エラー: 作成数は整数で指定してください。")
    except Exception as e:
        print(f"実行中に予期せぬエラーが発生しました: {e}")


"""
【実行方法】
このスクリプトは、manage.py の外で直接Pythonスクリプトとして実行できます。
（__name__ == "__main__" ブロックを使用）

一般ユーザーを10人作成
[Bash]
python core/scripts/generate_test_user.py 10

管理者ユーザーを1人作成
[Bash]
ython core/scripts/generate_test_user.py 1 --admin
"""

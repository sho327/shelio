# 🚀 Django カスタム認証とサインアップ機能の実装まとめ

本ドキュメントでは、カスタムフォームを使用したログイン・サインアップビューの構築と、サービス層におけるセキュリティと保守性を高めるための例外処理戦略についてまとめます。

---

## 1\. ユーザー認証（ログイン）ビューの実装

標準の `LoginView` ではなく、カスタムなビジネスロジックを組み込むため `FormView` を使用します。

### 📄 `account/views.py`

- **CustomLoginView**:
  - `FormView` を継承し、カスタムフォーム (`CustomAuthenticationForm`) を利用。
  - `form_valid()` メソッド内で、カスタム認証サービス (`AuthService`) を呼び出し、認証処理を実行。
  - 認証成功後、Django 標準の `login(self.request, user)` でセッションを確立。

### 🌐 `next` パラメータの安全な処理

ログイン後、元々アクセスしようとしていたページ（`?next=/dashboard/`）へリダイレクトするためのロジックを `get_success_url` に実装します。

```python
# CustomLoginView クラス内

from django.utils.http import url_has_allowed_host_and_scheme

def get_success_url(self):
    next_url = self.request.POST.get('next') or self.request.GET.get('next')

    # ⭐ セキュリティチェック ⭐
    # next パラメータが安全なホスト内のURLであることを確認（オープンリダイレクト防止）
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts=self.request.get_host(),
        require_https=self.request.is_secure()
    ):
        return next_url

    return self.success_url
```

---

## 2\. 新規ユーザー登録（サインアップ）の実装

### 📄 `account/forms/signup.py`

- **CustomSignupForm**: メールアドレス、パスワード、**表示名 (`display_name`)**、パスワード確認フィールドを持つフォームを定義。
- `clean()` メソッド内で、**パスワードの一致確認**を行う。
- `clean_email()` メソッド内で、**メールアドレスの重複チェック**を行う。

### 📄 `account/views.py`

- **CustomSignupView**: `FormView` を継承。
- `form_valid()` 内で、**`UserService.register_new_user`** を呼び出し、ユーザー登録とアクティベーション処理を実行。
- 登録成功後、そのまま `login()` 関数を呼び出し、ユーザーをセッションに登録（またはメール確認画面へリダイレクト）。

---

## 3\. 🛡️ サービス層における例外処理戦略

データベースの整合性や、システム内部の情報漏洩を防ぐため、**サービス層**は**例外翻訳の境界線**として機能します。

### 3.1. 例外の階層構造

カスタム例外は、**`core.exceptions.ApplicationError`** を基底クラスとして継承し、ドメイン固有のエラーを定義します。

- `ApplicationError` (core)
  - `AccountError` (account)
    - `AuthenticationFailedException` (認証失敗)
    - `AccountLockedException` (アカウント無効)
  - `DuplicationError` (core, データ重複)
  - `IntegrityError` (core, DB 整合性エラー)
  - `ExternalServiceError` (core, 外部連携エラー)

### 3.2. サインアップ時の例外翻訳の必要性

**データベースの登録/更新処理**、および\*\*外部サービス（メール送信）\*\*を伴う処理 (`UserService.register_new_user`) は、必ず `try...except` で囲み、低レベルなシステム例外を抽象化します。

| 発生源の処理                     | 低レベル例外（例）         | 翻訳後の高レベル例外                       |
| :------------------------------- | :------------------------- | :----------------------------------------- |
| **ユーザー・トークン作成**       | `django.db.IntegrityError` | `DuplicationError` または `IntegrityError` |
| **アクティベーションメール送信** | `smtplib.SMTPException`    | `ExternalServiceError`                     |

```python
# UserService.register_new_user の骨子

try:
    # 1. ユーザー作成 (DB変更)
    # 2. メール送信 (外部連携)
    pass
except DjangoIntegrityError as e:
    # データベースのエラーをキャッチ
    raise DuplicationError(details={"db_info": "hidden"})
except Exception as e:
    # その他の予期せぬエラーをキャッチ
    raise IntegrityError(message="登録処理中に予期せぬエラーが発生しました。")
```

### 3.3. ログイン処理に `try...except` が不要な理由

ログイン (`AuthService.login`) は主に **SELECT 操作**と**条件チェック**のみであり、発生するエラーは `user is None` や `user.is_active` といった**予測可能なビジネス上の状態**に基づいているため、明示的な `if` チェックで十分であり、広範囲の `try...except` は通常不要です。

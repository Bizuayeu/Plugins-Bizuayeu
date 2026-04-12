# OAuth 2.0 Setup Guide

GmailGrabber を使うためには Google Cloud Console で OAuth 2.0 credentials を取得する必要があります。

## 手順

### 1. Google Cloud Console でプロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 画面上部のプロジェクト選択 → 「新しいプロジェクト」
3. プロジェクト名: `GmailGrabber` (任意)
4. 「作成」

### 2. Gmail API の有効化

1. 左メニュー「APIとサービス」→「ライブラリ」
2. 検索窓に `Gmail API` と入力
3. Gmail API を選択 → 「有効にする」

### 3. OAuth 同意画面の設定

1. 左メニュー「APIとサービス」→「OAuth同意画面」
2. User Type: **External** を選択 → 作成
3. 必須項目を入力:
   - アプリ名: `GmailGrabber` (任意)
   - ユーザーサポートメール: 自分のGmailアドレス
   - デベロッパー連絡先: 自分のGmailアドレス
4. 「保存して次へ」
5. スコープ: そのまま「保存して次へ」(後で add or remove)
6. テストユーザー: バックアップ対象のGmailアドレスを追加
7. 「保存して次へ」→「ダッシュボードに戻る」

**注意**: 公開状態を **Testing** のままにしておくこと。**Production** にすると Google の審査が必要になります。Testing モードでも自分のアカウントは使えます。

### 4. OAuth クライアント ID の作成

1. 左メニュー「APIとサービス」→「認証情報」
2. 画面上部「認証情報を作成」→「OAuth クライアント ID」
3. アプリケーションの種類: **デスクトップ アプリ**
4. 名前: `GmailGrabber CLI` (任意)
5. 「作成」

### 5. client_secret.json のダウンロード

1. 作成された OAuth クライアント ID の右側のダウンロードアイコンをクリック
2. JSON をダウンロード
3. ファイル名を `client_secret.json` にリネーム
4. 安全な場所に保存 (例: `~/.gmailgrabber/client_secret.json`)

**セキュリティ注意**: `client_secret.json` は機密情報。Git にコミットしない。`.gitignore` に追加済み。

### 6. ディレクトリ準備

Windows の例:
```bash
mkdir -p "$APPDATA/GmailGrabber"
cp ~/Downloads/client_secret_*.json "$APPDATA/GmailGrabber/client_secret.json"
```

Linux/macOS の例:
```bash
mkdir -p ~/.config/gmailgrabber
cp ~/Downloads/client_secret_*.json ~/.config/gmailgrabber/client_secret.json
chmod 600 ~/.config/gmailgrabber/client_secret.json
```

### 7. 初回認証

```bash
cd /path/to/plugins-bizuayeu/GmailGrabber
PYTHONPATH=scripts python -m interfaces.auth_cli \
  --email your-account@gmail.com \
  --client-secret /path/to/client_secret.json
```

実行するとブラウザが自動で開き、Google アカウント選択画面が表示されます。

1. 対象アカウントを選択
2. 「このアプリは Google で確認されていません」の警告が出たら:
   - 「詳細」→「(安全でないページ) に移動」をクリック (テストモードのため)
3. 「GmailGrabber が Google アカウントへのアクセスをリクエストしています」→「許可」
4. 「認証フローが完了しました」の画面 → ブラウザを閉じる

成功すると `~/.config/gmailgrabber/token_<label>.json` が保存され、以後は自動で使われます (有効期限切れ時は refresh token で自動更新)。

## トラブルシューティング

### `invalid_client` エラー

`client_secret.json` のパスを確認。ファイルが壊れていないか、正しい OAuth クライアント ID (Desktop app) で作成されているかチェック。

### `access_denied` エラー

OAuth 同意画面のテストユーザーにバックアップ対象のアカウントを追加していない可能性。設定を確認。

### `invalid_grant` (token refresh 失敗)

token が長期間使われなかった、またはパスワード変更等で invalidate された。`token_*.json` を削除して再認証。

### ブラウザが開かない

`--config-dir` で明示的に config ディレクトリを指定して試す。ヘッドレス環境では `google-auth-oauthlib` の `run_local_server` は動作しないため、デスクトップ環境で認証する必要がある。

## スコープについて

デフォルトは **読み取り専用** (`gmail.readonly`):
- メッセージの閲覧・ダウンロードのみ可能
- 削除・送信はできない

バックアップ用途ではこれで十分です。より広いスコープが必要な場合は `--scope` (未実装) で指定予定。

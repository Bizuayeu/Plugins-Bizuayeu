---
description: OAuth 2.0 認証フローを実行して Gmail アカウントに接続する
---

# /gmail-auth

Gmail アカウントの OAuth 2.0 認証を行います。初回認証時はブラウザが開き、
Google アカウントへのアクセス許可を求めます。認証成功後は token が
config ディレクトリに保存され、以後は自動で使い回されます。

## 使い方

```bash
python -m interfaces.auth_cli \
  --email <gmail-address> \
  --client-secret <path/to/client_secret.json> \
  [--config-dir <path>] \
  [--label <short-name>]
```

## パラメータ

- `--email` (必須): 認証対象の Gmail アドレス
- `--client-secret` (必須): Google Cloud Console から取得した OAuth client_secret.json
- `--config-dir` (任意): token 保存先ディレクトリ（デフォルト: Platform 固有）
- `--label` (任意): ファイル名用の短縮ラベル（デフォルト: email のローカル部）

## 前提条件

1. Google Cloud Console で Gmail API を有効化
2. OAuth 同意画面を設定
3. OAuth 2.0 クライアント ID (Desktop app) を作成し client_secret.json をダウンロード

詳細は [docs/OAuth_Setup.md](../docs/OAuth_Setup.md) を参照。

## 実行例

```bash
cd /path/to/GmailGrabber
PYTHONPATH=scripts python -m interfaces.auth_cli \
  --email togami-log@meguru-construction.example.jp \
  --client-secret ~/.gmailgrabber/client_secret.json
```

## 出力

JSON (status=ok):
```json
{
  "status": "ok",
  "email": "togami-log@meguru-construction.example.jp",
  "label": "togami-log",
  "token_path": "/home/user/.config/gmailgrabber/token_togami-log.json",
  "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
  "expires_at": "2026-04-11T16:00:00+00:00"
}
```

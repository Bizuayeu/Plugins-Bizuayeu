---
description: Clean Architecture で実装された Gmail バックアップツール。OAuth認証、検索クエリベース取得、.eml/.mbox出力、再開機構をサポート
---

# GmailGrabber

Clean Architecture × TDD で構築された Gmail バックアップツールです。

## 設計思想

- **Clean Architecture 4層**: domain / application / infrastructure / interfaces
- **Protocol による依存関係逆転**: application層は infrastructureを直接importしない
- **TypedDict ドメインモデル**: 実行時オーバーヘッドゼロ、JSON相互運用
- **TDD 先行**: domain / application / infrastructure の各層に RED→GREEN→REFACTOR で書かれたテストがある（件数は `python -m pytest scripts/test/` が SSoT）

## コマンド

| コマンド | 用途 | スキル |
|---|---|---|
| `/gmail-auth` | OAuth 2.0 認証フロー | [commands/gmail-auth.md](../../commands/gmail-auth.md) |
| `/gmail-backup` | 検索クエリでバックアップ実行 | [commands/gmail-backup.md](../../commands/gmail-backup.md) |
| `/gmail-labels` | ラベル一覧取得 | [commands/gmail-labels.md](../../commands/gmail-labels.md) |
| `/gmail-multi-backup` | Service Account + DWD で Workspace 複数ユーザーを一括取得 | [commands/gmail-multi-backup.md](../../commands/gmail-multi-backup.md) |

## セットアップ手順

### 1. Google Cloud Console でプロジェクト作成

[docs/OAuth_Setup.md](../../docs/OAuth_Setup.md) の手順を参照。

要点:
1. Google Cloud Console で新規プロジェクト作成
2. Gmail API を有効化
3. OAuth 同意画面を構成（External、Testing状態でOK）
4. OAuth 2.0 クライアント ID (Desktop app) を作成
5. `client_secret.json` をダウンロード

### 2. 依存関係確認

```bash
python -c "import googleapiclient, google.auth, google_auth_oauthlib"
```

### 3. 認証

```bash
cd /path/to/plugins-bizuayeu/GmailGrabber
PYTHONPATH=scripts python -m interfaces.auth_cli \
  --email your-account@gmail.com \
  --client-secret /path/to/client_secret.json
```

初回はブラウザが開くので Google アカウントでログインし、アクセス許可。

### 4. バックアップ実行

```bash
PYTHONPATH=scripts python -m interfaces.backup_cli \
  --email your-account@gmail.com \
  --client-secret /path/to/client_secret.json \
  --output-dir /path/to/output \
  --format eml \
  --after 2026/04/01 --before 2026/04/12
```

## 運用層の使い方

### 典型的な月次バックアップ

togami-log@ の 4月分を BusinessWiki に保存:

```bash
PYTHONPATH=scripts python -m interfaces.backup_cli \
  --email togami-log@meguru-construction.example.jp \
  --client-secret ~/.gmailgrabber/client_secret.json \
  --output-dir '/path/to/workspace/BusinessWiki/data/2026-04' \
  --format eml \
  --after 2026/04/01 --before 2026/04/12
```

### 大量メール取得の中断・再開

1000件以上のバックアップ時、ネットワーク切断等で中断された場合:
- デフォルトで state ファイルが config ディレクトリ配下の `state/` に保存される（config ディレクトリは Windows が `%APPDATA%/GmailGrabber`、Unix が `~/.config/gmailgrabber`。`--config-dir` で上書き可）
- 同じコマンドで再実行 → 既取得分はスキップして続きから取得
- 完全にやり直したい場合は `--no-resume` フラグ

### 特定ラベルのみバックアップ

まずラベル一覧を確認:
```bash
PYTHONPATH=scripts python -m interfaces.labels_cli \
  --email togami-log@meguru-construction.example.jp \
  --client-secret ~/.gmailgrabber/client_secret.json
```

その後、`--label` で絞り込み:
```bash
PYTHONPATH=scripts python -m interfaces.backup_cli \
  --email togami-log@meguru-construction.example.jp \
  --client-secret ~/.gmailgrabber/client_secret.json \
  --output-dir /path/to/output \
  --label "案件/高尾"
```

## 開発者向け

### テスト実行

```bash
python -m pytest scripts/test/
```

### 型チェック

```bash
python -m mypy scripts/
```

### ディレクトリ構造

```
GmailGrabber/
├── README.md            # 入口（セットアップ・使い方）
├── scripts/
│   ├── domain/          # TypedDict, Protocol, 純関数
│   ├── application/     # UseCase
│   ├── infrastructure/  # Google API, Writers, State
│   ├── interfaces/      # CLI
│   └── test/            # pytest + hypothesis
├── commands/            # スラッシュコマンド定義
├── skills/
│   └── gmail-grabber/   # スキル定義
├── docs/                # OAuth setup等
└── pyproject.toml
```

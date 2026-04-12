# GmailGrabber (v0.2.0)

Clean Architecture × TDD で構築する Gmail バックアップツール。
個人 OAuth 認証と Workspace Service Account + DWD (Domain-Wide Delegation) の
両方をサポート。複数ユーザー取得時は RFC5322 Message-ID で重複排除します。

## 設計原則

1. **Clean Architecture 4層分離** (domain / application / infrastructure / interfaces)
2. **TDD (Red → Green → Refactor)** による段階的構築
3. **Protocol による依存関係逆転** — application層はinfrastructureを直接importしない
4. **TypedDict** によるドメインモデル (実行時オーバーヘッドゼロ、JSON相互運用)
5. **mypy strict + ruff + pytest + hypothesis** の品質ゲート

## 機能

### v0.1.0 (個人 OAuth)
- Gmail API 経由のメッセージ取得 (OAuth 2.0)
- 検索クエリ指定 (from, to, date range, label, has attachment)
- 出力形式: `.eml` (1メール1ファイル) / `.mbox` (一括束ね)
- 複数アカウント対応
- 中断・再開機構 (fetched IDs state persistence)
- ラベル一覧取得

### v0.2.0 (Workspace Multi-User)
- **Service Account + Domain-Wide Delegation** で複数ユーザー一括取得
- **RFC5322 Message-ID** ベースの重複排除 (CC配信メール対応)
- 全ユーザー跨ぎの `message_id_index` による first-wins 方式
- Message-ID 欠落メールの強制保存 + 警告出力
- user 単位の中断・再開

## ディレクトリ構造

```
GmailGrabber/
├── .claude-plugin/plugin.json
├── commands/                    # スラッシュコマンド定義
├── skills/gmail-grabber/        # スキル定義
├── docs/                        # OAuth setup等
├── pyproject.toml
└── scripts/
    ├── domain/                  # TypedDict, Protocol, 純関数
    ├── application/             # UseCase
    ├── infrastructure/          # Gmail API実装, ファイル書き出し
    ├── interfaces/              # CLI
    └── test/                    # pytest + hypothesis
```

## コマンド

| コマンド | 用途 |
|---|---|
| `/gmail-auth` | OAuth認証フロー |
| `/gmail-backup` | 単一ユーザーで検索クエリバックアップ |
| `/gmail-labels` | ラベル一覧取得 |
| `/gmail-multi-backup` | **v0.2.0:** Workspace 複数ユーザー SA 一括バックアップ + 重複排除 |

## セットアップ

### 1. OAuth credentials の準備

[docs/OAuth_Setup.md](docs/OAuth_Setup.md) 参照。Google Cloud Console で Gmail API を有効化し、`client_secret.json` を取得。

### 2. 認証

```bash
/gmail-auth --email togami-log@meguru-construction.com
```

### 3. バックアップ実行

```bash
/gmail-backup --email togami-log@meguru-construction.com \
              --after 2026/04/01 --before 2026/04/12 \
              --output-dir /path/to/data/2026-04 \
              --format eml
```

## 開発

```bash
# テスト実行
python -m pytest scripts/test/

# 型チェック
python -m mypy scripts/

# フォーマット・リント
python -m ruff check scripts/
python -m ruff format scripts/
```

## ライセンス

MIT License

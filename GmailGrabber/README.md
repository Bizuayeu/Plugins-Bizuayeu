# GmailGrabber (v0.2.0)

Clean Architecture × TDD で構築する Gmail バックアップツール。
個人 OAuth 認証と Workspace Service Account + DWD (Domain-Wide Delegation) の
両方をサポート。複数ユーザー取得時は RFC5322 Message-ID で重複排除します。

> BusinessCurator の `data/` ディレクトリに `.eml` / `.mbox` を供給する
> パイプラインの入口として機能します。

---

## 設計原則

1. **Clean Architecture 4層分離** (domain / application / infrastructure / interfaces)
2. **TDD (Red → Green → Refactor)** による段階的構築
3. **Protocol による依存関係逆転** — application 層は infrastructure を直接 import しない
4. **TypedDict** によるドメインモデル (実行時オーバーヘッドゼロ、JSON 相互運用)
5. **mypy strict + ruff + pytest + hypothesis** の品質ゲート

---

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
- **RFC5322 Message-ID** ベースの重複排除 (CC 配信メール対応)
- 全ユーザー跨ぎの `message_id_index` による first-wins 方式
- Message-ID 欠落メールの強制保存 + 警告出力
- user 単位の中断・再開

---

## コマンド

| コマンド | 用途 |
|---|---|
| `/gmail-auth` | OAuth 認証フロー |
| `/gmail-backup` | 単一ユーザーで検索クエリバックアップ |
| `/gmail-labels` | ラベル一覧取得 |
| `/gmail-multi-backup` | Workspace 複数ユーザー SA 一括バックアップ + 重複排除 |

---

## ディレクトリ構造

```
GmailGrabber/
├── commands/                    # 4 command md
├── skills/gmail-grabber/        # 1 skill md
├── docs/
│   ├── OAuth_Setup.md           # 個人 OAuth セットアップ
│   └── Multi_User_Setup.md     # SA + DWD セットアップ
├── pyproject.toml
└── scripts/
    ├── domain/                  # TypedDict, Protocol, 純関数
    ├── application/             # UseCase
    ├── infrastructure/          # Gmail API 実装, ファイル書き出し
    ├── interfaces/              # CLI
    └── test/                    # 274 tests (pytest + hypothesis)
        ├── domain_tests/
        ├── application_tests/
        ├── infrastructure_tests/
        ├── cli_integration_tests/
        ├── integration_tests/
        └── fixtures/
```

---

## セットアップ

### 個人 OAuth

1. [docs/OAuth_Setup.md](docs/OAuth_Setup.md) 参照。Google Cloud Console で Gmail API を有効化し、`client_secret.json` を取得
2. 認証:
   ```bash
   /gmail-auth --email user@example.com
   ```
3. バックアップ:
   ```bash
   /gmail-backup --email user@example.com \
                 --after 2026/04/01 --before 2026/04/12 \
                 --output-dir /path/to/data/2026-04 \
                 --format eml
   ```

### Workspace Service Account + DWD

1. [docs/Multi_User_Setup.md](docs/Multi_User_Setup.md) 参照。Service Account の作成と DWD 設定
2. 一括バックアップ:
   ```bash
   /gmail-multi-backup --sa-key /path/to/sa-key.json \
                       --users user1@corp.com,user2@corp.com \
                       --after 2026/04/01 \
                       --output-dir /path/to/data/2026-04
   ```

---

## 開発

### テスト実行

```bash
cd plugins-bizuayeu/GmailGrabber

# 全テスト
python -m pytest scripts/test/ -q --no-cov
# → 274 passed

# レイヤ別
python -m pytest scripts/test/domain_tests/ -v
python -m pytest scripts/test/application_tests/ -v
python -m pytest scripts/test/infrastructure_tests/ -v
python -m pytest scripts/test/cli_integration_tests/ -v
```

### 静的解析

```bash
python -m mypy scripts/ --strict
python -m ruff check scripts/
python -m ruff format scripts/
```

---

## 品質指標

| 項目 | 値 |
|---|---|
| **テスト数** | **274 passed** |
| **mypy strict** | 82 source files checked |
| **ruff** | 有効 |
| **TDD サイクル** | Red → Green → Refactor を全機能で遵守 |

---

## Changelog

### v0.2.0 (2026-04-12)

- **Service Account + DWD**: Workspace 複数ユーザー一括取得
- **RFC5322 Message-ID 重複排除**: CC 配信メールの二重取得防止
- **`/gmail-multi-backup`** コマンド追加
- **`docs/Multi_User_Setup.md`** 追加

### v0.1.0 (2026-04-12)

- 初回リリース: 個人 OAuth、検索クエリバックアップ、.eml/.mbox 出力、中断・再開機構

---

## ライセンス

MIT License

---

## クレジット

- 計画策定: Weave @ Claude Opus 4.6 (1M context)
- 要件確認: 大環主
- 実装環境: Claude Code + Plugins-Weave

参照プラグイン:
- [BusinessCurator](../BusinessCurator/) — Clean Architecture × TDD パターン元祖、メール知識の消費先
- [EpisodicRAG](https://github.com/Bizuayeu/Plugins-Weave) — Clean Architecture × TDD パターン提供

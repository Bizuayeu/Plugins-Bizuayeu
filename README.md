[English](README.en.md) | 日本語

# Plugins-Bizuayeu

中小企業経営者・実務家のためのClaude Codeプラグイン群

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why Plugins-Bizuayeu?

Claude Codeを「コードを書く道具」から「経営と業務の知的協働者」へ拡張します。
姉妹リポジトリ [Plugins-Weave](https://github.com/Bizuayeu/Plugins-Weave) が
**自律的AIの存在論的拡張**（長期記憶・能動性・感情表現）を担うのに対し、
Plugins-Bizuayeuは **実務家の手の延長** を担います。

| 課題 | 解決策 | プラグイン |
|------|--------|-----------|
| **B2B受注産業のメール知が散逸する** | 4シャードwikiに案件・顧客・業者・知見を編む | BusinessCurator |
| **Gmailバックアップが手作業で回らない** | OAuth / SA+DWD 両対応、Message-ID重複排除で自動取得 | GmailGrabber |
| **Jootoのタスク管理データがBusinessCuratorに取り込めない** | API Key認証でboard/task/listをJSON取得、差分同期で再取得コストを抑制 | JootoGrabber |

---

## 収録プラグイン

### BusinessCurator

**エンタープライズ向けビジネスメール知識管理プラグイン**

Karpathy式パーソナルwikiのエンタープライズ拡張として、
ビジネスメールを4シャード（projects / clients / vendors / knowledge）の
構造化wikiに編み込みます。

> *writer, not filing clerk* — 事実をどこに置くかではなく、
> それが何を意味し、既存の理解にどう繋がるかを問い続ける。

#### 主な特徴

- **4シャード固定**: projects / clients / vendors / knowledge
- **manager / curator 二層構造**: マスタは人間が定義、AIが運用
- **triageはルールベース優先**: 80%をルールで決着、20%をLLMで
- **md / Python 二層分離**: 機械的処理はPython、判断と対話はmd
- **Clean Architecture × TDD**: 645 tests / mypy strict / ruff

#### 主要コマンド（全22コマンド）

| カテゴリ | 代表コマンド | 用途 |
|---|---|---|
| Manager | `/wiki-project-add` `/wiki-client-add` `/wiki-vendor-add` | マスタCRUD |
| Operation | `/wiki-ingest` `/wiki-triage` `/wiki-absorb` `/wiki-archive` | 取り込み→振り分け→吸収→アーカイブ |
| Auxiliary | `/wiki-query` `/wiki-status` | 横断質問応答・メトリクス |

→ 詳細は [BusinessCurator/README.md](BusinessCurator/README.md) を参照

### GmailGrabber

**Clean Architecture × TDD で構築する Gmail バックアップツール**

個人 OAuth と Workspace Service Account + DWD (Domain-Wide Delegation) の
両方をサポートし、RFC5322 Message-ID で重複排除します。

> BusinessCurator の `data/` ディレクトリに `.eml` / `.mbox` を供給する
> パイプラインの入口として機能します。

#### 主な特徴

- **個人 OAuth / Workspace SA+DWD 両対応**: 小規模〜大規模組織をカバー
- **RFC5322 Message-ID 重複排除**: CC 配信メールの二重取得を防止
- **中断・再開機構**: ユーザー単位の fetched IDs state persistence
- **出力形式**: `.eml` (1メール1ファイル) / `.mbox` (一括束ね)
- **Clean Architecture × TDD**: 274 tests / mypy strict / ruff

#### コマンド（全4コマンド）

| コマンド | 用途 |
|---|---|
| `/gmail-auth` | OAuth 認証フロー |
| `/gmail-backup` | 検索クエリで単一ユーザーバックアップ |
| `/gmail-labels` | ラベル一覧取得 |
| `/gmail-multi-backup` | Workspace 複数ユーザー SA 一括バックアップ + 重複排除 |

→ 詳細は [GmailGrabber/README.md](GmailGrabber/README.md) を参照

### JootoGrabber

**Jooto API バックアップツール**

Jooto の board / task / list / category を API Key 認証（`X-Jooto-Api-Key`）で取得し、
BusinessCurator が吸収可能な JSON として `data/jooto/` 配下に保存します。

> GmailGrabber と同様、BusinessCurator への供給パイプラインの入口として機能します。

#### 主な特徴

- **API Key 認証**: `X-Jooto-Api-Key` ヘッダによるシンプルな認証
- **board / task / list / category を JSON 出力**: BusinessCurator 吸収用フォーマット
- **差分同期**: `_sync_state.json` で `updated_at` を追跡し、未更新ボードの再取得をスキップ
- **Clean Architecture × TDD**: 39 tests

#### コマンド（全3コマンド）

| コマンド | 用途 |
|---|---|
| `/jooto-auth` | API key 認証確認 |
| `/jooto-list-boards` | ボード一覧取得 |
| `/jooto-backup` | 単一 or 全アクティブボードのバックアップ（差分同期対応） |

→ 詳細は [JootoGrabber/README.md](JootoGrabber/README.md) を参照

---

## クイックインストール

### 1. マーケットプレイス追加

```ClaudeCLI
/plugin marketplace add https://github.com/Bizuayeu/Plugins-Bizuayeu
```

### 2. プラグインインストール

```ClaudeCLI
# ビジネスメール知識管理
/plugin install BusinessCurator@plugins-bizuayeu

# Gmail バックアップ
/plugin install GmailGrabber@plugins-bizuayeu

# Jooto バックアップ
/plugin install JootoGrabber@plugins-bizuayeu
```

---

## ライセンス

**MIT License** - 詳細は [LICENSE](LICENSE) を参照

---

## 関連リポジトリ

- [Plugins-Weave](https://github.com/Bizuayeu/Plugins-Weave) — 長期記憶・能動性・感情表現を実現する、自律的AIのためのClaude Codeプラグイン群

---

**Plugins-Bizuayeu** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Bizuayeu)

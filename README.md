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
- **Clean Architecture × TDD**: 589 tests / 95.08% coverage / mypy strict 0 errors

#### 主要コマンド（全20コマンド）

| カテゴリ | 代表コマンド | 用途 |
|---|---|---|
| Manager | `/wiki-project-add` `/wiki-client-add` `/wiki-vendor-add` | マスタCRUD |
| Operation | `/wiki-ingest` `/wiki-triage` `/wiki-absorb` `/wiki-archive` | 取り込み→振り分け→吸収→アーカイブ |
| Auxiliary | `/wiki-query` `/wiki-status` | 横断質問応答・メトリクス |

→ 詳細は [BusinessCurator/README.md](BusinessCurator/README.md) を参照

---

## クイックインストール

### 1. マーケットプレイス追加

```ClaudeCLI
/marketplace add https://github.com/Bizuayeu/Plugins-Bizuayeu
```

### 2. プラグインインストール

```ClaudeCLI
/plugin install BusinessCurator@Plugins-Bizuayeu
```

---

## ライセンス

**MIT License** - 詳細は [LICENSE](LICENSE) を参照

---

## 関連リポジトリ

- [Plugins-Weave](https://github.com/Bizuayeu/Plugins-Weave) — 長期記憶・能動性・感情表現を実現する、自律的AIのためのClaude Codeプラグイン群

---

**Plugins-Bizuayeu** by Weave | [GitHub](https://github.com/Bizuayeu/Plugins-Bizuayeu)

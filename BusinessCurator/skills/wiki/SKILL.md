---
name: wiki
description: BusinessCurator - エンタープライズ向けビジネスメール知識管理。triage で振り分け、curator で wiki 化、archive で卒業させる。writer, not filing clerk.
---

# BusinessCurator

ビジネスメールを **4 シャード wiki** (projects / clients / vendors / knowledge) に編み込む知識管理プラグインです。
原則は wiki スキルを継承: **writer, not filing clerk**。事実をどこに置くかではなく、それが何を意味し、既存の理解にどう繋がるかを問い続けます。

このスキルは**ナビゲーター**として機能します。実際の処理は専門スキルと CLI に委譲します。

---

## 設計原則

1. **シャードは4種固定**、シャード内のカテゴリはデータから有機的に創発する
2. **manager 層と curator 層を分離**: マスタデータ（案件・得意先・取引先・知見カテゴリ）は人間が定義し、AI が運用する
3. **triage はルールベース優先**、LLM フォールバック（Claude CLI）は2割
4. **archive は手動発動**、知見抽出は半自動化して暗黙知の消失を防ぐ
5. **md で済むものを Python 化しない**: 判断・対話・キュレーションは md、機械的処理だけ Python

---

## ディレクトリ構造

```
BusinessCurator/
  _root.md                  ← ルート wiki
  _alias_resolver.md          ← 全シャード統合エイリアス解決器
  triage_logs/              ← 振り分け履歴
  data/                     ← 生メール（.eml/.mbox、変更不可）
  inbox/
    raw-entries/             ← ingest 済み・triage 待ち
    unclassified/           ← triage 分類不能・ユーザー確認待ち
  shards/
    projects/{Name}/_project.md
    clients/{Name}.md
    vendors/{Name}.md
    knowledge/{Category}/*.md
  archive/projects/{CompletedName}/
```

---

## コマンド全 21 件

### Manager 層（マスタデータ CRUD）

manager は `[project-manager.md](project-manager.md)` / `[client-manager.md](client-manager.md)` / `[vendor-manager.md](vendor-manager.md)` / `[knowledge-manager.md](knowledge-manager.md)` を参照。

| コマンド | スキル | 用途 |
|---|---|---|
| `/wiki-project-add` | project-manager | 案件を新規登録 |
| `/wiki-project-edit` | project-manager | 案件のメタデータ更新 |
| `/wiki-project-close` | project-manager | 案件を完了マーク（archive 発動準備） |
| `/wiki-client-add` | client-manager | 得意先を登録 |
| `/wiki-client-edit` | client-manager | 得意先を編集 |
| `/wiki-client-remove` | client-manager | 得意先を論理削除 |
| `/wiki-vendor-add` | vendor-manager | 取引先を登録 |
| `/wiki-vendor-edit` | vendor-manager | 取引先を編集 |
| `/wiki-vendor-remove` | vendor-manager | 取引先を論理削除 |
| `/wiki-knowledge-add-domain` | knowledge-manager | 知見カテゴリを追加 |
| `/wiki-knowledge-edit` | knowledge-manager | 知見カテゴリを編集 |
| `/wiki-knowledge-remove` | knowledge-manager | 知見カテゴリを論理削除 |

### 運用層（ingest → triage → absorb → archive）

| コマンド | スキル | 用途 |
|---|---|---|
| `/wiki-ingest` | （CLI 直接） | data/ → raw-entries/ |
| `/wiki-triage` | [triage.md](triage.md) | raw-entries/ をシャードに振り分け |
| `/wiki-absorb` | curator 系 | shards/ にエントリを吸収 |
| `/wiki-archive` | [archive.md](archive.md) | 完工案件を archive/ に移動 |

### 補助層（query / status / cleanup / rebuild）

| コマンド | スキル | 用途 |
|---|---|---|
| `/wiki-query` | （curator 系） | wiki 横断質問応答 |
| `/wiki-status` | （CLI 直接） | シャード横断メトリクス |
| `/wiki-rebuild-resolver` | （CLI 直接） | エイリアスリゾルバ再構築 |
| `/wiki-index-rebuild` | （CLI 直接） | 日本語ナビゲーション用 _index.md ツリー再生成 |
| `/wiki-verify-links` | （CLI 直接） | wikilink の整合性検証（broken / stale link 検出） |
| `/wiki-cleanup` | curator 系 | 既存記事の品質改善 |

---

## クイックスタート

```text
1. /wiki-status                              # 現状確認
2. /wiki-project-add ○○マンション             # 案件登録
3. /wiki-client-add 株式会社□□              # 得意先登録
4. /wiki-ingest data/sample.mbox             # メール取り込み
5. /wiki-triage                              # 振り分け
6. /wiki-absorb projects                     # 案件 wiki に吸収
7. /wiki-status                              # 結果確認
```

---

## 簡易操作（このスキルから直接実行可能）

ナビゲーターとして、以下の簡易操作を提供します：

### 状態確認

```bash
python -m interfaces.status_cli --plugin-root <plugin_root>
```

JSON が返るので metrics セクションをユーザーに整形して報告してください。

### 案件一覧

```bash
python -m interfaces.resolver_cli list --plugin-root <plugin_root> --shard projects
```

### 全レコード（archived 含む）

```bash
python -m interfaces.resolver_cli list --plugin-root <plugin_root> --include-archived
```

---

## エラー時の振る舞い

- CLI が exit 1 を返した場合、JSON の `status` / `error` / `details` を読みユーザーに伝える
- マスタデータ未登録で triage が機能しない場合、manager コマンドの実行を提案する
- triage で unclassified が多い場合、resolver の aliases を追加することを提案する
- absorb は LLM の判断が本質なので、wiki スキル（[../../../../.claude/skills/wiki/SKILL.md](../../../../.claude/skills/wiki/SKILL.md)）の "writer, not filing clerk" 原則に従う

---

## CLI 出力スキーマ

詳細は [CLI_OUTPUT_SCHEMAS.md](../../scripts/interfaces/CLI_OUTPUT_SCHEMAS.md) を参照。

すべての CLI は JSON-only 出力。エラー時は `{"status":"error","error":"<msg>","details":{...}}` で exit 1。

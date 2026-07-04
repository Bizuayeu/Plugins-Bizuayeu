---
name: jooto-absorb
description: Jooto タスク状態を project shard の ## Jooto セクションに編み込む方針スキル。writer, not filing clerk を「案件追い」文脈に適用する。
---

# jooto-absorb

JootoGrabber 出力（`data/jooto/{id}_{slug}/`）を MeguruWiki project shard に吸収する方針スキル。
`/wiki-jooto-absorb` 実行時に Claude が直接読んで実行します。

---

## 継承する原則

`[SKILL.md](SKILL.md)`（BusinessCurator wiki スキル本体）の **writer, not filing clerk** 原則を継承：

タスクを丸ごと転記するのではなく、「**いま何を追うべきか**」を抽出して記事化する。

---

## 入出力

**入力**: `JootoGrabber/data/jooto/{id}_{slug}/`
- `board.json` — board メタ情報（`id`, `title`, `archived`, `updated_at`）
- `tasks.json` — タスク配列。主要フィールド:
  - `id`, `task_number`（表示用番号）, `name`（タスク名。`title` ではない）
  - `status`: `to_do` / `in_progress` / `done`
  - `list_id` — 列への所属
  - `deadline_date_time` — 期限（多くは `null`）
  - `assigned_user_ids` — 担当者 user id の配列（名前は別途 `/v1/users` で解決）
  - `categories` — タスクに付いたラベル配列
  - `updated_at` — 完了日付の近似として利用
- `lists.json` — 列（Jooto 上のカンバン列）。`id`, `name`（列名。`title` ではない）, `order`, `auto_task_status`
- `categories.json` — ボードに定義されたラベル

**出力**: 運用 wiki インスタンスの `shards/projects/{Slug}/_project.md`
- frontmatter の `jooto` フィールド追加/更新
- 本文末尾付近の `## Jooto` セクション **全置換**（冪等）

仕様詳細: 運用 wiki インスタンス側の `docs/JOOTO_SCHEMA.md` で管理（本プラグインには同梱しない。Jooto API のフィールド仕様は上記「入力」節が要約）

---

## 実行手順

### 1. Board → ターゲット shard マッピング

対象 board を以下3クラスに分類し、それぞれ配置先を決める:

| クラス | 判定 | 配置先 |
|---|---|---|
| **project** | board 名が地名/案件名（例: `FY26_18 東長崎4丁目`, `66_多摩川1丁目プロジェクト`） | `shards/projects/{Slug}/_project.md` |
| **team** | 部署・個人・テンプレート（例: `バックオフィス`, `１課`, `牛山への依頼`, `設計PM`, `工事への申し送り`, `設計PMテンプレート`） | `shards/teams/{Slug}.md`（なければ新規作成） |
| **ambiguous** | project とも team とも判定不能、または project slug と一致しない | `inbox/unclassified/jooto-{board_id}.md` |

project クラスの slug 決定優先度:

1. **`_alias_resolver.md` 突合** — `board.title` が既存 project の alias/title と一致
2. **タイトル正規化マッチ** — `FY26_18 東長崎4丁目` → `HigashiNagasaki4Chome` 等、空白/全半角/記号を正規化して類似度判定
3. **確信度が低ければ ambiguous に落とす**（勝手に新規 project を起こさない）

### 2. 既存 frontmatter の更新

```yaml
jooto:
  board_id: "1287379"
  board_name: "FY26_18 東長崎4丁目"
  last_synced: 2026-04-14T10:00:00+09:00
```

- 既存 `jooto:` があれば `last_synced` のみ更新
- `status`, `title`, 既存フィールドは触らない

### 3. `## Jooto` セクション再生成

既存 `## Jooto ... (次の ## まで)` を全削除し、以下テンプレで置換:

```markdown
## Jooto

_最終同期: YYYY-MM-DD_  _board: [{board.title}](https://app.jooto.com/boards/{board_id})_

### 進行中 (N)

**{list.name}** (M件)
- **#{task.task_number} {task.name}** — 期限: {date or 未定} / [jooto#{task.id}]({url})

### 未着手 (N)

**{list.name}** (M件)
- **#{task.task_number} {task.name}** — 期限: {date or 未定} / [jooto#{task.id}]({url})
- …他 X 件

### 完了 (直近5件)

- ~~#{task_number} {task.name}~~ — 完了: YYYY-MM-DD / [jooto#{id}]({url})
```

**ルール**:
- タスクの分類は `task.status`（`to_do` / `in_progress` / `done`）を使う。`lists.json` の列名では分類しない（列 = 工程段階の意味で使われており、status とは独立）
- **進行中・未着手** は `list_id` → `list.name` で**列ごとにカテゴライズ**。列の表示順は `list.order` 昇順
- **各列内の並び順は `tasks.json` の API レスポンス順を保持**（Jooto 画面の列内並びと一致）
- **進行中**: 全件表示。**未着手**: 列ごとに上位3件 + `- …他 N 件`
- 完了: `updated_at` 降順で最大5件
- 期限切れ（`today > deadline_date_time` かつ `status != done`）は行頭に `⚠️`
- タスクが0件のセクション/列は省略
- タスク URL: `https://app.jooto.com/boards/{board_id}/tasks/{task_id}`
- 担当者名の解決は MVP ではスコープ外（assigned_user_ids を `/v1/users` で突合する拡張は別途）

### 4. 冪等性の担保

- 書き換え前に git diff を想定し、タスク状態に変化がなければ `last_synced` 更新のみで済ませる
- frontmatter と本文は YAML/Markdown として壊さない（壊す前に必ず dry-run で検証）

---

## 案件追いとしての判断

以下は「書く vs 書かない」の判断基準:

**書く**:
- 進行中タスクで関係者にボールがある
- 期限を過ぎたタスク（⚠️）
- 直近完了した重要タスク（フェーズ切り替えに関わるもの）

**書かない**:
- チェックリストの細部（tasks.json には含まれるが、記事側では省略）
- タスクコメントの本文（別途 `/v1/tasks/{id}/comments` で取得可能だが、MVP ではスコープ外）
- 完了後1ヶ月以上経過した過去タスク

---

## 反パターン

- ❌ tasks.json を丸ごと Markdown 化して貼る（シグナルが死ぬ）
- ❌ board.title をそのまま shard slug にする（既存 slug と不整合）
- ❌ 既存の `## Jooto` に append する（冪等性崩壊）
- ❌ マッチングが曖昧な board を勝手に新規 project に起こす（人間判断が必要）

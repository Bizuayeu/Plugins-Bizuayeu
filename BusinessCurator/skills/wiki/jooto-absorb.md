---
name: jooto-absorb
description: Jooto タスク状態を project shard の ## Jooto セクションに編み込む方針スキル。writer, not filing clerk を「案件追い」文脈に適用する。
---

# jooto-absorb

JootoGrabber 出力（`data/jooto/{id}_{slug}/`）を MeguruWiki project shard に吸収する方針スキル。
`/wiki-jooto-absorb` 実行時に Claude が直接読んで実行します。

---

## 継承する原則

`[../../../../.claude/skills/wiki/SKILL.md](../../../../.claude/skills/wiki/SKILL.md)` の **writer, not filing clerk** 原則を継承：

タスクを丸ごと転記するのではなく、「**いま何を追うべきか**」を抽出して記事化する。

---

## 入出力

**入力**: `JootoGrabber/data/jooto/{id}_{slug}/`
- `board.json` — board メタ情報（id, title, archived, updated_at）
- `tasks.json` — 配列。各要素に title, status, assignees, due_date, updated_at 等
- `lists.json` — 列（ToDo / 進行中 / 完了 等）
- `categories.json` — ラベル

**出力**: `MeguruWiki/shards/projects/{Slug}/_project.md`
- frontmatter の `jooto` フィールド追加/更新
- 本文末尾付近の `## Jooto` セクション **全置換**（冪等）

仕様詳細: [JOOTO_SCHEMA.md](../../../../MeguruWiki/docs/JOOTO_SCHEMA.md)

---

## 実行手順

### 1. Board → Project マッピング

対象 board ごとに、対応する MeguruWiki project slug を決定する。優先度:

1. **`_alias_resolver.md` 突合** — board.title が既存 project の alias/title と一致
2. **タイトル正規化マッチ** — `FY26_18 東長崎4丁目` → `HigashiNagasaki4Chome` 等、空白/全半角/記号を正規化して類似度判定
3. **LLM 推論** — 一致しない場合、board 内のタスク内容から推測

いずれも確信度が低い場合は **`inbox/unclassified/jooto-{board_id}.md`** に退避し、人間レビューへ。

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

_最終同期: YYYY-MM-DD HH:MM_

### 進行中 (In Progress)

- **{task.title}** — 担当: {assignee} / 期限: {due or 未定} / [jooto#{task.id}]({url})
  - {短い補足があれば1行}

### 未着手 (To Do)

- ...

### 完了 (Done) — 直近5件

- ~~{title}~~ — {completed_at 日付} / [jooto#{id}]({url})
```

**ルール**:
- lists.json の列名を参照し、「進行中 / To Do / Done」に正規化
- 期限切れ（today > due、かつ Done でない）は先頭に `⚠️`
- Done は updated_at 降順で最大5件
- タスクが0件のセクションは省略
- assignee が未設定なら「担当: 未定」
- URL は `https://app.jooto.com/boards/{board_id}/tasks/{task_id}` で構築

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

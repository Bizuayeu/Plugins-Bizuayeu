---
name: knowledge-manager
description: 知見カテゴリ CRUD（add-domain/edit/remove）。法規・工法・資材等のカテゴリを対話で定義し、resolver_cli に渡して shards/knowledge/{Category}/ ディレクトリを準備する。
---

# knowledge-manager

知見シャードのカテゴリ管理スキルです。
案件に依存しない汎用的知見を分類するためのカテゴリを整備します。

## 責務

- 新規カテゴリの定義（add-domain: 知識領域の追加）
- カテゴリ名やキーワードの編集
- 不要カテゴリの論理削除

## 対話パターン

AskUserQuestion で：

1. **カテゴリ名**: 「法規」「工法」「資材」「契約」等
2. **slug**: `houki`, `kouhou` 等の ASCII
3. **カバー範囲**: 短い説明（1-2文）
4. **キーワード**: 関連用語（aliases として triage で使う）

## CLI 呼び出し

`interfaces.resolver_cli`:

### add (= add-domain)

```bash
python -m interfaces.resolver_cli add \
  --plugin-root <plugin_root> \
  --kind knowledge \
  --slug <Slug> \
  --canonical "<カテゴリ名>" \
  --target-path "shards/knowledge/<Slug>/_index.md" \
  --aliases "<keyword1>,<keyword2>"
```

### edit

```bash
python -m interfaces.resolver_cli edit \
  --plugin-root <plugin_root> \
  --id knowledge/<Slug> \
  --add-aliases "<新キーワード>"
```

### remove

```bash
python -m interfaces.resolver_cli remove \
  --plugin-root <plugin_root> \
  --id knowledge/<Slug>
```

## 後処理

`shards/knowledge/<Slug>/_index.md` を作成：

```markdown
# <カテゴリ名>

- **カバー範囲**: <description>
- **キーワード**: <keyword1>, <keyword2>

## 記事一覧

(absorb で記事が増えていく)
```

## エラー対応

- duplicate → 既存カテゴリへの edit を提案
- knowledge シャードは案件と直交する分類軸なので、安易に削除せず archived フラグで残すことを推奨

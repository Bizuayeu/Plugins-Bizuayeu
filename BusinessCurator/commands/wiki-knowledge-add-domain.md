---
name: wiki-knowledge-add-domain
description: 知見カテゴリを新規定義（法規・工法・資材等）。resolver と shards/knowledge/{Slug}/_index.md を生成する。
---

# /wiki-knowledge-add-domain

知見シャードに新しいカテゴリを追加します。

## 動作

[knowledge-manager.md](../skills/wiki/knowledge-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli add \
  --plugin-root <plugin_root> \
  --kind knowledge \
  --slug <Slug> \
  --canonical "<カテゴリ名>" \
  --target-path "shards/knowledge/<Slug>/_index.md" \
  --aliases "<keyword1>,<keyword2>"
```

## 関連

- [knowledge-manager.md](../skills/wiki/knowledge-manager.md)

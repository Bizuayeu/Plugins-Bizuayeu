---
name: wiki-knowledge-edit
description: 既存知見カテゴリの編集（キーワード追加、カバー範囲変更等）。
---

# /wiki-knowledge-edit

知見カテゴリを編集します。

## 動作

[knowledge-manager.md](../skills/wiki/knowledge-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli edit \
  --plugin-root <plugin_root> \
  --id knowledge/<Slug> \
  --add-aliases "<新キーワード>"
```

## 関連

- [knowledge-manager.md](../skills/wiki/knowledge-manager.md)

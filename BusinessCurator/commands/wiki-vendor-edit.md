---
name: wiki-vendor-edit
description: 既存取引先のメタデータ更新（担当者追加、業種変更等）。
---

# /wiki-vendor-edit

取引先を編集します。

## 動作

[vendor-manager.md](../skills/wiki/vendor-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli edit \
  --plugin-root <plugin_root> \
  --id vendors/<Slug> \
  --add-aliases "<追加担当者>"
```

## 関連

- [vendor-manager.md](../skills/wiki/vendor-manager.md)

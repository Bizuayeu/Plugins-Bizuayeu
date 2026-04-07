---
name: wiki-client-edit
description: 既存得意先のメタデータ更新（aliases / target_path 等）。
---

# /wiki-client-edit

既存得意先を編集します。

## 動作

[client-manager.md](../skills/wiki/client-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli edit \
  --plugin-root <plugin_root> \
  --id clients/<Slug> \
  --add-aliases "<新キーパーソン>"
```

## 関連

- [client-manager.md](../skills/wiki/client-manager.md)

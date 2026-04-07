---
name: wiki-client-remove
description: 得意先を論理削除（archived フラグ）。取引終了時に使用。
---

# /wiki-client-remove

得意先を archived フラグで論理削除します。

## 動作

[client-manager.md](../skills/wiki/client-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli remove \
  --plugin-root <plugin_root> \
  --id clients/<Slug>
```

## 関連

- [client-manager.md](../skills/wiki/client-manager.md)

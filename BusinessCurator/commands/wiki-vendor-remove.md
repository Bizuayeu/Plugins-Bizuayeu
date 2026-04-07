---
name: wiki-vendor-remove
description: 取引先を論理削除（archived フラグ）。取引停止時に使用。
---

# /wiki-vendor-remove

取引先を archived フラグで論理削除します。

## 動作

[vendor-manager.md](../skills/wiki/vendor-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli remove \
  --plugin-root <plugin_root> \
  --id vendors/<Slug>
```

## 関連

- [vendor-manager.md](../skills/wiki/vendor-manager.md)

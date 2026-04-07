---
name: wiki-knowledge-remove
description: 知見カテゴリを論理削除（archived フラグ）。安易な削除は推奨しない。
---

# /wiki-knowledge-remove

知見カテゴリを archived フラグで論理削除します。

## 動作

[knowledge-manager.md](../skills/wiki/knowledge-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli remove \
  --plugin-root <plugin_root> \
  --id knowledge/<Slug>
```

## 注意

知見シャードは案件と直交する分類軸なので、安易に削除せず統合や名称変更を優先することを推奨。

## 関連

- [knowledge-manager.md](../skills/wiki/knowledge-manager.md)

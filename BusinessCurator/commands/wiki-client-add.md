---
name: wiki-client-add
description: 得意先を新規登録。法人名・ドメイン・キーパーソンを対話で収集し、resolver と shards/clients/{Slug}.md を生成する。
---

# /wiki-client-add

新しい得意先を登録します。

## 動作

[client-manager.md](../skills/wiki/client-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli add \
  --plugin-root <plugin_root> \
  --kind clients \
  --slug <Slug> \
  --canonical "<法人名>" \
  --target-path "shards/clients/<Slug>.md" \
  --aliases "<domain>,<略称>"
```

## 関連

- [client-manager.md](../skills/wiki/client-manager.md)

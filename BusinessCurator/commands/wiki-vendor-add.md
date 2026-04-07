---
name: wiki-vendor-add
description: 取引先を新規登録。法人名・業種・ドメイン・担当者を対話で収集し、resolver と shards/vendors/{Slug}.md を生成する。
---

# /wiki-vendor-add

取引先を登録します。

## 動作

[vendor-manager.md](../skills/wiki/vendor-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli add \
  --plugin-root <plugin_root> \
  --kind vendors \
  --slug <Slug> \
  --canonical "<法人名>" \
  --target-path "shards/vendors/<Slug>.md" \
  --aliases "<domain>,<業種>,<担当者>"
```

## 関連

- [vendor-manager.md](../skills/wiki/vendor-manager.md)

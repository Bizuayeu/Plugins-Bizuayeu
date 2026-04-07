---
name: wiki-rebuild-resolver
description: alias resolver を再構築（resolver_cli list で全レコードを取得し、必要に応じて手動編集 → resolver_cli rebuild 相当の操作）。
---

# /wiki-rebuild-resolver

エイリアスリゾルバを確認・再構築します。

## 動作

`interfaces.resolver_cli` の `list --include-archived` で全レコードを取得：

```bash
python -m interfaces.resolver_cli list \
  --plugin-root <plugin_root> \
  --include-archived
```

JSON を解析し、`_alias_resolver.md` と整合しているか確認。
不整合があれば、ユーザーに報告して manager 系コマンドでの修正を提案する。

## 使用例

```text
/wiki-rebuild-resolver
```

## 注意

resolver は manager 系コマンドの実行時に自動更新されるので、通常はこのコマンドは不要です。
ファイル直接編集や外部要因で不整合が生じたときの最終手段として使います。

## 関連

- `/wiki-project-add`, `/wiki-client-add`, etc.: 通常の更新経路
- [SKILL.md](../skills/wiki/SKILL.md)

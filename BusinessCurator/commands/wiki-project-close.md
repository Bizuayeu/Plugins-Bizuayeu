---
name: wiki-project-close
description: 案件を完了マーク（archived フラグ）。実ファイル移動は /wiki-archive で行う。
---

# /wiki-project-close

案件を resolver 上で論理削除（archived = True）します。実ファイル移動は伴いません。

## 動作

[project-manager.md](../skills/wiki/project-manager.md) スキルに委譲。

```bash
python -m interfaces.resolver_cli remove \
  --plugin-root <plugin_root> \
  --id projects/<Slug>
```

## 使用例

```text
/wiki-project-close MaruMaru
```

## 注意

このコマンドは resolver の archived フラグのみを立てます。
実際のファイル移動と知見抽出は `/wiki-archive` で行います。

## 関連

- [project-manager.md](../skills/wiki/project-manager.md)
- `/wiki-archive`: ファイル移動 + 知見抽出を伴うアーカイブ

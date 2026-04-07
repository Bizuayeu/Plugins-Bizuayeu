---
name: wiki-project-edit
description: 既存案件のメタデータ更新（canonical / aliases / target_path）。
---

# /wiki-project-edit

既存案件のメタデータを編集します。

## 動作

[project-manager.md](../skills/wiki/project-manager.md) スキルに委譲。スキルが対話で変更内容を収集し、`interfaces.resolver_cli` に渡します：

```bash
python -m interfaces.resolver_cli edit \
  --plugin-root <plugin_root> \
  --id projects/<Slug> \
  --canonical "<新名称>" \
  --add-aliases "<追加alias>" \
  --remove-aliases "<削除alias>"
```

## 使用例

```text
/wiki-project-edit MaruMaru
```

## 関連

- [project-manager.md](../skills/wiki/project-manager.md)
- `/wiki-project-add`
- `/wiki-project-close`

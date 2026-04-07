---
name: wiki-project-add
description: 案件を新規登録。物件名・現場番号・エイリアスを対話で収集し、resolver と shards/projects/{Slug}/_project.md を生成する。
---

# /wiki-project-add

新しい案件を BusinessCurator に登録します。

## 動作

このコマンドは [project-manager.md](../skills/wiki/project-manager.md) スキルに委譲します。

スキルは AskUserQuestion でマスタデータ（案件名、slug、エイリアス、得意先紐付け）を収集し、最終的に以下を実行：

```bash
python -m interfaces.resolver_cli add \
  --plugin-root <plugin_root> \
  --kind projects \
  --slug <Slug> \
  --canonical "<案件名>" \
  --target-path "shards/projects/<Slug>/_project.md" \
  --aliases "<alias1>,<alias2>"
```

## 使用例

```text
/wiki-project-add
```

→ 対話開始 → resolver 更新 → `shards/projects/<Slug>/_project.md` テンプレート生成

## 関連

- [project-manager.md](../skills/wiki/project-manager.md): 詳細な対話パターンとテンプレート
- `/wiki-project-edit`: 既存案件の編集
- `/wiki-project-close`: 完了マーク

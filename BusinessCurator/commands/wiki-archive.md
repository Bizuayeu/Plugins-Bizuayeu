---
name: wiki-archive
description: 完工案件を shards/projects から archive/projects に移動する。完工確認 → 知見抽出候補提示 → archive_cli execute の対話フロー。
---

# /wiki-archive

完工した案件をアーカイブします。

## 動作

[archive.md](../skills/wiki/archive.md) スキルに委譲。

スキルは以下の対話フローを実行：

1. **完工確認**: AskUserQuestion で日付・状態・理由を収集
2. **知見抽出候補の提示**: 案件記事から汎用化可能な知見を提案
3. **knowledge / vendor / client wiki への追記**: 該当 curator スキルに従う
4. **アーカイブ実行**:

```bash
python -m interfaces.archive_cli execute \
  --plugin-root <plugin_root> \
  --project <slug> \
  --reason "<reason>"
```

事前確認のみ行いたい場合（実行しない）:

```bash
python -m interfaces.archive_cli plan \
  --plugin-root <plugin_root> \
  --project <slug>
```

## 使用例

```text
/wiki-archive MaruMaru
```

→ 対話 → 知見抽出 → ファイル移動 → 報告

## 関連

- [archive.md](../skills/wiki/archive.md): 対話フロー詳細
- `/wiki-project-close`: archived フラグだけ立てる軽量版

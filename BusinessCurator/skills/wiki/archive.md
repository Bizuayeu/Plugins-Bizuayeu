---
name: archive
description: 案件アーカイブ運用スキル。完工確認 → 知見抽出候補提示 → archive_cli execute の対話フローで案件を shards/projects から archive/projects に移動する。
---

# archive

完工した案件を `shards/projects/` から `archive/projects/` に移動する運用スキルです。

**手動発動が原則**。「完工」の判断は業務判断であり、自動化すべきではありません。
ただし**知見抽出は半自動化**します（完工時の暗黙知の消失防止）。

## 対話フロー

### Step 1: 完工確認

ユーザーから対象案件 slug を受け取り、AskUserQuestion で確認：

```text
案件 [○○マンション新築工事] をアーカイブします。
- 完工日: <ユーザー入力>
- 状態: <completed | suspended | cancelled>
- アーカイブ理由: <自由記入>

よろしいですか？
```

### Step 2: 知見抽出候補の提示

`shards/projects/<slug>/_project.md` および同ディレクトリの記事を読み、汎用化可能な知見を提案：

```text
以下の知見を抽出候補とします：

1. 「排煙告示の解釈」 → knowledge/法規/
2. 「△△設備工業の対応評価」 → vendors/SankakuSetsubi（既存記事更新）
3. 「□□不動産との価格交渉パターン」 → clients/Shikaku（既存記事更新）

抽出する候補を選んでください（複数選択可）
```

ユーザーが選択したら、curator スキル（[knowledge-curator.md](knowledge-curator.md) / [vendor-curator.md](vendor-curator.md) / [client-curator.md](client-curator.md)）に従って該当 wiki に追記。

### Step 3: アーカイブ実行

知見抽出が完了したら、`interfaces.archive_cli` を実行：

#### plan（事前確認）

```bash
python -m interfaces.archive_cli plan \
  --plugin-root <plugin_root> \
  --project <slug> \
  --reason "<reason>"
```

manifest を表示してユーザーに最終確認。

#### execute（実行）

```bash
python -m interfaces.archive_cli execute \
  --plugin-root <plugin_root> \
  --project <slug> \
  --reason "<reason>"
```

これにより：
1. resolver で archived = True にマーク
2. target_path を `shards/projects/<slug>/_project.md` → `archive/projects/<slug>/_project.md` に更新
3. ファイルシステム上で `shards/projects/<slug>/` → `archive/projects/<slug>/` に移動

### Step 4: 結果報告

JSON 出力を解析してユーザーに報告：

```json
{
  "status": "ok",
  "action": "execute",
  "manifest": {
    "project_slug": "MaruMaru",
    "project_canonical": "○○マンション新築工事",
    "archived_at": "2026-04-07T15:00:00+09:00",
    "reason": "completed",
    "source_path": "shards/projects/MaruMaru",
    "destination_path": "archive/projects/MaruMaru",
    "extracted_knowledge": []
  },
  "moved": true
}
```

## エラー対応

- not found → list で既存案件を表示
- already archived → 既にアーカイブ済みである旨を伝え、誤操作を確認
- 移動先既存 / 移動元不存在 → ファイルシステム状態を確認、必要なら `--no-move` で resolver のみ更新

## 注意事項

- アーカイブ後も得意先 / 取引先 / 知見記事からの wikilink は有効（resolver に archived=True で残るため）
- アーカイブを取り消したい場合は resolver_cli edit で archived フラグを操作 + 手動でファイル戻し

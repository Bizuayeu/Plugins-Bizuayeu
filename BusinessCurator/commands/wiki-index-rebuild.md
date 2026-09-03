---
name: wiki-index-rebuild
description: 日本語ナビゲーション用の _index.md ツリー（ルート + 4シャード）を再生成する。
---

# /wiki-index-rebuild

BusinessWiki の `_index.md` ツリーを resolver の最新状態から再生成します。

## 動作

`interfaces.index_cli` を直接呼び出します（純機械処理）：

```bash
python -m interfaces.index_cli rebuild --plugin-root <plugin_root>
```

以下のファイルが上書き生成されます：

- `{plugin_root}/_index.md` — ルート入口（4シャードへのリンク + 件数サマリ）
- `{plugin_root}/shards/projects/_index.md`
- `{plugin_root}/shards/vendors/_index.md`
- `{plugin_root}/shards/clients/_index.md`
- `{plugin_root}/shards/knowledge/_index.md`

各シャードの `_index.md` は EpisodicWiki と同じ形式（`- [日本語名](相対パス) — also: alias1, alias2`）で、Firefox 等の Markdown ビューでそのまま日本語ナビゲーションが動作します。

## 自動トリガー

通常は `resolver_cli add / edit / remove` の実行後に自動的に再生成されるため、手動呼び出しは以下の場合に限定されます：

- 一括登録後の最終整備
- `_alias_resolver.md` を直接編集した後の再同期
- 初期導入時（`--skip-index-rebuild` を付けてまとめて追加した後）

## オプション

### `--shard <kind>`
指定したシャードのみを再生成（ルートは更新しない）。

```bash
python -m interfaces.index_cli rebuild --plugin-root <path> --shard projects
```

### `--include-archived`
archived フラグ付きのレコードも `_index.md` に含める。

```bash
python -m interfaces.index_cli rebuild --plugin-root <path> --include-archived
```

## JSON 出力

全シャード再生成：

```json
{
  "status": "ok",
  "action": "rebuild_all",
  "counts": {
    "projects": 36,
    "vendors": 41,
    "clients": 20,
    "knowledge": 4
  }
}
```

単一シャード再生成：

```json
{
  "status": "ok",
  "action": "rebuild_shard",
  "shard": "projects",
  "count": 36
}
```

## ユーザーへの報告

```text
=== _index.md 再生成完了 ===
projects:    36
vendors:     41
clients:     20
knowledge:    4
```

## 関連

- `_alias_resolver.md` — resolver 内部管理用（手動編集可、triage マッチ情報）
- `_index.md` — 人間閲覧用（自動生成、手動編集禁止）
- `/wiki-status` — メトリクス集計

---
name: project-curator
description: 案件 wiki キュレーション方針。raw-entries をエピソード型ナラティブとして案件記事に編み込む。writer, not filing clerk 原則を案件文脈に適用。
---

# project-curator

案件シャード（`shards/projects/{Name}/`）のキュレーション方針スキルです。

このスキルは LLM の判断が本質なので、Python 化されません。`/wiki-absorb projects` 実行時に Claude が直接読んで実行します。

---

## 継承する原則

`[SKILL.md](SKILL.md)` の **writer, not filing clerk** 原則を継承します：

- 事実をどこに置くかではなく、それが何を意味するかを問う
- 既存記事に append するのではなく、新たな次元を見出して統合する
- 事象（diary-driven）ではなく、テーマ（narrative-driven）で記事を構造化する

## 案件固有の方針

### 1. 時系列ではなくフェーズで構造化

NG（diary-driven）:
```
## 2026-04-07 排煙設備の相談
## 2026-04-08 図面修正
## 2026-04-10 確認申請
```

OK（narrative）:
```
## 経緯
## 設計決定（排煙計画）
## 施工準備
## 完成後の保守要件
```

### 2. 判断と理由を必ず記録

メールには「やる/やらない」だけでなく**なぜ**が含まれる。これを抽出するのが project-curator の核心。

例：
- 「排煙告示の解釈で◯◯に決めた」→ **設計決定** 節へ
- 「□□社が納期遅延だが既存関係を優先」→ **判断ログ** 節へ

### 3. クロスシャード参照

判断や評価に関わる固有名は wikilink で繋ぐ：
- `[[clients/ShikakuFudosan]]` ← 得意先側の判断履歴
- `[[vendors/SankakuSetsubi]]` ← 取引先側の実績
- `[[knowledge/法規/排煙告示]]` ← 抽象化された知見

### 4. 完工までの「圧」を逃さない

メールに現れるイライラ・焦り・折衝の重みは記録すべき情報。フラットなまとめで漂白しない。

## absorb の流れ

1. raw-entries/ から triage で `projects/<slug>` 主シャードのエントリを取得
2. `_alias_resolver.md` で対象案件を確認
3. 既存の `shards/projects/<slug>/_project.md` と既存トピック記事を読む
4. **読解 → 統合 → 更新**:
   - 新しい次元（決定・判断・問題・解決）が含まれるか？
   - 既存節を更新するか、新節を起こすか
   - 50行を超えそうなら新トピック記事に分離
5. wikilink の追加・修正
6. checkpoint: 15 エントリ毎に `_index.md` 再生成

## 反パターン（避ける）

- ❌ 全エントリを `## YYYY-MM-DD` で時系列にダンプする
- ❌ 既存の長大記事に append し続ける
- ❌ 判断の理由を省略して結論だけ書く
- ❌ クロスシャードのリンクを忘れる

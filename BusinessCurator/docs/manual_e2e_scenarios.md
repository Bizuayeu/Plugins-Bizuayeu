# Manual E2E Scenarios

自動テストでは検証しきれない md スキル経由の対話フローを、手動で再現するためのシナリオ集です。
4/16 Curator Family 発表のデモシナリオもここに集約します。

---

## 前提

- BusinessCurator プラグインがインストール済み（または `cd plugins-bizuayeu/BusinessCurator/`）
- `data/` に合成サンプルメール（個人情報を含めない）を配置
- `python -m interfaces.*` が PYTHONPATH=scripts で実行可能

---

## シナリオ 1: 案件登録から absorb まで通し

**目的**: 1案件分のフルライフサイクル（登録 → ingest → triage → absorb → status）。

```bash
# 0. 初期状態確認
python -m interfaces.status_cli --plugin-root .
# → metrics 全 0

# 1. マスタ登録（manager 系コマンド）
python -m interfaces.resolver_cli add --plugin-root . \
  --kind projects --slug MaruMaru \
  --canonical "MaruMaruMansion" \
  --target-path "shards/projects/MaruMaru/_project.md" \
  --aliases "MM,2026-003"

python -m interfaces.resolver_cli add --plugin-root . \
  --kind clients --slug Shikaku \
  --canonical "ShikakuFudosan" \
  --target-path "shards/clients/Shikaku.md" \
  --aliases "shikaku.example.jp"

python -m interfaces.resolver_cli add --plugin-root . \
  --kind vendors --slug Sankaku \
  --canonical "SankakuSetsubi" \
  --target-path "shards/vendors/Sankaku.md" \
  --aliases "sankaku.example.jp"

# 2. ingest
python -m interfaces.ingest_cli --plugin-root . \
  --source data/sample_meguru.mbox

# 3. triage（オフライン: --no-llm）
python -m interfaces.triage_cli --plugin-root . --no-llm

# 4. status で確認
python -m interfaces.status_cli --plugin-root .
# → raw_entries_count > 0, alias_records_active = 3

# 5. absorb は md スキル経由（claude code 内で /wiki-absorb projects）
#    LLM 判断が本質なので Python CLI なし
```

**期待結果**:
- ルールマッチが大半（subject に MaruMaruMansion を含むメール）
- unclassified が少数残れば alias 追加で再 triage
- absorb 後 `shards/projects/MaruMaru/_project.md` に curator 方針に沿った内容が蓄積

---

## シナリオ 2: 完工アーカイブの対話フロー

**目的**: archive スキルの対話フローと知見抽出を検証。

```bash
# 1. 事前: シナリオ1完了状態

# 2. archive plan（副作用なし、manifest 確認）
python -m interfaces.archive_cli plan --plugin-root . \
  --project MaruMaru --reason "完工"

# 3. md スキル経由 (/wiki-archive MaruMaru)
#    - 完工確認の AskUserQuestion
#    - shards/projects/MaruMaru/ 内の記事を読み、知見抽出候補を提示
#    - ユーザーが選択 → curator スキル経由で knowledge / vendor / client wiki に追記
#    - その後 archive_cli execute を起動

# 4. 直接 execute する場合
python -m interfaces.archive_cli execute --plugin-root . \
  --project MaruMaru --reason "完工"

# 5. 結果確認
python -m interfaces.status_cli --plugin-root .
# → alias_records_archived = 1
ls archive/projects/MaruMaru/
# → _project.md, topic-*.md が移動済み
```

**期待結果**:
- `shards/projects/MaruMaru/` が消えている
- `archive/projects/MaruMaru/` に全ファイル移動
- resolver の archived フラグが立つ
- target_path が `archive/projects/MaruMaru/_project.md` に更新

---

## シナリオ 3: triage ルール改善ループ

**目的**: unclassified エントリを発見して alias を追加し、再 triage で rule_match に変える。

```bash
# 1. 初回 triage
python -m interfaces.triage_cli --plugin-root . --no-llm
# → unclassified = N (>0)

# 2. inbox/unclassified/ の内容を確認
ls inbox/unclassified/

# 3. md スキル経由 (/wiki-triage)
#    - スキルが unclassified エントリを表示
#    - 各エントリについて AskUserQuestion でシャード選択
#    - resolver_cli edit で alias 追加

# 4. 手動で alias 追加例
python -m interfaces.resolver_cli edit --plugin-root . \
  --id projects/MaruMaru \
  --add-aliases "新しいキーワード"

# 5. 再 triage
python -m interfaces.triage_cli --plugin-root . --no-llm
# → unclassified が減っていることを確認
```

---

## シナリオ 4: LLM フォールバック動作確認 (Claude Code 必須)

**目的**: ClaudeCliTriageClient (subprocess `claude -p`) の実 LLM 呼び出しを検証。
**前提**: `claude` CLI が PATH 上にある + サブスクリプションが有効。

```bash
# 1. 既知のキーワードに含まれない subject のエントリだけを準備

# 2. デフォルト triage (LLM フォールバック有効)
python -m interfaces.triage_cli --plugin-root .

# 3. 結果確認
# → llm_fallback > 0
# → triage_logs/ に llm_invoked: true のエントリ
```

**注意**:
- `claude -p` は API キー設定不要（サブスクリプション認証）
- CI ではこのシナリオは実行しない（unit test では mock 化）

---

## 4/16 Curator Family 発表用デモシナリオ

**目的**: 5分以内で Clean Architecture × TDD × md/python 二層分離の価値を伝える。

### Demo Track

1. **状態 0 表示** (`status_cli`) → JSON で全 0
2. **manager 1ファイルだけ実行** → resolver と md が同時更新されることを示す
3. **ingest** → JSON サマリ表示
4. **triage --no-llm** → ルールベースで決着する数を実演（LLM 呼ばずとも 8 割）
5. **status 再実行** → before/after で metrics の変化
6. **archive plan + execute** → ファイル移動を実演

### Talking Points

- 「md で済むものを Python 化しない」原則：absorb / cleanup は CLI なし
- 「事前認識合わせが全てを決める」原則：マスタ登録 → triage → curator は必然の順序
- 全 600+ tests / mypy strict / ruff 0警告 / カバレッジ 90%+

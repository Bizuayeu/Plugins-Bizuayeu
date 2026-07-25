#!/usr/bin/env python3
"""
md構造テスト
============

skills/wiki/ と commands/ の md ファイルが満たすべき構造制約を検証。

検証内容:
1. すべての必須スキル/コマンドファイルが存在する
2. 各 md は YAML frontmatter を持ち、name と description が定義されている
3. command の name は wiki-* 形式
4. skill の name は kebab-case
5. command の本文は対応する CLI / skill 参照を含む
6. skill の本文は対応する CLI / Python script 参照を含む（操作系のみ）
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

import pytest

# =============================================================================
# Constants
# =============================================================================

REPO_ROOT = Path(
    __file__
).parent.parent.parent.parent  # scripts/test/skill_structure_tests/ → BusinessCurator/
SKILLS_DIR = REPO_ROOT / "skills" / "wiki"
COMMANDS_DIR = REPO_ROOT / "commands"

REQUIRED_SKILLS: List[str] = [
    "SKILL.md",
    "triage.md",
    "archive.md",
    "jooto-absorb.md",
    "project-manager.md",
    "client-manager.md",
    "vendor-manager.md",
    "knowledge-manager.md",
    "project-curator.md",
    "client-curator.md",
    "vendor-curator.md",
    "knowledge-curator.md",
]

REQUIRED_COMMANDS: List[str] = [
    "wiki-project-add.md",
    "wiki-project-edit.md",
    "wiki-project-close.md",
    "wiki-client-add.md",
    "wiki-client-edit.md",
    "wiki-client-remove.md",
    "wiki-vendor-add.md",
    "wiki-vendor-edit.md",
    "wiki-vendor-remove.md",
    "wiki-knowledge-add-domain.md",
    "wiki-knowledge-edit.md",
    "wiki-knowledge-remove.md",
    "wiki-ingest.md",
    "wiki-triage.md",
    "wiki-absorb.md",
    "wiki-jooto-absorb.md",
    "wiki-query.md",
    "wiki-status.md",
    "wiki-rebuild-resolver.md",
    "wiki-archive.md",
    "wiki-cleanup.md",
    "wiki-index-rebuild.md",
    "wiki-verify-links.md",
]

# CLI が呼ばれる command → CLI モジュール名 のマップ
COMMAND_TO_CLI: Dict[str, str] = {
    "wiki-ingest.md": "interfaces.ingest_cli",
    "wiki-triage.md": "interfaces.triage_cli",
    "wiki-status.md": "interfaces.status_cli",
    "wiki-archive.md": "interfaces.archive_cli",
    "wiki-index-rebuild.md": "interfaces.index_cli",
    "wiki-verify-links.md": "interfaces.quality_cli",
    "wiki-project-add.md": "interfaces.resolver_cli",
    "wiki-project-edit.md": "interfaces.resolver_cli",
    "wiki-project-close.md": "interfaces.resolver_cli",
    "wiki-client-add.md": "interfaces.resolver_cli",
    "wiki-client-edit.md": "interfaces.resolver_cli",
    "wiki-client-remove.md": "interfaces.resolver_cli",
    "wiki-vendor-add.md": "interfaces.resolver_cli",
    "wiki-vendor-edit.md": "interfaces.resolver_cli",
    "wiki-vendor-remove.md": "interfaces.resolver_cli",
    "wiki-knowledge-add-domain.md": "interfaces.resolver_cli",
    "wiki-knowledge-edit.md": "interfaces.resolver_cli",
    "wiki-knowledge-remove.md": "interfaces.resolver_cli",
}

# command → 参照すべき skill ファイル
COMMAND_TO_SKILL: Dict[str, str] = {
    "wiki-project-add.md": "project-manager.md",
    "wiki-project-edit.md": "project-manager.md",
    "wiki-project-close.md": "project-manager.md",
    "wiki-client-add.md": "client-manager.md",
    "wiki-client-edit.md": "client-manager.md",
    "wiki-client-remove.md": "client-manager.md",
    "wiki-vendor-add.md": "vendor-manager.md",
    "wiki-vendor-edit.md": "vendor-manager.md",
    "wiki-vendor-remove.md": "vendor-manager.md",
    "wiki-knowledge-add-domain.md": "knowledge-manager.md",
    "wiki-knowledge-edit.md": "knowledge-manager.md",
    "wiki-knowledge-remove.md": "knowledge-manager.md",
    "wiki-triage.md": "triage.md",
    "wiki-archive.md": "archive.md",
    "wiki-absorb.md": "project-curator.md",  # absorb はシャード別に curator を呼ぶ
}

# 操作系 skill → 参照すべき CLI モジュール
SKILL_TO_CLI: Dict[str, str] = {
    "triage.md": "interfaces.triage_cli",
    "archive.md": "interfaces.archive_cli",
    "project-manager.md": "interfaces.resolver_cli",
    "client-manager.md": "interfaces.resolver_cli",
    "vendor-manager.md": "interfaces.resolver_cli",
    "knowledge-manager.md": "interfaces.resolver_cli",
}


# =============================================================================
# Helpers
# =============================================================================


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _parse_frontmatter(content: str) -> Optional[Dict[str, str]]:
    """簡易 YAML frontmatter パーサ（key: value のみ対応）"""
    m = _FRONTMATTER_RE.match(content)
    if not m:
        return None
    fm: Dict[str, str] = {}
    for line in m.group(1).split("\n"):
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def _read_md(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


# =============================================================================
# 存在確認
# =============================================================================


class TestRequiredFiles:
    @pytest.mark.unit
    @pytest.mark.parametrize("filename", REQUIRED_SKILLS)
    def test_skill_exists(self, filename: str) -> None:
        path = SKILLS_DIR / filename
        assert path.exists(), f"missing skill file: {path}"

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", REQUIRED_COMMANDS)
    def test_command_exists(self, filename: str) -> None:
        path = COMMANDS_DIR / filename
        assert path.exists(), f"missing command file: {path}"

    @pytest.mark.unit
    def test_no_extra_skill_files(self) -> None:
        """skills/wiki/ に予期しない .md がない（_*.md 等のサポートファイルは除外）"""
        if not SKILLS_DIR.exists():
            pytest.skip(f"{SKILLS_DIR} does not exist yet")
        actual = sorted(p.name for p in SKILLS_DIR.glob("*.md") if not p.name.startswith("_"))
        expected = sorted(REQUIRED_SKILLS)
        assert actual == expected, f"extra/missing skill files: {set(actual) ^ set(expected)}"

    @pytest.mark.unit
    def test_no_extra_command_files(self) -> None:
        if not COMMANDS_DIR.exists():
            pytest.skip(f"{COMMANDS_DIR} does not exist yet")
        actual = sorted(p.name for p in COMMANDS_DIR.glob("*.md") if not p.name.startswith("_"))
        expected = sorted(REQUIRED_COMMANDS)
        assert actual == expected, f"extra/missing command files: {set(actual) ^ set(expected)}"


# =============================================================================
# Frontmatter 検証
# =============================================================================


class TestFrontmatter:
    @pytest.mark.unit
    @pytest.mark.parametrize("filename", REQUIRED_SKILLS)
    def test_skill_has_frontmatter(self, filename: str) -> None:
        content = _read_md(SKILLS_DIR / filename)
        fm = _parse_frontmatter(content)
        assert fm is not None, f"{filename}: missing frontmatter"
        assert "name" in fm, f"{filename}: frontmatter missing 'name'"
        assert "description" in fm, f"{filename}: frontmatter missing 'description'"

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", REQUIRED_COMMANDS)
    def test_command_has_frontmatter(self, filename: str) -> None:
        content = _read_md(COMMANDS_DIR / filename)
        fm = _parse_frontmatter(content)
        assert fm is not None, f"{filename}: missing frontmatter"
        assert "name" in fm, f"{filename}: frontmatter missing 'name'"
        assert "description" in fm, f"{filename}: frontmatter missing 'description'"

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", REQUIRED_COMMANDS)
    def test_command_name_starts_with_wiki(self, filename: str) -> None:
        content = _read_md(COMMANDS_DIR / filename)
        fm = _parse_frontmatter(content) or {}
        name = fm.get("name", "")
        assert name.startswith("wiki-"), f"{filename}: name {name!r} must start with 'wiki-'"

    @pytest.mark.unit
    @pytest.mark.parametrize("filename", REQUIRED_COMMANDS)
    def test_command_name_matches_filename(self, filename: str) -> None:
        """frontmatter name が filename (without .md) と一致"""
        content = _read_md(COMMANDS_DIR / filename)
        fm = _parse_frontmatter(content) or {}
        expected_name = filename[:-3]  # strip .md
        assert fm.get("name") == expected_name, (
            f"{filename}: name {fm.get('name')!r} != {expected_name!r}"
        )


# =============================================================================
# 参照整合性
# =============================================================================


class TestCrossReferences:
    @pytest.mark.unit
    @pytest.mark.parametrize("command_filename, cli_module", list(COMMAND_TO_CLI.items()))
    def test_command_references_cli(self, command_filename: str, cli_module: str) -> None:
        """command md は対応する CLI モジュール名を本文に含む"""
        content = _read_md(COMMANDS_DIR / command_filename)
        assert cli_module in content, f"{command_filename}: must reference '{cli_module}' in body"

    @pytest.mark.unit
    @pytest.mark.parametrize("command_filename, skill_filename", list(COMMAND_TO_SKILL.items()))
    def test_command_references_skill(self, command_filename: str, skill_filename: str) -> None:
        """command md は対応する skill ファイル名を本文に含む（フルパス or ファイル名）"""
        content = _read_md(COMMANDS_DIR / command_filename)
        skill_name = skill_filename[:-3]  # without .md
        assert skill_filename in content or skill_name in content, (
            f"{command_filename}: must reference skill '{skill_filename}' or '{skill_name}'"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("skill_filename, cli_module", list(SKILL_TO_CLI.items()))
    def test_skill_references_cli(self, skill_filename: str, cli_module: str) -> None:
        """操作系 skill は対応する CLI モジュール名を含む"""
        content = _read_md(SKILLS_DIR / skill_filename)
        assert cli_module in content, f"{skill_filename}: must reference '{cli_module}' in body"

    @pytest.mark.unit
    def test_main_skill_lists_all_commands(self) -> None:
        """SKILL.md は全 20 コマンドを言及する（ナビゲーター責務）"""
        content = _read_md(SKILLS_DIR / "SKILL.md")
        for cmd in REQUIRED_COMMANDS:
            cmd_name = cmd[:-3]  # without .md
            assert cmd_name in content, f"SKILL.md: must list /{cmd_name}"

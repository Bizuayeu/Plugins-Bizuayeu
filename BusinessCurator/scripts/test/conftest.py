#!/usr/bin/env python3
"""
pytest 共通設定
===============

BusinessCuratorのテスト共通設定。
- pytestマーカー登録
- hypothesisプロファイル設定

Phase 1以降で domain/application 層の fixture を追加する。
"""

import os

import pytest

# =============================================================================
# Hypothesis Configuration
# =============================================================================

try:
    from hypothesis import Verbosity, settings

    # Default profile for local development
    settings.register_profile("default", max_examples=100)

    # CI profile - more thorough but slower
    settings.register_profile("ci", max_examples=500, verbosity=Verbosity.verbose)

    # Quick profile for rapid iteration
    settings.register_profile("quick", max_examples=20)

    # Load profile from environment or use default
    settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))

except ImportError:
    # hypothesis is an optional dependency
    pass


# =============================================================================
# pytestマーカー定義
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """カスタムマーカーを登録"""
    config.addinivalue_line("markers", "unit: 単体テスト（高速、外部依存なし）")
    config.addinivalue_line("markers", "integration: 統合テスト（ファイルI/O）")
    config.addinivalue_line("markers", "property: Property-based tests using hypothesis")
    config.addinivalue_line("markers", "cli: CLI統合テスト（subprocess経由）")
    config.addinivalue_line("markers", "slow: 時間のかかるテスト")

"""
Pytest configuration and shared fixtures.

最小構成: マーカー登録のみ。Phase 1以降でFake注入フィクスチャを拡張する。
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers (pyproject.toml と同期)."""
    config.addinivalue_line("markers", "unit: 単体テスト（高速、外部依存なし）")
    config.addinivalue_line("markers", "integration: 統合テスト（ファイルI/O）")
    config.addinivalue_line(
        "markers", "property: Property-based tests using hypothesis"
    )
    config.addinivalue_line("markers", "cli: CLI統合テスト（subprocess経由）")
    config.addinivalue_line("markers", "slow: 時間のかかるテスト")

from pathlib import Path

from infrastructure.sync_state import load_sync_state, save_sync_state


class TestSyncState:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert load_sync_state(tmp_path / "nope.json") == {}

    def test_roundtrip(self, tmp_path: Path) -> None:
        target = tmp_path / "_sync_state.json"
        save_sync_state(target, {"1287379": "2026-04-14T00:00:00Z"})
        assert load_sync_state(target) == {"1287379": "2026-04-14T00:00:00Z"}

    def test_corrupt_file_returns_empty(self, tmp_path: Path) -> None:
        target = tmp_path / "_sync_state.json"
        target.write_text("not json")
        assert load_sync_state(target) == {}

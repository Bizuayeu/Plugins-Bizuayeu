from application.backup import should_skip


class TestShouldSkip:
    def test_no_prior_state_never_skips(self) -> None:
        board = {"id": 1, "updated_at": "2026-04-14T00:00:00Z"}
        assert should_skip(board, sync_state={}) is False

    def test_unchanged_updated_at_skips(self) -> None:
        board = {"id": 1, "updated_at": "2026-04-14T00:00:00Z"}
        state = {"1": "2026-04-14T00:00:00Z"}
        assert should_skip(board, sync_state=state) is True

    def test_newer_updated_at_does_not_skip(self) -> None:
        board = {"id": 1, "updated_at": "2026-04-15T00:00:00Z"}
        state = {"1": "2026-04-14T00:00:00Z"}
        assert should_skip(board, sync_state=state) is False

    def test_older_updated_at_skips(self) -> None:
        # Shouldn't happen in practice, but defensively skip.
        board = {"id": 1, "updated_at": "2026-04-13T00:00:00Z"}
        state = {"1": "2026-04-14T00:00:00Z"}
        assert should_skip(board, sync_state=state) is True

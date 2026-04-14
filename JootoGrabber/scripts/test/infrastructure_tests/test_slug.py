import pytest

from infrastructure.slug import board_slug


class TestBoardSlug:
    @pytest.mark.parametrize(
        "title,board_id,expected",
        [
            ("FY26_18 東長崎4丁目", 1287379, "1287379_FY26_18_東長崎4丁目"),
            ("  leading trailing  ", 42, "42_leading_trailing"),
            ("slash/in:name?", 7, "7_slash_in_name"),
            ("", 9, "9"),
        ],
    )
    def test_cases(self, title: str, board_id: int, expected: str) -> None:
        assert board_slug(board_id, title) == expected

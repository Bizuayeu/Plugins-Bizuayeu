import json
from pathlib import Path

from infrastructure.storage import write_json


class TestWriteJson:
    def test_creates_dirs_and_writes_utf8(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "file.json"
        write_json(target, {"名前": "太郎", "n": 1})

        assert target.exists()
        parsed = json.loads(target.read_text(encoding="utf-8"))
        assert parsed == {"名前": "太郎", "n": 1}

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        target = tmp_path / "x.json"
        write_json(target, {"v": 1})
        write_json(target, {"v": 2})
        assert json.loads(target.read_text())["v"] == 2

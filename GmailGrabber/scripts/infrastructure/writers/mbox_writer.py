#!/usr/bin/env python3
"""
MboxFileWriter
==============

GmailMessage を単一 .mbox ファイルに追記する MessageWriterProtocol 実装。
"""

import mailbox
from pathlib import Path

from domain.exceptions import ExportError
from domain.file_naming import mbox_filename
from domain.types.message import GmailMessage


class MboxFileWriter:
    """
    単一 .mbox ファイルに全メッセージを追記する writer。

    write() はメッセージを mbox に append するのみ。
    finalize() で mbox をクローズし、単一ファイルパスを返す。
    """

    def __init__(self, plan_id: str) -> None:
        self._plan_id = plan_id
        self._mbox: mailbox.mbox | None = None
        self._mbox_path: Path | None = None

    def write(self, message: GmailMessage, output_dir: str) -> str:
        """
        raw_mime を mbox メッセージとして追加する。

        Args:
            message: GmailMessage
            output_dir: 出力先ディレクトリ

        Returns:
            mbox ファイルの絶対パス（全メッセージで同じ）
        """
        try:
            if self._mbox is None:
                self._open_mbox(output_dir)
            assert self._mbox is not None
            assert self._mbox_path is not None
            self._mbox.add(mailbox.mboxMessage(message["raw_mime"]))
            self._mbox.flush()
            return str(self._mbox_path.resolve())
        except OSError as e:
            raise ExportError(f"failed to write mbox: {e}") from e

    def finalize(self, output_dir: str) -> list[str]:
        """
        mbox をクローズし、単一ファイルパスを返す。

        Returns:
            [mbox_file_path] （1要素のリスト）
        """
        if self._mbox is None:
            # write() が一度も呼ばれていない → 空 mbox を作成しない
            return []
        try:
            self._mbox.close()
            assert self._mbox_path is not None
            return [str(self._mbox_path.resolve())]
        except OSError as e:
            raise ExportError(f"failed to finalize mbox: {e}") from e

    def _open_mbox(self, output_dir: str) -> None:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        self._mbox_path = out_path / mbox_filename(self._plan_id)
        self._mbox = mailbox.mbox(str(self._mbox_path), create=True)
        self._mbox.lock()


__all__ = ["MboxFileWriter"]

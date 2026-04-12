#!/usr/bin/env python3
"""
EmlFileWriter
=============

GmailMessage を 1メール1ファイル (.eml) として書き出す MessageWriterProtocol 実装。
"""

from pathlib import Path
from typing import List

from domain.exceptions import ExportError
from domain.file_naming import eml_filename
from domain.types.message import GmailMessage


class EmlFileWriter:
    """
    1メール 1 .eml ファイル方式で書き出す writer。

    finalize は何もせず空リストを返す（呼び出し側は write() の戻り値を集める）。
    """

    def __init__(self) -> None:
        self._written_paths: List[str] = []

    def write(self, message: GmailMessage, output_dir: str) -> str:
        """
        raw_mime をそのまま .eml ファイルに書き出す。

        Args:
            message: GmailMessage
            output_dir: 出力先ディレクトリ（存在しない場合は作成）

        Returns:
            書き出したファイルの絶対パス
        """
        try:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            filename = eml_filename(message["internal_date"], message["gmail_id"])
            file_path = out_path / filename
            file_path.write_bytes(message["raw_mime"])
            abs_path = str(file_path.resolve())
            self._written_paths.append(abs_path)
            return abs_path
        except OSError as e:
            raise ExportError(f"failed to write eml: {e}") from e

    def finalize(self, output_dir: str) -> List[str]:
        """
        個別ファイル方式なので最終化不要。

        Returns:
            空リスト（FetchBatchUseCase は write() 戻り値を集約する）
        """
        return []


__all__ = ["EmlFileWriter"]

#!/usr/bin/env python3
"""
JsonStateRepository
===================

StateRepositoryProtocol の JSON ファイル実装。

保存形式: {state_dir}/state_{plan_id}.json
"""

import json
from datetime import datetime
from pathlib import Path

from domain.exceptions import StateRepositoryError
from domain.types.backup import BackupState


class JsonStateRepository:
    """BackupState を JSON ファイルで永続化"""

    def load(self, plan_id: str, state_dir: str) -> BackupState | None:
        try:
            path = self._state_path(plan_id, state_dir)
            if not path.exists():
                return None
            raw = json.loads(path.read_text(encoding="utf-8"))
            return self._deserialize(raw)
        except (OSError, json.JSONDecodeError) as e:
            raise StateRepositoryError(f"failed to load state for {plan_id}: {e}") from e

    def save(self, state: BackupState, state_dir: str) -> None:
        try:
            Path(state_dir).mkdir(parents=True, exist_ok=True)
            path = self._state_path(state["plan_id"], state_dir)
            serialized = self._serialize(state)
            path.write_text(
                json.dumps(serialized, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            raise StateRepositoryError(f"failed to save state for {state['plan_id']}: {e}") from e

    def delete(self, plan_id: str, state_dir: str) -> None:
        try:
            path = self._state_path(plan_id, state_dir)
            if path.exists():
                path.unlink()
        except OSError as e:
            raise StateRepositoryError(f"failed to delete state for {plan_id}: {e}") from e

    # =========================================================================
    # helpers
    # =========================================================================

    def _state_path(self, plan_id: str, state_dir: str) -> Path:
        return Path(state_dir) / f"state_{plan_id}.json"

    def _serialize(self, state: BackupState) -> dict:
        return {
            "plan_id": state["plan_id"],
            "fetched_ids": list(state["fetched_ids"]),
            "failed_ids": list(state["failed_ids"]),
            "last_updated": state["last_updated"].isoformat(),
            "total_estimated": state["total_estimated"],
        }

    def _deserialize(self, raw: dict) -> BackupState:
        return {
            "plan_id": raw["plan_id"],
            "fetched_ids": list(raw.get("fetched_ids", [])),
            "failed_ids": list(raw.get("failed_ids", [])),
            "last_updated": datetime.fromisoformat(raw["last_updated"]),
            "total_estimated": int(raw.get("total_estimated", 0)),
        }


__all__ = ["JsonStateRepository"]

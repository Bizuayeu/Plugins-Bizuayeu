#!/usr/bin/env python3
"""
JsonMultiUserStateRepository
============================

MultiUserStateRepositoryProtocol の JSON ファイル実装。

保存形式: {state_dir}/multi_state_{multi_plan_id}.json

per_user_states (Dict[str, BackupState]) を nested serialize する。
datetime は isoformat 文字列化。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from domain.exceptions import StateRepositoryError
from domain.types.backup import BackupState
from domain.types.multi_backup import MultiUserBackupState


class JsonMultiUserStateRepository:
    """MultiUserBackupState を JSON ファイルで永続化"""

    def load(self, multi_plan_id: str, state_dir: str) -> MultiUserBackupState | None:
        try:
            path = self._state_path(multi_plan_id, state_dir)
            if not path.exists():
                return None
            raw = json.loads(path.read_text(encoding="utf-8"))
            return self._deserialize(raw)
        except (OSError, json.JSONDecodeError) as e:
            raise StateRepositoryError(
                f"failed to load multi-user state for {multi_plan_id}: {e}"
            ) from e

    def save(self, state: MultiUserBackupState, state_dir: str) -> None:
        try:
            Path(state_dir).mkdir(parents=True, exist_ok=True)
            path = self._state_path(state["multi_plan_id"], state_dir)
            serialized = self._serialize(state)
            path.write_text(
                json.dumps(serialized, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            raise StateRepositoryError(
                f"failed to save multi-user state for {state['multi_plan_id']}: {e}"
            ) from e

    def delete(self, multi_plan_id: str, state_dir: str) -> None:
        try:
            path = self._state_path(multi_plan_id, state_dir)
            if path.exists():
                path.unlink()
        except OSError as e:
            raise StateRepositoryError(
                f"failed to delete multi-user state for {multi_plan_id}: {e}"
            ) from e

    # =========================================================================
    # helpers
    # =========================================================================

    def _state_path(self, multi_plan_id: str, state_dir: str) -> Path:
        return Path(state_dir) / f"multi_state_{multi_plan_id}.json"

    def _serialize(self, state: MultiUserBackupState) -> dict[str, Any]:
        return {
            "multi_plan_id": state["multi_plan_id"],
            "per_user_states": {
                email: self._serialize_single_state(s)
                for email, s in state["per_user_states"].items()
            },
            "message_id_index": dict(state["message_id_index"]),
            "last_updated": state["last_updated"].isoformat(),
            "started_user_emails": list(state["started_user_emails"]),
            "completed_user_emails": list(state["completed_user_emails"]),
        }

    def _serialize_single_state(self, s: BackupState) -> dict[str, Any]:
        return {
            "plan_id": s["plan_id"],
            "fetched_ids": list(s["fetched_ids"]),
            "failed_ids": list(s["failed_ids"]),
            "last_updated": s["last_updated"].isoformat(),
            "total_estimated": s["total_estimated"],
        }

    def _deserialize(self, raw: dict[str, Any]) -> MultiUserBackupState:
        return {
            "multi_plan_id": raw["multi_plan_id"],
            "per_user_states": {
                email: self._deserialize_single_state(s)
                for email, s in raw.get("per_user_states", {}).items()
            },
            "message_id_index": dict(raw.get("message_id_index", {})),
            "last_updated": datetime.fromisoformat(raw["last_updated"]),
            "started_user_emails": list(raw.get("started_user_emails", [])),
            "completed_user_emails": list(raw.get("completed_user_emails", [])),
        }

    def _deserialize_single_state(self, raw: dict[str, Any]) -> BackupState:
        return {
            "plan_id": raw["plan_id"],
            "fetched_ids": list(raw.get("fetched_ids", [])),
            "failed_ids": list(raw.get("failed_ids", [])),
            "last_updated": datetime.fromisoformat(raw["last_updated"]),
            "total_estimated": int(raw.get("total_estimated", 0)),
        }


__all__ = ["JsonMultiUserStateRepository"]

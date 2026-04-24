"""JSON-backed storage for the minimal Styio community decision flow."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .state_machine import InvalidTransition, StateMachineError, WorkflowNode


class StorageError(Exception):
    """Base class for storage-layer failures surfaced to the API."""


class RecordNotFoundError(StorageError):
    """Raised when a requested decision record does not exist."""


class ValidationError(StorageError):
    """Raised when a requested mutation is missing required input."""


class ConflictError(StorageError):
    """Raised when a requested mutation is invalid for the current state."""


Clock = Callable[[], str]
IdFactory = Callable[[], str]

EVENT_TYPE_BY_KIND = {
    "syntax-change": "syntax_change",
    "ide-capability-gap": "ide_capability_gap",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def default_store_path() -> Path:
    configured = os.environ.get("STYIO_COMMUNITY_STORE")
    if configured:
        return Path(configured)
    return Path.cwd() / ".styio-community" / "records.json"


def build_dispatch_payload(record: dict[str, Any]) -> dict[str, Any]:
    decision = record.get("decision") or {}
    event_type = EVENT_TYPE_BY_KIND.get(record["kind"], record["kind"].replace("-", "_"))
    target_repository = record.get("target_repository") or record.get("repository", "styio-view")
    source_repository = record.get("source_repository") or "styio-community"
    return {
        "schema_version": "styio.community.decision.v1",
        "node_id": record["id"],
        "record_id": record["id"],
        "event_type": event_type,
        "repository": target_repository,
        "source_repository": source_repository,
        "target_repository": target_repository,
        "kind": record["kind"],
        "title": record["title"],
        "status": record["status"],
        "decision": {
            "state": decision.get("state"),
            "opinion": decision.get("opinion"),
            "decided_at": decision.get("decided_at"),
        },
        "payload": copy.deepcopy(record.get("proposal", {})),
        "proposal": copy.deepcopy(record.get("proposal", {})),
    }


class JsonRecordStore:
    def __init__(
        self,
        path: str | os.PathLike[str] | None = None,
        *,
        clock: Clock = utc_now,
        id_factory: IdFactory | None = None,
    ) -> None:
        self.path = Path(path) if path is not None else default_store_path()
        self._clock = clock
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))

    def list_records(self) -> list[dict[str, Any]]:
        records = self._read_records()
        return [copy.deepcopy(record) for record in records]

    def get_record(self, record_id: str) -> dict[str, Any]:
        for record in self._read_records():
            if record["id"] == record_id:
                return copy.deepcopy(record)
        raise RecordNotFoundError(f"record not found: {record_id}")

    def create_record(
        self,
        *,
        kind: str,
        title: str,
        summary: str,
        proposal: Mapping[str, Any],
        source_repository: str = "styio-community",
        target_repository: str | None = None,
        repository: str | None = None,
        detected_message: str | None = None,
    ) -> dict[str, Any]:
        kind = _require_text(kind, "kind")
        title = _require_text(title, "title")
        summary = _require_text(summary, "summary")
        proposal = _require_mapping(proposal, "proposal")
        source_repository = _require_text(source_repository, "source_repository")
        target_repository = _default_target_repository(kind, target_repository or repository)

        records = self._read_records()
        now = self._clock()
        record = {
            "id": self._id_factory(),
            "kind": kind,
            "title": title,
            "summary": summary,
            "status": "awaiting_decision",
            "created_at": now,
            "updated_at": now,
            "source_repository": source_repository,
            "target_repository": target_repository,
            "repository": target_repository,
            "proposal": proposal,
            "decision": None,
            "dispatch": None,
            "history": [
                {
                    "at": now,
                    "event": "detected",
                    "message": detected_message or f"{kind} proposal detected.",
                },
                {
                    "at": now,
                    "event": "awaiting_decision",
                    "message": f"{kind} proposal is ready for a written decision opinion.",
                },
            ],
        }
        records.append(record)
        self._write_records(records)
        return copy.deepcopy(record)

    def create_demo_syntax_change(self) -> dict[str, Any]:
        return self.create_record(
            kind="syntax-change",
            title="Demo syntax-change: stdin return pipe",
            summary="A minimal upstream syntax record that should be adapted by styio-view after approval.",
            source_repository="styio",
            target_repository="styio-view",
            proposal={
                "title": "stdin return pipe shorthand",
                "syntax_area": "IO return grammar",
                "summary": "Support `@stdin := { <| [>_] }` as the compact return-pipe form and keep `@stdin := { <| <- [>_] }` as the expanded form.",
                "rationale": "The community decision should move the approved syntax into downstream IDE grammar and highlighting without making GitHub issues the decision source.",
                "examples": [
                    "@stdin := { <| [>_] }",
                    "@stdin := { <| <- [>_] }",
                    "str.lines() >> [>_]",
                ],
                "affected_components": [
                    "syntax highlighter",
                    "IDE parser",
                    "snippet catalog",
                ],
            },
            detected_message="Demo syntax-change proposal detected from styio.",
        )

    def create_demo_ide_gap(self) -> dict[str, Any]:
        return self.create_record(
            kind="ide-capability-gap",
            title="Demo IDE gap: inline return-pipe diagnostics",
            summary="A downstream IDE finding that should be sent back to styio after approval.",
            source_repository="styio-view",
            target_repository="styio",
            proposal={
                "capability": "Inline return-pipe diagnostics",
                "current_behavior": "The IDE can highlight the syntax but cannot explain parser-suite gaps for the return-pipe form.",
                "expected_behavior": "The Styio suite exposes enough diagnostics for styio-view to explain unsupported return-pipe cases inline.",
                "impact": "Users cannot distinguish an editor limitation from an upstream parser-suite limitation.",
                "reproduction_steps": [
                    "Open a file containing `@stdin := { <| [>_] }`.",
                    "Trigger the IDE diagnostics view.",
                    "Observe that unsupported-suite details are not available.",
                ],
            },
            detected_message="Demo IDE capability gap detected from styio-view.",
        )

    def decide_record(self, record_id: str, decision: str, opinion: str) -> dict[str, Any]:
        if decision not in {"approved", "rejected"}:
            raise ValidationError("decision must be approved or rejected")

        opinion = opinion.strip()
        if not opinion:
            raise ValidationError("decision opinion is required")

        records = self._read_records()
        record = self._find_mutable(records, record_id)
        node = _workflow_node_from_record(record)
        try:
            if decision == "approved":
                node.approve(opinion, actor="community")
            else:
                node.reject(opinion, actor="community")
        except InvalidTransition as error:
            raise ConflictError(str(error)) from error
        except StateMachineError as error:
            raise ValidationError(str(error)) from error

        now = self._clock()
        record["status"] = node.state.value
        record["updated_at"] = now
        record["decision"] = {
            "state": node.state.value,
            "opinion": opinion,
            "decided_at": now,
        }
        record["history"].append(
            {
                "at": now,
                "event": decision,
                "message": opinion,
            }
        )

        self._write_records(records)
        return copy.deepcopy(record)

    def dispatch_record(
        self,
        record_id: str,
        *,
        adapter_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        records = self._read_records()
        record = self._find_mutable(records, record_id)
        node = _workflow_node_from_record(record)
        try:
            node.dispatch(reason="Adapter-facing payload dispatched.", actor="community")
        except InvalidTransition as error:
            raise ConflictError(str(error)) from error
        except StateMachineError as error:
            raise ValidationError(str(error)) from error

        now = self._clock()
        payload = build_dispatch_payload(record)
        result = adapter_result or {
            "adapter": "fallback",
            "accepted": True,
            "message": "No community.adapters dispatcher was available; payload was recorded locally.",
        }
        record["status"] = node.state.value
        record["updated_at"] = now
        record["dispatch"] = {
            "payload": payload,
            "result": copy.deepcopy(result),
            "dispatched_at": now,
        }
        record["history"].append(
            {
                "at": now,
                "event": "dispatched",
                "message": "Adapter-facing payload dispatched.",
            }
        )

        self._write_records(records)
        return copy.deepcopy(record)

    def _find_mutable(self, records: list[dict[str, Any]], record_id: str) -> dict[str, Any]:
        for record in records:
            if record["id"] == record_id:
                return record
        raise RecordNotFoundError(f"record not found: {record_id}")

    def _read_records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        records = payload.get("records")
        if not isinstance(records, list):
            raise ValidationError("storage file must contain a records list")
        return records

    def _write_records(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"records": records}
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
        ) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temp_name = handle.name
        os.replace(temp_name, self.path)


def _workflow_node_from_record(record: Mapping[str, Any]) -> WorkflowNode:
    return WorkflowNode(
        node_id=_require_text(record.get("id"), "id"),
        state=_require_text(record.get("status"), "status"),
        payload=_require_mapping(record.get("proposal", {}), "proposal"),
        metadata={
            "kind": _require_text(record.get("kind"), "kind"),
            "source_repository": _require_text(
                record.get("source_repository", "styio-community"),
                "source_repository",
            ),
            "target_repository": _require_text(
                record.get("target_repository") or record.get("repository", "styio-view"),
                "target_repository",
            ),
        },
    )


def _default_target_repository(kind: str, value: str | None) -> str:
    if value is not None:
        return _require_text(value, "target_repository")
    if kind == "syntax-change":
        return "styio-view"
    if kind == "ide-capability-gap":
        return "styio"
    raise ValidationError(f"target_repository is required for kind: {kind}")


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValidationError(f"{field_name} must not be empty")
    return value


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{field_name} must be a JSON object")
    return copy.deepcopy(dict(value))

"""Repository adapters for community decision-framework events."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Tuple, Union

from .contracts import (
    IDE_CAPABILITY_GAP_EVENT,
    SYNTAX_CHANGE_EVENT,
    ContractValidationError,
    IDECapabilityGapPayload,
    RepositoryRequest,
    SyntaxChangePayload,
)


PayloadInput = Union[SyntaxChangePayload, IDECapabilityGapPayload, Mapping[str, Any]]


class AdapterError(ValueError):
    """Raised when an event cannot be translated for a repository."""


class RepositoryAdapter(ABC):
    """Base interface for translating framework events into repo requests."""

    repository: str
    supported_event_types: Tuple[str, ...] = ()
    common_labels: Tuple[str, ...] = ("community-decision",)

    def wrap_event(self, event: Mapping[str, Any]) -> RepositoryRequest:
        """Translate a framework event mapping into a repository request."""

        if not isinstance(event, Mapping):
            raise AdapterError("event must be a mapping")

        try:
            node_id = event["node_id"]
            event_type = event["event_type"]
            payload = event["payload"]
        except KeyError as exc:
            raise AdapterError(f"event is missing required field: {exc.args[0]}") from exc

        return self.wrap_node_payload(
            node_id=node_id,
            event_type=event_type,
            payload=payload,
        )

    def wrap_node_payload(
        self,
        node_id: str,
        event_type: str,
        payload: PayloadInput,
    ) -> RepositoryRequest:
        """Wrap a node payload in a repo-specific message.

        This method is intentionally translation-only. It does not inspect or
        mutate coordination state, advance a workflow, or execute repository IO.
        """

        node_id = self._required_text(node_id, "node_id")
        event_type = self._required_text(event_type, "event_type")
        if event_type not in self.supported_event_types:
            raise AdapterError(
                f"{self.repository} does not support event type {event_type!r}"
            )

        contract_payload = self._coerce_payload(event_type, payload)
        return self._build_request(node_id, event_type, contract_payload)

    def _coerce_payload(
        self,
        event_type: str,
        payload: PayloadInput,
    ) -> Union[SyntaxChangePayload, IDECapabilityGapPayload]:
        if event_type == SYNTAX_CHANGE_EVENT:
            if isinstance(payload, SyntaxChangePayload):
                return payload
            if isinstance(payload, Mapping):
                return SyntaxChangePayload.from_mapping(payload)
        if event_type == IDE_CAPABILITY_GAP_EVENT:
            if isinstance(payload, IDECapabilityGapPayload):
                return payload
            if isinstance(payload, Mapping):
                return IDECapabilityGapPayload.from_mapping(payload)
        raise AdapterError(f"payload does not match event type {event_type!r}")

    @abstractmethod
    def _build_request(
        self,
        node_id: str,
        event_type: str,
        payload: Union[SyntaxChangePayload, IDECapabilityGapPayload],
    ) -> RepositoryRequest:
        """Build a repository-facing request from a validated payload."""

    @staticmethod
    def _required_text(value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise AdapterError(f"{field_name} must be a string")
        value = value.strip()
        if not value:
            raise AdapterError(f"{field_name} must not be empty")
        return value


class StyioAdapter(RepositoryAdapter):
    """Adapter for language and compiler-facing `styio` requests."""

    repository = "styio"
    supported_event_types = (IDE_CAPABILITY_GAP_EVENT,)

    def _build_request(
        self,
        node_id: str,
        event_type: str,
        payload: Union[SyntaxChangePayload, IDECapabilityGapPayload],
    ) -> RepositoryRequest:
        if not isinstance(payload, IDECapabilityGapPayload):
            raise AdapterError("styio adapter requires an IDE capability gap payload")

        body = _render_sections(
            (
                ("Decision node", node_id),
                ("Capability", payload.capability),
                ("Current behavior", payload.current_behavior),
                ("Expected behavior", payload.expected_behavior),
                ("Impact", payload.impact),
                ("Reproduction steps", _render_bullets(payload.reproduction_steps)),
            )
        )
        return RepositoryRequest(
            repository=self.repository,
            title=f"[ide-gap] {payload.capability}",
            body=body,
            labels=self.common_labels + ("ide-capability-gap", "styio"),
            metadata={
                "adapter": self.repository,
                "event_type": event_type,
                "node_id": node_id,
                "payload_schema": IDE_CAPABILITY_GAP_EVENT,
            },
        )


class StyioViewAdapter(RepositoryAdapter):
    """Adapter for editor and IDE-facing `styio-view` requests."""

    repository = "styio-view"
    supported_event_types = (SYNTAX_CHANGE_EVENT,)

    def _build_request(
        self,
        node_id: str,
        event_type: str,
        payload: Union[SyntaxChangePayload, IDECapabilityGapPayload],
    ) -> RepositoryRequest:
        if not isinstance(payload, SyntaxChangePayload):
            raise AdapterError("styio-view adapter requires a syntax change payload")

        body = _render_sections(
            (
                ("Decision node", node_id),
                ("Syntax area", payload.syntax_area),
                ("Summary", payload.summary),
                ("Rationale", payload.rationale or "Not provided."),
                ("Examples", _render_bullets(payload.examples)),
                ("Affected components", _render_bullets(payload.affected_components)),
            )
        )
        return RepositoryRequest(
            repository=self.repository,
            title=f"[syntax-adaptation] {payload.title}",
            body=body,
            labels=self.common_labels + ("syntax-change", "syntax-adaptation", "styio-view"),
            metadata={
                "adapter": self.repository,
                "event_type": event_type,
                "node_id": node_id,
                "payload_schema": SYNTAX_CHANGE_EVENT,
            },
        )


def adapter_for_repository(repository: str) -> RepositoryAdapter:
    """Return the adapter for a supported repository name."""

    repository = RepositoryAdapter._required_text(repository, "repository")
    adapters = {
        "styio": StyioAdapter,
        "styio-view": StyioViewAdapter,
    }
    try:
        return adapters[repository]()
    except KeyError as exc:
        raise AdapterError(f"unsupported repository: {repository}") from exc


def _render_sections(sections: Tuple[Tuple[str, str], ...]) -> str:
    rendered = []
    for heading, content in sections:
        rendered.append(f"## {heading}\n\n{content}")
    return "\n\n".join(rendered)


def _render_bullets(items: Tuple[str, ...]) -> str:
    if not items:
        return "Not provided."
    return "\n".join(f"- {item}" for item in items)


__all__ = [
    "AdapterError",
    "ContractValidationError",
    "RepositoryAdapter",
    "StyioAdapter",
    "StyioViewAdapter",
    "adapter_for_repository",
]

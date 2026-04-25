"""Minimal generic state machine for community decision workflows."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Mapping, Optional, Set


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class StateMachineError(ValueError):
    """Base error for invalid state-machine operations."""


class InvalidTransition(StateMachineError):
    """Raised when a state transition is not allowed."""


class SerializationError(StateMachineError):
    """Raised when serialized state-machine data is malformed."""


class State(str, Enum):
    DETECTED = "detected"
    AWAITING_DECISION = "awaiting_decision"
    APPROVED = "approved"
    DISPATCHED = "dispatched"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    REJECTED = "rejected"


class DecisionAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


@dataclass(frozen=True)
class EventRecord:
    name: str
    state: State
    message: str = ""
    actor: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _coerce_state(self.state))
        object.__setattr__(self, "data", deepcopy(self.data))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "message": self.message,
            "actor": self.actor,
            "data": deepcopy(self.data),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EventRecord":
        try:
            return cls(
                name=_require_string(value, "name"),
                state=_coerce_state(value["state"]),
                message=str(value.get("message", "")),
                actor=_optional_string(value.get("actor")),
                data=_require_dict(value.get("data", {}), "data"),
                timestamp=_require_string(value, "timestamp"),
            )
        except KeyError as exc:
            raise SerializationError(f"missing event field: {exc.args[0]}") from exc


@dataclass(frozen=True)
class TransitionRecord:
    from_state: State
    to_state: State
    event: str
    reason: str = ""
    actor: Optional[str] = None
    timestamp: str = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "from_state", _coerce_state(self.from_state))
        object.__setattr__(self, "to_state", _coerce_state(self.to_state))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "event": self.event,
            "reason": self.reason,
            "actor": self.actor,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TransitionRecord":
        try:
            return cls(
                from_state=_coerce_state(value["from_state"]),
                to_state=_coerce_state(value["to_state"]),
                event=_require_string(value, "event"),
                reason=str(value.get("reason", "")),
                actor=_optional_string(value.get("actor")),
                timestamp=_require_string(value, "timestamp"),
            )
        except KeyError as exc:
            raise SerializationError(f"missing transition field: {exc.args[0]}") from exc


@dataclass(frozen=True)
class DecisionRecord:
    action: DecisionAction
    opinion: str
    actor: Optional[str] = None
    timestamp: str = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", _coerce_decision_action(self.action))
        object.__setattr__(self, "opinion", _require_non_empty_text(self.opinion, "opinion"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "opinion": self.opinion,
            "actor": self.actor,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DecisionRecord":
        try:
            return cls(
                action=_coerce_decision_action(value["action"]),
                opinion=_require_string(value, "opinion"),
                actor=_optional_string(value.get("actor")),
                timestamp=_require_string(value, "timestamp"),
            )
        except KeyError as exc:
            raise SerializationError(f"missing decision field: {exc.args[0]}") from exc


@dataclass
class WorkflowNode:
    """A repository-agnostic workflow item that moves through decision states."""

    node_id: str
    state: State = State.DETECTED
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[TransitionRecord] = field(default_factory=list)
    events: List[EventRecord] = field(default_factory=list)
    decisions: List[DecisionRecord] = field(default_factory=list)

    _ALLOWED_TRANSITIONS: ClassVar[Dict[State, Set[State]]] = {
        State.DETECTED: {State.AWAITING_DECISION, State.BLOCKED},
        State.AWAITING_DECISION: {State.APPROVED, State.REJECTED, State.BLOCKED},
        State.APPROVED: {State.DISPATCHED, State.BLOCKED, State.COMPLETED},
        State.DISPATCHED: {State.COMPLETED, State.BLOCKED},
        State.BLOCKED: {State.AWAITING_DECISION},
        State.COMPLETED: set(),
        State.REJECTED: set(),
    }

    def __post_init__(self) -> None:
        self.node_id = _require_non_empty_text(self.node_id, "node_id")
        self.state = _coerce_state(self.state)
        self.payload = _require_dict(self.payload, "payload")
        self.metadata = _require_dict(self.metadata, "metadata")
        self.history = [self._coerce_transition(record) for record in self.history]
        self.events = [self._coerce_event(record) for record in self.events]
        self.decisions = [self._coerce_decision(record) for record in self.decisions]

    @classmethod
    def create(
        cls,
        node_id: str,
        payload: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        actor: Optional[str] = None,
    ) -> "WorkflowNode":
        node = cls(
            node_id=node_id,
            payload=dict(payload or {}),
            metadata=dict(metadata or {}),
        )
        node.events.append(
            EventRecord(
                name="node.detected",
                state=node.state,
                actor=actor,
                message="workflow node detected",
            )
        )
        return node

    @property
    def is_terminal(self) -> bool:
        return self.state in {State.COMPLETED, State.REJECTED}

    def allowed_next_states(self) -> List[State]:
        return sorted(self._ALLOWED_TRANSITIONS[self.state], key=lambda item: item.value)

    def transition_to(
        self,
        next_state: State,
        *,
        event: str = "state.transitioned",
        reason: str = "",
        actor: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> TransitionRecord:
        next_state = _coerce_state(next_state)
        if next_state in {State.APPROVED, State.REJECTED}:
            raise InvalidTransition(
                "approval and rejection must be recorded with approve() or reject() "
                "so the decision opinion is preserved"
            )
        return self._apply_transition(
            next_state,
            event=event,
            reason=reason,
            actor=actor,
            data=data,
        )

    def request_decision(
        self,
        *,
        reason: str = "",
        actor: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> TransitionRecord:
        return self.transition_to(
            State.AWAITING_DECISION,
            event="decision.requested",
            reason=reason,
            actor=actor,
            data=data,
        )

    def approve(self, opinion: str, *, actor: Optional[str] = None) -> DecisionRecord:
        return self.decide(DecisionAction.APPROVE, opinion, actor=actor)

    def reject(self, opinion: str, *, actor: Optional[str] = None) -> DecisionRecord:
        return self.decide(DecisionAction.REJECT, opinion, actor=actor)

    def decide(
        self,
        action: DecisionAction,
        opinion: str,
        *,
        actor: Optional[str] = None,
    ) -> DecisionRecord:
        if self.state != State.AWAITING_DECISION:
            raise InvalidTransition(
                f"decision actions require {State.AWAITING_DECISION.value}; "
                f"current state is {self.state.value}"
            )

        action = _coerce_decision_action(action)
        decision = DecisionRecord(action=action, opinion=opinion, actor=actor)
        next_state = State.APPROVED if action == DecisionAction.APPROVE else State.REJECTED

        self._apply_transition(
            next_state,
            event=f"decision.{action.value}",
            reason=decision.opinion,
            actor=actor,
            data={"decision": action.value, "opinion": decision.opinion},
        )
        self.decisions.append(decision)
        return decision

    def dispatch(
        self,
        *,
        reason: str = "",
        actor: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> TransitionRecord:
        return self.transition_to(
            State.DISPATCHED,
            event="node.dispatched",
            reason=reason,
            actor=actor,
            data=data,
        )

    def block(
        self,
        reason: str,
        *,
        actor: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> TransitionRecord:
        return self.transition_to(
            State.BLOCKED,
            event="node.blocked",
            reason=_require_non_empty_text(reason, "reason"),
            actor=actor,
            data=data,
        )

    def complete(
        self,
        *,
        reason: str = "",
        actor: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> TransitionRecord:
        return self.transition_to(
            State.COMPLETED,
            event="node.completed",
            reason=reason,
            actor=actor,
            data=data,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "state": self.state.value,
            "payload": deepcopy(self.payload),
            "metadata": deepcopy(self.metadata),
            "history": [record.to_dict() for record in self.history],
            "events": [record.to_dict() for record in self.events],
            "decisions": [record.to_dict() for record in self.decisions],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "WorkflowNode":
        try:
            return cls(
                node_id=_require_string(value, "node_id"),
                state=_coerce_state(value["state"]),
                payload=_require_dict(value.get("payload", {}), "payload"),
                metadata=_require_dict(value.get("metadata", {}), "metadata"),
                history=[
                    TransitionRecord.from_dict(record)
                    for record in _require_sequence(value.get("history", []), "history")
                ],
                events=[
                    EventRecord.from_dict(record)
                    for record in _require_sequence(value.get("events", []), "events")
                ],
                decisions=[
                    DecisionRecord.from_dict(record)
                    for record in _require_sequence(value.get("decisions", []), "decisions")
                ],
            )
        except KeyError as exc:
            raise SerializationError(f"missing workflow node field: {exc.args[0]}") from exc

    @classmethod
    def _coerce_transition(cls, value: Any) -> TransitionRecord:
        if isinstance(value, TransitionRecord):
            return value
        if isinstance(value, Mapping):
            return TransitionRecord.from_dict(value)
        raise SerializationError("history entries must be transition records or dictionaries")

    @classmethod
    def _coerce_event(cls, value: Any) -> EventRecord:
        if isinstance(value, EventRecord):
            return value
        if isinstance(value, Mapping):
            return EventRecord.from_dict(value)
        raise SerializationError("event entries must be event records or dictionaries")

    @classmethod
    def _coerce_decision(cls, value: Any) -> DecisionRecord:
        if isinstance(value, DecisionRecord):
            return value
        if isinstance(value, Mapping):
            return DecisionRecord.from_dict(value)
        raise SerializationError("decision entries must be decision records or dictionaries")

    def _apply_transition(
        self,
        next_state: State,
        *,
        event: str,
        reason: str,
        actor: Optional[str],
        data: Optional[Mapping[str, Any]],
    ) -> TransitionRecord:
        self._validate_transition(next_state)
        previous_state = self.state
        self.state = next_state

        transition = TransitionRecord(
            from_state=previous_state,
            to_state=next_state,
            event=event,
            reason=reason,
            actor=actor,
        )
        event_data = {
            "from_state": previous_state.value,
            "to_state": next_state.value,
        }
        if data:
            event_data.update(deepcopy(dict(data)))

        self.history.append(transition)
        self.events.append(
            EventRecord(
                name=event,
                state=next_state,
                message=reason,
                actor=actor,
                data=event_data,
            )
        )
        return transition

    def _validate_transition(self, next_state: State) -> None:
        if next_state not in self._ALLOWED_TRANSITIONS[self.state]:
            allowed = ", ".join(state.value for state in self.allowed_next_states()) or "none"
            raise InvalidTransition(
                f"cannot transition from {self.state.value} to {next_state.value}; "
                f"allowed next states: {allowed}"
            )


def _coerce_state(value: Any) -> State:
    if isinstance(value, State):
        return value
    try:
        return State(value)
    except ValueError as exc:
        raise SerializationError(f"unknown workflow state: {value!r}") from exc


def _coerce_decision_action(value: Any) -> DecisionAction:
    if isinstance(value, DecisionAction):
        return value
    try:
        return DecisionAction(value)
    except ValueError as exc:
        raise SerializationError(f"unknown decision action: {value!r}") from exc


def _require_dict(value: Any, field_name: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SerializationError(f"{field_name} must be a dictionary")
    return deepcopy(dict(value))


def _require_sequence(value: Any, field_name: str) -> List[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise SerializationError(f"{field_name} must be a list")
    for item in value:
        if not isinstance(item, Mapping):
            raise SerializationError(f"{field_name} entries must be dictionaries")
    return value


def _require_string(value: Mapping[str, Any], field_name: str) -> str:
    result = value.get(field_name)
    if not isinstance(result, str):
        raise SerializationError(f"{field_name} must be a string")
    return result


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SerializationError("actor must be a string or null")
    return value


def _require_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise SerializationError(f"{field_name} must be a string")
    result = value.strip()
    if not result:
        raise StateMachineError(f"{field_name} must not be empty")
    return result

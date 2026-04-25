"""Payload contracts for repository-facing community requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Mapping, Tuple


SYNTAX_CHANGE_EVENT = "syntax_change"
IDE_CAPABILITY_GAP_EVENT = "ide_capability_gap"


class ContractValidationError(ValueError):
    """Raised when a framework payload does not match its contract."""


def _normalize_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ContractValidationError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ContractValidationError(f"{field_name} must not be empty")
    return value


def _normalize_optional_text(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ContractValidationError(f"{field_name} must be a string")
    return value.strip()


def _normalize_string_tuple(value: Any, field_name: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        value = (value,)
    if not isinstance(value, (list, tuple)):
        raise ContractValidationError(f"{field_name} must be a list of strings")

    normalized = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ContractValidationError(
                f"{field_name}[{index}] must be a string"
            )
        item = item.strip()
        if not item:
            raise ContractValidationError(
                f"{field_name}[{index}] must not be empty"
            )
        normalized.append(item)
    return tuple(normalized)


def _normalize_metadata(value: Any) -> Dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ContractValidationError("metadata must be a mapping")

    normalized: Dict[str, str] = {}
    for key, item in value.items():
        key = _normalize_text(key, "metadata key")
        normalized[key] = _normalize_text(item, f"metadata[{key}]")
    return normalized


def _reject_unknown_fields(data: Mapping[str, Any], allowed: Tuple[str, ...]) -> None:
    unknown = sorted(set(data) - set(allowed))
    if unknown:
        fields = ", ".join(unknown)
        raise ContractValidationError(f"unknown payload field(s): {fields}")


def _string_schema(description: str) -> Dict[str, Any]:
    return {
        "type": "string",
        "minLength": 1,
        "description": description,
    }


def _optional_string_schema(description: str) -> Dict[str, Any]:
    return {
        "type": "string",
        "description": description,
    }


def _string_array_schema(description: str) -> Dict[str, Any]:
    return {
        "type": "array",
        "description": description,
        "items": {"type": "string", "minLength": 1},
    }


@dataclass(frozen=True)
class SyntaxChangePayload:
    """Contract for a language or syntax-level change request."""

    title: str
    syntax_area: str
    summary: str
    rationale: str = ""
    examples: Tuple[str, ...] = field(default_factory=tuple)
    affected_components: Tuple[str, ...] = field(default_factory=tuple)

    EVENT_TYPE: ClassVar[str] = SYNTAX_CHANGE_EVENT
    _FIELDS: ClassVar[Tuple[str, ...]] = (
        "title",
        "syntax_area",
        "summary",
        "rationale",
        "examples",
        "affected_components",
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _normalize_text(self.title, "title"))
        object.__setattr__(
            self,
            "syntax_area",
            _normalize_text(self.syntax_area, "syntax_area"),
        )
        object.__setattr__(self, "summary", _normalize_text(self.summary, "summary"))
        object.__setattr__(
            self,
            "rationale",
            _normalize_optional_text(self.rationale, "rationale"),
        )
        object.__setattr__(
            self,
            "examples",
            _normalize_string_tuple(self.examples, "examples"),
        )
        object.__setattr__(
            self,
            "affected_components",
            _normalize_string_tuple(
                self.affected_components,
                "affected_components",
            ),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SyntaxChangePayload":
        if not isinstance(data, Mapping):
            raise ContractValidationError("syntax change payload must be a mapping")
        _reject_unknown_fields(data, cls._FIELDS)
        return cls(
            title=data.get("title"),
            syntax_area=data.get("syntax_area"),
            summary=data.get("summary"),
            rationale=data.get("rationale", ""),
            examples=data.get("examples", ()),
            affected_components=data.get("affected_components", ()),
        )

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "syntax_area": self.syntax_area,
            "summary": self.summary,
            "rationale": self.rationale,
            "examples": list(self.examples),
            "affected_components": list(self.affected_components),
        }

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "SyntaxChangePayload",
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "syntax_area", "summary"],
            "properties": {
                "title": _string_schema("Short repository-facing request title."),
                "syntax_area": _string_schema(
                    "Language, parser, formatter, or grammar area affected."
                ),
                "summary": _string_schema("Concise description of the change."),
                "rationale": _optional_string_schema(
                    "Optional reason the change is needed."
                ),
                "examples": _string_array_schema(
                    "Optional before/after snippets or usage examples."
                ),
                "affected_components": _string_array_schema(
                    "Optional compiler or tooling components affected."
                ),
            },
        }


@dataclass(frozen=True)
class IDECapabilityGapPayload:
    """Contract for a missing or incomplete IDE capability."""

    capability: str
    current_behavior: str
    expected_behavior: str
    impact: str
    reproduction_steps: Tuple[str, ...] = field(default_factory=tuple)

    EVENT_TYPE: ClassVar[str] = IDE_CAPABILITY_GAP_EVENT
    _FIELDS: ClassVar[Tuple[str, ...]] = (
        "capability",
        "current_behavior",
        "expected_behavior",
        "impact",
        "reproduction_steps",
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capability",
            _normalize_text(self.capability, "capability"),
        )
        object.__setattr__(
            self,
            "current_behavior",
            _normalize_text(self.current_behavior, "current_behavior"),
        )
        object.__setattr__(
            self,
            "expected_behavior",
            _normalize_text(self.expected_behavior, "expected_behavior"),
        )
        object.__setattr__(self, "impact", _normalize_text(self.impact, "impact"))
        object.__setattr__(
            self,
            "reproduction_steps",
            _normalize_string_tuple(
                self.reproduction_steps,
                "reproduction_steps",
            ),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "IDECapabilityGapPayload":
        if not isinstance(data, Mapping):
            raise ContractValidationError("IDE capability gap payload must be a mapping")
        _reject_unknown_fields(data, cls._FIELDS)
        return cls(
            capability=data.get("capability"),
            current_behavior=data.get("current_behavior"),
            expected_behavior=data.get("expected_behavior"),
            impact=data.get("impact"),
            reproduction_steps=data.get("reproduction_steps", ()),
        )

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "capability": self.capability,
            "current_behavior": self.current_behavior,
            "expected_behavior": self.expected_behavior,
            "impact": self.impact,
            "reproduction_steps": list(self.reproduction_steps),
        }

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "IDECapabilityGapPayload",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "capability",
                "current_behavior",
                "expected_behavior",
                "impact",
            ],
            "properties": {
                "capability": _string_schema("IDE feature or capability name."),
                "current_behavior": _string_schema(
                    "What users can or cannot do today."
                ),
                "expected_behavior": _string_schema(
                    "Expected IDE behavior once the gap is closed."
                ),
                "impact": _string_schema("Why this gap matters to users or workflow."),
                "reproduction_steps": _string_array_schema(
                    "Optional steps that demonstrate the gap."
                ),
            },
        }


@dataclass(frozen=True)
class RepositoryRequest:
    """Repository-facing message produced by an adapter."""

    repository: str
    title: str
    body: str
    labels: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "repository",
            _normalize_text(self.repository, "repository"),
        )
        object.__setattr__(self, "title", _normalize_text(self.title, "title"))
        object.__setattr__(self, "body", _normalize_text(self.body, "body"))
        object.__setattr__(
            self,
            "labels",
            _normalize_string_tuple(self.labels, "labels"),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "repository": self.repository,
            "title": self.title,
            "body": self.body,
            "labels": list(self.labels),
            "metadata": dict(self.metadata),
        }


CONTRACT_SCHEMAS = {
    SYNTAX_CHANGE_EVENT: SyntaxChangePayload.schema(),
    IDE_CAPABILITY_GAP_EVENT: IDECapabilityGapPayload.schema(),
}

import unittest

from community.adapters import AdapterError, StyioAdapter, StyioViewAdapter
from community.adapters import adapter_for_repository
from community.contracts import (
    CONTRACT_SCHEMAS,
    IDE_CAPABILITY_GAP_EVENT,
    SYNTAX_CHANGE_EVENT,
    ContractValidationError,
    IDECapabilityGapPayload,
    SyntaxChangePayload,
)


class ContractTests(unittest.TestCase):
    def test_syntax_payload_normalizes_and_exports_mapping(self):
        payload = SyntaxChangePayload.from_mapping(
            {
                "title": "  Add match guards  ",
                "syntax_area": " parser ",
                "summary": "Allow guard clauses on match cases.",
                "examples": [" case Foo if ready => ok "],
                "affected_components": [" grammar ", " formatter "],
            }
        )

        self.assertEqual(payload.title, "Add match guards")
        self.assertEqual(payload.syntax_area, "parser")
        self.assertEqual(payload.examples, ("case Foo if ready => ok",))
        self.assertEqual(payload.affected_components, ("grammar", "formatter"))
        self.assertEqual(
            payload.to_mapping()["examples"],
            ["case Foo if ready => ok"],
        )

    def test_payload_schemas_expose_required_fields(self):
        syntax_schema = CONTRACT_SCHEMAS[SYNTAX_CHANGE_EVENT]
        ide_schema = CONTRACT_SCHEMAS[IDE_CAPABILITY_GAP_EVENT]

        self.assertEqual(syntax_schema["type"], "object")
        self.assertFalse(syntax_schema["additionalProperties"])
        self.assertIn("syntax_area", syntax_schema["required"])
        self.assertIn("expected_behavior", ide_schema["required"])

    def test_payload_rejects_unknown_fields(self):
        with self.assertRaises(ContractValidationError):
            IDECapabilityGapPayload.from_mapping(
                {
                    "capability": "Diagnostics",
                    "current_behavior": "No squiggles are shown.",
                    "expected_behavior": "Syntax errors are highlighted.",
                    "impact": "Users miss parser failures.",
                    "state_machine_action": "advance",
                }
            )


class AdapterTests(unittest.TestCase):
    def test_styio_view_adapter_wraps_syntax_change_request(self):
        request = StyioViewAdapter().wrap_node_payload(
            node_id="decision-001",
            event_type=SYNTAX_CHANGE_EVENT,
            payload={
                "title": "Add match guards",
                "syntax_area": "parser",
                "summary": "Allow guard clauses on match cases.",
                "rationale": "Keeps control flow local to the match arm.",
                "examples": ["case Foo if ready => ok"],
                "affected_components": ["grammar", "formatter"],
            },
        )

        self.assertEqual(request.repository, "styio-view")
        self.assertEqual(request.title, "[syntax-adaptation] Add match guards")
        self.assertIn("syntax-change", request.labels)
        self.assertIn("syntax-adaptation", request.labels)
        self.assertEqual(request.metadata["node_id"], "decision-001")
        self.assertEqual(request.metadata["payload_schema"], SYNTAX_CHANGE_EVENT)
        self.assertIn("## Syntax area\n\nparser", request.body)
        self.assertIn("- formatter", request.body)

    def test_styio_adapter_wraps_ide_gap_request(self):
        request = StyioAdapter().wrap_event(
            {
                "node_id": "decision-002",
                "event_type": IDE_CAPABILITY_GAP_EVENT,
                "payload": IDECapabilityGapPayload(
                    capability="Inline parser diagnostics",
                    current_behavior="Errors are only visible in build output.",
                    expected_behavior="The editor marks syntax errors inline.",
                    impact="Authors cannot fix syntax mistakes in context.",
                    reproduction_steps=(
                        "Open a file with an invalid match arm.",
                        "Observe the editor surface.",
                    ),
                ),
                "state": "approved",
            }
        )

        self.assertEqual(request.repository, "styio")
        self.assertEqual(request.title, "[ide-gap] Inline parser diagnostics")
        self.assertIn("ide-capability-gap", request.labels)
        self.assertEqual(request.metadata["event_type"], IDE_CAPABILITY_GAP_EVENT)
        self.assertNotIn("state", request.metadata)
        self.assertIn("## Expected behavior", request.body)
        self.assertIn("- Open a file with an invalid match arm.", request.body)

    def test_adapter_rejects_unsupported_event_type(self):
        with self.assertRaises(AdapterError):
            StyioAdapter().wrap_node_payload(
                node_id="decision-003",
                event_type=SYNTAX_CHANGE_EVENT,
                payload={
                    "title": "Add match guards",
                    "syntax_area": "parser",
                    "summary": "Allow guard clauses on match cases.",
                },
            )

    def test_adapter_factory_selects_repository_adapter(self):
        self.assertIsInstance(adapter_for_repository("styio"), StyioAdapter)
        self.assertIsInstance(adapter_for_repository("styio-view"), StyioViewAdapter)

        with self.assertRaises(AdapterError):
            adapter_for_repository("styio-nightly")


if __name__ == "__main__":
    unittest.main()

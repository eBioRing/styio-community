import json
import tempfile
import unittest
from pathlib import Path

from community.storage import ConflictError, JsonRecordStore, ValidationError, build_dispatch_payload


class JsonRecordStoreTest(unittest.TestCase):
    def make_store(self, path: Path) -> JsonRecordStore:
        times = iter(
            [
                "2026-04-24T00:00:00Z",
                "2026-04-24T00:01:00Z",
                "2026-04-24T00:02:00Z",
            ]
        )
        return JsonRecordStore(path, clock=lambda: next(times), id_factory=lambda: "demo-1")

    def test_create_demo_record_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "records.json"
            record = self.make_store(path).create_demo_syntax_change()

            self.assertEqual(record["id"], "demo-1")
            self.assertEqual(record["kind"], "syntax-change")
            self.assertEqual(record["status"], "awaiting_decision")
            self.assertEqual(record["source_repository"], "styio")
            self.assertEqual(record["target_repository"], "styio-view")
            self.assertEqual(record["history"][0]["event"], "detected")
            self.assertEqual(record["history"][1]["event"], "awaiting_decision")

            reloaded = JsonRecordStore(path).list_records()
            self.assertEqual(len(reloaded), 1)
            self.assertEqual(reloaded[0]["title"], record["title"])

    def test_decision_requires_opinion_and_records_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self.make_store(Path(tmpdir) / "records.json")
            store.create_demo_syntax_change()

            with self.assertRaises(ValidationError):
                store.decide_record("demo-1", "approved", " ")

            approved = store.decide_record("demo-1", "approved", "Small enough to trial behind an adapter flag.")
            self.assertEqual(approved["status"], "approved")
            self.assertEqual(approved["decision"]["state"], "approved")
            self.assertEqual(approved["decision"]["opinion"], "Small enough to trial behind an adapter flag.")
            self.assertEqual(
                [event["event"] for event in approved["history"]],
                ["detected", "awaiting_decision", "approved"],
            )

    def test_decision_is_not_overwritten_after_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self.make_store(Path(tmpdir) / "records.json")
            store.create_demo_syntax_change()
            approved = store.decide_record("demo-1", "approved", "First pass approval.")

            with self.assertRaises(ConflictError):
                store.decide_record("demo-1", "rejected", "Needs a clearer migration story.")

            self.assertEqual(approved["status"], "approved")
            self.assertEqual(store.get_record("demo-1")["decision"]["state"], "approved")

    def test_dispatch_requires_approval_and_stores_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self.make_store(Path(tmpdir) / "records.json")
            store.create_demo_syntax_change()

            with self.assertRaises(ConflictError):
                store.dispatch_record("demo-1")

            store.decide_record("demo-1", "approved", "Ready for adapter trial.")
            dispatched = store.dispatch_record("demo-1", adapter_result={"adapter": "test", "accepted": True})

            self.assertEqual(dispatched["status"], "dispatched")
            self.assertEqual(dispatched["dispatch"]["result"]["adapter"], "test")
            self.assertEqual(dispatched["dispatch"]["payload"]["record_id"], "demo-1")
            self.assertEqual(dispatched["dispatch"]["payload"]["event_type"], "syntax_change")
            self.assertEqual(dispatched["dispatch"]["payload"]["repository"], "styio-view")
            self.assertEqual(dispatched["history"][-1]["event"], "dispatched")

            with self.assertRaises(ConflictError):
                store.decide_record("demo-1", "rejected", "Too late.")

    def test_dispatch_payload_is_adapter_facing_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self.make_store(Path(tmpdir) / "records.json")
            store.create_demo_syntax_change()
            approved = store.decide_record("demo-1", "approved", "Ready.")

            payload = build_dispatch_payload(approved)

            self.assertEqual(payload["schema_version"], "styio.community.decision.v1")
            self.assertEqual(payload["node_id"], "demo-1")
            self.assertEqual(payload["event_type"], "syntax_change")
            self.assertEqual(payload["repository"], "styio-view")
            self.assertEqual(payload["source_repository"], "styio")
            self.assertEqual(payload["payload"]["title"], "stdin return pipe shorthand")
            self.assertEqual(payload["decision"]["opinion"], "Ready.")
            json.dumps(payload)

    def test_demo_ide_gap_dispatch_targets_styio(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self.make_store(Path(tmpdir) / "records.json")
            record = store.create_demo_ide_gap()
            self.assertEqual(record["kind"], "ide-capability-gap")
            self.assertEqual(record["source_repository"], "styio-view")
            self.assertEqual(record["target_repository"], "styio")

            approved = store.decide_record("demo-1", "approved", "Send upstream.")
            payload = build_dispatch_payload(approved)

            self.assertEqual(payload["event_type"], "ide_capability_gap")
            self.assertEqual(payload["repository"], "styio")
            self.assertEqual(payload["payload"]["capability"], "Inline return-pipe diagnostics")


if __name__ == "__main__":
    unittest.main()

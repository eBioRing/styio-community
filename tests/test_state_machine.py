import unittest

from community.state_machine import (
    DecisionAction,
    InvalidTransition,
    SerializationError,
    State,
    StateMachineError,
    WorkflowNode,
)


class WorkflowNodeTests(unittest.TestCase):
    def test_approve_dispatch_complete_records_history_and_events(self):
        node = WorkflowNode.create(
            "issue-123",
            payload={"source": "discussion", "external": {"id": 123}},
            actor="scanner",
        )

        node.request_decision(reason="needs maintainer review", actor="triage")
        decision = node.approve("Ship the minimal adapter-neutral flow.", actor="maintainer")
        node.dispatch(reason="queued for worker", actor="dispatcher", data={"queue": "default"})
        node.complete(reason="worker finished", actor="worker")

        self.assertEqual(node.state, State.COMPLETED)
        self.assertTrue(node.is_terminal)
        self.assertEqual(decision.action, DecisionAction.APPROVE)
        self.assertEqual(decision.opinion, "Ship the minimal adapter-neutral flow.")
        self.assertEqual([item.to_state for item in node.history], [
            State.AWAITING_DECISION,
            State.APPROVED,
            State.DISPATCHED,
            State.COMPLETED,
        ])
        self.assertEqual(node.events[0].name, "node.detected")
        self.assertEqual(node.events[-1].name, "node.completed")
        self.assertEqual(node.events[-2].data["queue"], "default")

    def test_reject_decision_is_terminal_with_opinion_text(self):
        node = WorkflowNode.create("proposal-1")

        node.request_decision(actor="triage")
        decision = node.reject("The proposal does not meet the current policy.", actor="reviewer")

        self.assertEqual(node.state, State.REJECTED)
        self.assertTrue(node.is_terminal)
        self.assertEqual(decision.action, DecisionAction.REJECT)
        self.assertEqual(node.decisions[0].opinion, "The proposal does not meet the current policy.")
        self.assertEqual(node.history[-1].event, "decision.reject")

    def test_invalid_transitions_do_not_mutate_node(self):
        node = WorkflowNode.create("proposal-2")

        with self.assertRaises(InvalidTransition):
            node.dispatch(actor="dispatcher")

        self.assertEqual(node.state, State.DETECTED)
        self.assertEqual(node.history, [])
        self.assertEqual(len(node.events), 1)

        with self.assertRaises(InvalidTransition):
            node.approve("Skipping review should fail.", actor="reviewer")

        self.assertEqual(node.state, State.DETECTED)
        self.assertEqual(node.decisions, [])

    def test_decisions_require_non_empty_opinion(self):
        node = WorkflowNode.create("proposal-3")
        node.request_decision()

        with self.assertRaises(StateMachineError):
            node.approve("   ", actor="reviewer")

        self.assertEqual(node.state, State.AWAITING_DECISION)
        self.assertEqual(node.decisions, [])
        self.assertEqual(len(node.history), 1)

    def test_generic_transition_cannot_bypass_decision_record(self):
        node = WorkflowNode.create("proposal-3b")
        node.request_decision()

        with self.assertRaises(InvalidTransition):
            node.transition_to(State.APPROVED, reason="no recorded opinion")

        self.assertEqual(node.state, State.AWAITING_DECISION)
        self.assertEqual(node.decisions, [])

    def test_blocked_nodes_can_return_to_decision(self):
        node = WorkflowNode.create("proposal-4")

        node.block("missing evidence", actor="reviewer")
        self.assertEqual(node.state, State.BLOCKED)
        self.assertIn(State.AWAITING_DECISION, node.allowed_next_states())

        node.request_decision(reason="evidence supplied", actor="author")
        node.reject("Still incomplete.", actor="reviewer")

        self.assertEqual(node.state, State.REJECTED)
        self.assertEqual([item.to_state for item in node.history], [
            State.BLOCKED,
            State.AWAITING_DECISION,
            State.REJECTED,
        ])

    def test_serialization_round_trips_plain_dicts(self):
        node = WorkflowNode.create(
            "proposal-5",
            payload={"adapter_payload": {"kind": "unknown", "refs": [1, 2]}},
            metadata={"priority": "normal"},
        )
        node.request_decision(reason="review required")
        node.approve("Looks correct.", actor="reviewer")

        serialized = node.to_dict()
        restored = WorkflowNode.from_dict(serialized)

        self.assertEqual(restored.to_dict(), serialized)
        self.assertEqual(restored.state, State.APPROVED)
        self.assertEqual(restored.payload["adapter_payload"]["kind"], "unknown")
        self.assertEqual(restored.decisions[0].action, DecisionAction.APPROVE)

        serialized["payload"]["adapter_payload"]["kind"] = "mutated"
        self.assertEqual(restored.payload["adapter_payload"]["kind"], "unknown")

    def test_unknown_serialized_state_is_rejected(self):
        with self.assertRaises(SerializationError):
            WorkflowNode.from_dict({"node_id": "bad", "state": "waiting_for_magic"})


if __name__ == "__main__":
    unittest.main()

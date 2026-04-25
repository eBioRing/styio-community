# Styio Community Decision Framework

**Purpose:** Define the minimal decision workflow for coordinating upstream Styio changes with downstream repositories without making GitHub issues the source of truth.

**Last updated:** 2026-04-24

## Boundary

`styio-community` owns coordination records and workflow state. It does not own
Styio language semantics, `styio-view` product decisions, or implementation
details inside downstream repositories.

## First Workflow

The first supported workflow is `syntax_change_adaptation`:

1. `styio` lands a syntax change through its normal documentation and gate flow.
2. `styio-community` records a syntax-change node in `detected`.
3. The node moves to `awaiting_decision` for a human decision.
4. A coordinator approves or rejects the request with written execution opinion.
5. If approved, the adapter layer translates the node into a repository-facing
   request for `styio-view`; the syntax-change adapter is owned by
   `StyioViewAdapter`.
6. `styio-view` can either complete the adaptation or send back an IDE capability
   gap for `styio`; the IDE-gap adapter is owned by `StyioAdapter`.

## Architectural Rule

The state machine only knows generic nodes, states, transitions, and decisions.
Adapters translate node payloads into repository-specific requests. A repository
adapter may choose GitHub issues, pull requests, webhooks, or a future private
transport, but that transport is not the coordination source of truth.

## Adapter Direction

- `syntax_change`: source `styio`, target `styio-view`.
- `ide_capability_gap`: source `styio-view`, target `styio`.

## Minimal States

- `detected`
- `awaiting_decision`
- `approved`
- `dispatched`
- `blocked`
- `completed`
- `rejected`

## Decision Evidence

Approval requires written execution opinion. The opinion is stored on the
coordination record before any downstream dispatch happens.

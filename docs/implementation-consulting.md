# Implementation Consulting Notes

## Assigned Roles

| Role | Decision |
|---|---|
| Architecture | Layered `DIV -> Adapter -> DAACS` integration |
| Migration | Create schema and adapter before moving source code |
| Verification/Risk | Secret redaction, evidence boundary, and claim gate first |
| Quantitative Measurement | Record reuse candidates and test gaps |
| Portfolio/README | Present as AI Agent Workflow Harness, not full autonomous platform |

## Main Decision

The two projects should become one portfolio project only through a shared harness contract. The original apps should not be copied together as-is.

## MVP Success Criteria

- A natural language idea becomes an `IdeaBrief`.
- Planner output becomes a `PlanningBlueprint`.
- Adapter creates a `BuildSpec`.
- Builder returns a `VerificationReport`.
- Artifacts are stored under the same run id.
- Tests cover schema, adapter, redaction, evidence, claim, and smoke workflow.


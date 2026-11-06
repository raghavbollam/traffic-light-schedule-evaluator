"""Verify an agent's submitted traffic evaluation deterministically."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from contract import (
    ArrivalEvaluation,
    TrafficScheduleInput,
    TrafficScheduleOutput,
)

from .rules import build_evaluations, validate_evaluations


@dataclass(frozen=True)
class VerificationResult:
    """The deterministic verdict for one submitted task answer."""

    ok: bool
    score: float
    message: str
    errors: list[str]


def _describe(evaluation: ArrivalEvaluation) -> str:
    return (
        f"intersection={evaluation.intersection_id!r}, "
        f"arrival_time={evaluation.arrival_time}, "
        f"signal_color={evaluation.signal_color!r}, "
        f"may_cross={evaluation.may_cross}, "
        f"next_crossing_time={evaluation.next_crossing_time}, "
        f"wait_seconds={evaluation.wait_seconds}"
    )


def verify_task(
    arguments: TrafficScheduleInput,
    output: TrafficScheduleOutput,
    reference: object | None,
    workspace: Path,
) -> VerificationResult:
    """Compare a submitted report with independently calculated evaluations."""

    del reference, workspace

    try:
        expected = build_evaluations(arguments)
        validate_evaluations(output.evaluations)
    except (TypeError, ValueError) as error:
        return VerificationResult(
            ok=False,
            score=0.0,
            message="The traffic task or submitted evaluation is invalid.",
            errors=[str(error)],
        )

    errors: list[str] = []
    expected_by_id = {entry.arrival_id: entry for entry in expected}
    actual_by_id = {entry.arrival_id: entry for entry in output.evaluations}

    for arrival_id in expected_by_id.keys() - actual_by_id.keys():
        errors.append(f"Missing evaluation for arrival {arrival_id!r}.")
    for arrival_id in actual_by_id.keys() - expected_by_id.keys():
        errors.append(f"Unexpected evaluation for arrival {arrival_id!r}.")

    for arrival_id in expected_by_id.keys() & actual_by_id.keys():
        expected_entry = expected_by_id[arrival_id]
        actual_entry = actual_by_id[arrival_id]
        if actual_entry != expected_entry:
            errors.append(
                f"Evaluation for arrival {arrival_id!r} does not match. "
                f"Expected ({_describe(expected_entry)}); "
                f"received ({_describe(actual_entry)})."
            )

    expected_ids = [entry.arrival_id for entry in expected]
    actual_ids = [entry.arrival_id for entry in output.evaluations]
    if not errors and actual_ids != expected_ids:
        errors.append(
            "Evaluations are not in arrival input order. "
            f"Expected {expected_ids!r}."
        )

    if errors:
        return VerificationResult(
            ok=False,
            score=0.0,
            message="The submitted traffic evaluation did not match the schedules.",
            errors=sorted(errors),
        )

    return VerificationResult(
        ok=True,
        score=1.0,
        message="Every arrival has the correct signal and next crossing time.",
        errors=[],
    )

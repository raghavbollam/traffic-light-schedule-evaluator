"""Tools that inspect traffic schedules and save arrival evaluations."""

from __future__ import annotations

import json
from pathlib import Path

from slimconfig import plain_output

from contract import (
    ReadTrafficRequestInput,
    ReadTrafficRequestOutput,
    TrafficScheduleOutput,
    WriteTrafficEvaluationInput,
    WriteTrafficEvaluationOutput,
)
from verifier.rules import REPORT_NAME, validate_evaluations, validate_traffic_input


def read_traffic_request(
    given: ReadTrafficRequestInput,
    workspace: Path,
) -> ReadTrafficRequestOutput:
    """Return the validated schedules and arrivals for the task."""

    del workspace
    validate_traffic_input(given.task)
    return ReadTrafficRequestOutput(
        intersections=given.task.intersections,
        arrivals=given.task.arrivals,
    )


def write_traffic_evaluation(
    given: WriteTrafficEvaluationInput,
    workspace: Path,
) -> WriteTrafficEvaluationOutput:
    """Write the agent's final structured traffic evaluation."""

    validate_traffic_input(given.task)
    validate_evaluations(given.evaluations)

    report = TrafficScheduleOutput(evaluations=given.evaluations)
    report_path = Path(workspace) / REPORT_NAME
    report_path.write_text(
        json.dumps(plain_output(report), indent=2) + "\n",
        encoding="utf-8",
    )

    return WriteTrafficEvaluationOutput(
        report_path=REPORT_NAME,
        report=report,
    )

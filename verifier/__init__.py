"""Deterministic verifier entry points for the traffic schedule evaluator."""

import json
from pathlib import Path

from contract import (
    ReadTrafficRequestOutput,
    Task,
    Tool,
    TrafficScheduleOutput,
)

from .rules import REPORT_NAME, validate_evaluations, validate_traffic_input
from .task import verify_task as verify_traffic_schedule


def result(valid, message, *, score=None, **details):
    """Return a NanoAgent v0001 verifier result."""

    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def serialize_report(report: TrafficScheduleOutput) -> dict[str, list[dict[str, object]]]:
    """Convert a report to the JSON representation written by the tool."""

    return {
        "evaluations": [
            {
                "arrival_id": entry.arrival_id,
                "intersection_id": entry.intersection_id,
                "arrival_time": entry.arrival_time,
                "signal_color": entry.signal_color,
                "may_cross": entry.may_cross,
                "next_crossing_time": entry.next_crossing_time,
                "wait_seconds": entry.wait_seconds,
            }
            for entry in report.evaluations
        ]
    }


def verify_input(tool, value):
    """Validate tool inputs against the deterministic task rules."""

    selected_tool = Tool(tool)
    try:
        validate_traffic_input(value.task)
        if selected_tool is Tool.READ_TRAFFIC_REQUEST:
            return result(True, "The traffic request is valid.")
        validate_evaluations(value.evaluations)
    except (TypeError, ValueError) as error:
        return result(False, "The tool input is invalid.", errors=[str(error)])

    return result(True, "The submitted evaluations are structurally valid.")


def verify_output(tool, input_value, output_value, workspace):
    """Validate that each tool returns the value specified by its contract."""

    if Tool(tool) is Tool.READ_TRAFFIC_REQUEST:
        expected = ReadTrafficRequestOutput(
            intersections=input_value.task.intersections,
            arrivals=input_value.task.arrivals,
        )
        valid = output_value == expected
        return result(
            valid,
            "The traffic request was read correctly."
            if valid
            else "The traffic request output did not match the task.",
        )

    expected = TrafficScheduleOutput(evaluations=input_value.evaluations)
    expected_report = serialize_report(expected)
    report_file = Path(workspace) / REPORT_NAME

    try:
        written_report = json.loads(report_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return result(
            False,
            "The traffic evaluation was not written.",
            errors=[f"{REPORT_NAME} is missing."],
        )
    except json.JSONDecodeError as error:
        return result(
            False,
            "The traffic evaluation is not valid JSON.",
            errors=[f"{REPORT_NAME} could not be decoded: {error.msg}."],
        )

    valid = (
        output_value.report_path == REPORT_NAME
        and output_value.report == expected
        and written_report == expected_report
    )
    return result(
        valid,
        "The traffic evaluation was written correctly."
        if valid
        else "The written report did not match the submitted evaluations.",
        errors=[]
        if valid
        else [f"{REPORT_NAME} or the returned report differs from the submission."],
    )


def verify_task(task, arguments, output, reference, workspace):
    """Verify final task output against independently calculated schedules."""

    verdict = verify_traffic_schedule(
        arguments,
        output,
        reference,
        Path(workspace),
    )
    return result(
        verdict.ok,
        verdict.message,
        score=verdict.score,
        errors=verdict.errors,
        task=Task(task).value,
    )

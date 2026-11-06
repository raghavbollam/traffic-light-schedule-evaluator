from pathlib import Path

from contract import (
    ArrivalEvaluation,
    IntersectionSchedule,
    ReadTrafficRequestInput,
    Task,
    Tool,
    TrafficScheduleInput,
    TrafficScheduleOutput,
    VehicleArrival,
    WriteTrafficEvaluationInput,
    WriteTrafficEvaluationOutput,
)
from plugin.tools import write_traffic_evaluation
from verifier import verify_input, verify_output
from verifier import verify_task as verify_registered_task
from verifier.rules import build_evaluations
from verifier.task import verify_task


def prepare_task() -> TrafficScheduleInput:
    return TrafficScheduleInput(
        intersections=[
            IntersectionSchedule("north", 0, 30, 5, 25),
            IntersectionSchedule("east", 10, 10, 2, 8),
        ],
        arrivals=[
            VehicleArrival("green-arrival", "north", 29),
            VehicleArrival("yellow-boundary", "north", 30),
            VehicleArrival("red-arrival", "east", 22),
        ],
    )


def test_verifier_accepts_correct_evaluation(tmp_path: Path) -> None:
    traffic_task = prepare_task()
    output = TrafficScheduleOutput(
        evaluations=build_evaluations(traffic_task),
    )

    result = verify_task(traffic_task, output, reference=None, workspace=tmp_path)

    assert result.ok is True
    assert result.score == 1.0
    assert result.errors == []


def test_verifier_rejects_wrong_phase_and_crossing_time(tmp_path: Path) -> None:
    traffic_task = prepare_task()
    evaluations = build_evaluations(traffic_task)
    evaluations[1] = ArrivalEvaluation(
        "yellow-boundary",
        "north",
        30,
        "red",
        False,
        61,
        31,
    )

    result = verify_task(
        traffic_task,
        TrafficScheduleOutput(evaluations),
        reference=None,
        workspace=tmp_path,
    )

    assert result.ok is False
    assert result.score == 0.0
    assert "does not match" in result.errors[0]
    assert "yellow-boundary" in result.errors[0]


def test_verifier_rejects_missing_and_extra_evaluations(tmp_path: Path) -> None:
    traffic_task = prepare_task()
    output = TrafficScheduleOutput(
        evaluations=[
            ArrivalEvaluation(
                "unexpected",
                "north",
                1,
                "green",
                True,
                1,
                0,
            )
        ]
    )

    result = verify_task(
        traffic_task,
        output,
        reference=None,
        workspace=tmp_path,
    )

    assert result.ok is False
    assert any("Missing evaluation" in error for error in result.errors)
    assert any("Unexpected evaluation" in error for error in result.errors)


def test_verifier_rejects_reordered_evaluations(tmp_path: Path) -> None:
    traffic_task = prepare_task()
    evaluations = build_evaluations(traffic_task)

    result = verify_task(
        traffic_task,
        TrafficScheduleOutput(list(reversed(evaluations))),
        reference=None,
        workspace=tmp_path,
    )

    assert result.ok is False
    assert result.errors == [
        (
            "Evaluations are not in arrival input order. "
            "Expected ['green-arrival', 'yellow-boundary', 'red-arrival']."
        )
    ]


def test_registered_verifier_dispatches_to_task_verifier(tmp_path: Path) -> None:
    traffic_task = prepare_task()

    result = verify_registered_task(
        Task.EVALUATE_TRAFFIC_SCHEDULE.value,
        traffic_task,
        TrafficScheduleOutput(build_evaluations(traffic_task)),
        reference=None,
        workspace=tmp_path,
    )

    assert result["valid"] is True
    assert result["score"] == 1.0


def test_read_request_input_verifier_rejects_invalid_duration() -> None:
    traffic_task = prepare_task()
    traffic_task.intersections[0].yellow_seconds = 0

    result = verify_input(
        Tool.READ_TRAFFIC_REQUEST.value,
        ReadTrafficRequestInput(task=traffic_task),
    )

    assert result["valid"] is False
    assert "positive integer" in result["details"]["errors"][0]


def test_write_output_verifier_requires_persisted_report(tmp_path: Path) -> None:
    traffic_task = prepare_task()
    evaluations = build_evaluations(traffic_task)
    input_value = WriteTrafficEvaluationInput(traffic_task, evaluations)
    output_value = WriteTrafficEvaluationOutput(
        report_path="traffic-evaluation.json",
        report=TrafficScheduleOutput(evaluations),
    )

    result = verify_output(
        Tool.WRITE_TRAFFIC_EVALUATION.value,
        input_value,
        output_value,
        tmp_path,
    )

    assert result["valid"] is False
    assert result["details"]["errors"] == ["traffic-evaluation.json is missing."]


def test_write_output_verifier_accepts_persisted_report(tmp_path: Path) -> None:
    traffic_task = prepare_task()
    evaluations = build_evaluations(traffic_task)
    input_value = WriteTrafficEvaluationInput(traffic_task, evaluations)
    output_value = write_traffic_evaluation(input_value, tmp_path)

    result = verify_output(
        Tool.WRITE_TRAFFIC_EVALUATION.value,
        input_value,
        output_value,
        str(tmp_path),
    )

    assert result["valid"] is True

import json
from pathlib import Path

from contract import (
    IntersectionSchedule,
    ReadTrafficRequestInput,
    TrafficScheduleInput,
    VehicleArrival,
    WriteTrafficEvaluationInput,
)
from plugin.tools import read_traffic_request, write_traffic_evaluation
from verifier.rules import build_evaluations


def prepare_task() -> TrafficScheduleInput:
    return TrafficScheduleInput(
        intersections=[
            IntersectionSchedule(
                intersection_id="main",
                cycle_start=0,
                green_seconds=30,
                yellow_seconds=5,
                red_seconds=25,
            )
        ],
        arrivals=[
            VehicleArrival("vehicle-green", "main", 12),
            VehicleArrival("vehicle-red", "main", 44),
        ],
    )


def test_read_traffic_request_returns_validated_task_data(tmp_path: Path) -> None:
    traffic_task = prepare_task()

    result = read_traffic_request(
        ReadTrafficRequestInput(task=traffic_task),
        tmp_path,
    )

    assert result.intersections == traffic_task.intersections
    assert result.arrivals == traffic_task.arrivals


def test_write_traffic_evaluation_saves_structured_json_report(
    tmp_path: Path,
) -> None:
    traffic_task = prepare_task()
    evaluations = build_evaluations(traffic_task)

    result = write_traffic_evaluation(
        WriteTrafficEvaluationInput(
            task=traffic_task,
            evaluations=evaluations,
        ),
        tmp_path,
    )

    assert result.report_path == "traffic-evaluation.json"
    assert result.report.evaluations == evaluations
    assert json.loads(
        (tmp_path / "traffic-evaluation.json").read_text(encoding="utf-8")
    ) == {
        "evaluations": [
            {
                "arrival_id": "vehicle-green",
                "intersection_id": "main",
                "arrival_time": 12,
                "signal_color": "green",
                "may_cross": True,
                "next_crossing_time": 12,
                "wait_seconds": 0,
            },
            {
                "arrival_id": "vehicle-red",
                "intersection_id": "main",
                "arrival_time": 44,
                "signal_color": "red",
                "may_cross": False,
                "next_crossing_time": 60,
                "wait_seconds": 16,
            },
        ]
    }

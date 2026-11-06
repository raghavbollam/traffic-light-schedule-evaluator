import json
from pathlib import Path

import pytest

from contract import (
    ArrivalEvaluation,
    IntersectionSchedule,
    TrafficScheduleInput,
    VehicleArrival,
)
from verifier.rules import (
    build_evaluations,
    evaluate_arrival,
    validate_evaluations,
    validate_traffic_input,
)


def schedule(
    *,
    intersection_id: str = "main",
    cycle_start: int = 0,
    green_seconds: int = 30,
    yellow_seconds: int = 5,
    red_seconds: int = 25,
) -> IntersectionSchedule:
    return IntersectionSchedule(
        intersection_id=intersection_id,
        cycle_start=cycle_start,
        green_seconds=green_seconds,
        yellow_seconds=yellow_seconds,
        red_seconds=red_seconds,
    )


def arrival(
    arrival_time: int,
    *,
    arrival_id: str = "vehicle-1",
    intersection_id: str = "main",
) -> VehicleArrival:
    return VehicleArrival(
        arrival_id=arrival_id,
        intersection_id=intersection_id,
        arrival_time=arrival_time,
    )


def task(
    *,
    intersections: list[IntersectionSchedule] | None = None,
    arrivals: list[VehicleArrival] | None = None,
) -> TrafficScheduleInput:
    return TrafficScheduleInput(
        intersections=[schedule()] if intersections is None else intersections,
        arrivals=[arrival(0)] if arrivals is None else arrivals,
    )


@pytest.mark.parametrize(
    ("arrival_time", "color", "next_crossing", "wait"),
    [
        (0, "green", 0, 0),
        (29, "green", 29, 0),
        (30, "yellow", 60, 30),
        (34, "yellow", 60, 26),
        (35, "red", 60, 25),
        (59, "red", 60, 1),
        (60, "green", 60, 0),
        (120, "green", 120, 0),
    ],
)
def test_evaluate_arrival_handles_phase_boundaries(
    arrival_time: int,
    color: str,
    next_crossing: int,
    wait: int,
) -> None:
    result = evaluate_arrival(schedule(), arrival(arrival_time))

    assert result.signal_color == color
    assert result.may_cross is (color == "green")
    assert result.next_crossing_time == next_crossing
    assert result.wait_seconds == wait


def test_cycle_start_offsets_the_repeating_schedule() -> None:
    shifted = schedule(cycle_start=10)

    assert evaluate_arrival(shifted, arrival(9)).signal_color == "red"
    assert evaluate_arrival(shifted, arrival(10)).signal_color == "green"
    assert evaluate_arrival(shifted, arrival(40)).signal_color == "yellow"


def test_build_evaluations_supports_multiple_intersections_and_preserves_order() -> None:
    traffic_task = task(
        intersections=[
            schedule(intersection_id="north"),
            schedule(
                intersection_id="east",
                cycle_start=10,
                green_seconds=10,
                yellow_seconds=2,
                red_seconds=8,
            ),
        ],
        arrivals=[
            arrival(22, arrival_id="east-first", intersection_id="east"),
            arrival(5, arrival_id="north-second", intersection_id="north"),
        ],
    )

    evaluations = build_evaluations(traffic_task)

    assert [entry.arrival_id for entry in evaluations] == [
        "east-first",
        "north-second",
    ]
    assert evaluations[0].signal_color == "red"
    assert evaluations[0].next_crossing_time == 30
    assert evaluations[1].signal_color == "green"


def test_repository_fixture_matches_expected_evaluation() -> None:
    fixtures = Path(__file__).parent / "fixtures"
    input_data = json.loads(
        (fixtures / "basic-case-input.json").read_text(encoding="utf-8")
    )
    expected_data = json.loads(
        (fixtures / "basic-case-expected.json").read_text(encoding="utf-8")
    )
    traffic_task = TrafficScheduleInput(
        intersections=[
            IntersectionSchedule(**value) for value in input_data["intersections"]
        ],
        arrivals=[VehicleArrival(**value) for value in input_data["arrivals"]],
    )

    actual = build_evaluations(traffic_task)

    assert [
        {
            "arrival_id": entry.arrival_id,
            "intersection_id": entry.intersection_id,
            "arrival_time": entry.arrival_time,
            "signal_color": entry.signal_color,
            "may_cross": entry.may_cross,
            "next_crossing_time": entry.next_crossing_time,
            "wait_seconds": entry.wait_seconds,
        }
        for entry in actual
    ] == expected_data["evaluations"]


@pytest.mark.parametrize(
    ("traffic_task", "message"),
    [
        (task(intersections=[]), "at least one schedule"),
        (task(arrivals=[]), "at least one vehicle"),
        (
            task(intersections=[schedule(green_seconds=0)]),
            "positive integer",
        ),
        (
            task(intersections=[schedule(cycle_start=-1)]),
            "non-negative integer",
        ),
        (
            task(
                intersections=[
                    schedule(intersection_id="same"),
                    schedule(intersection_id="same"),
                ]
            ),
            "duplicate id",
        ),
        (
            task(
                arrivals=[
                    arrival(1, arrival_id="same"),
                    arrival(2, arrival_id="same"),
                ]
            ),
            "duplicate id",
        ),
        (
            task(arrivals=[arrival(1, intersection_id="unknown")]),
            "unknown intersection",
        ),
        (
            task(arrivals=[arrival(True)]),
            "non-negative integer",
        ),
        (
            task(intersections=[schedule(intersection_id="bad id")]),
            "1-64 letters",
        ),
    ],
)
def test_validate_traffic_input_rejects_malformed_tasks(
    traffic_task: TrafficScheduleInput,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_traffic_input(traffic_task)


def test_validate_evaluations_rejects_inconsistent_wait_and_crossing_values() -> None:
    with pytest.raises(ValueError, match="must equal"):
        validate_evaluations(
            [
                ArrivalEvaluation(
                    "vehicle-1",
                    "main",
                    30,
                    "yellow",
                    False,
                    60,
                    29,
                )
            ]
        )

    with pytest.raises(ValueError, match="exactly when"):
        validate_evaluations(
            [
                ArrivalEvaluation(
                    "vehicle-1",
                    "main",
                    1,
                    "green",
                    False,
                    1,
                    0,
                )
            ]
        )


def test_validate_evaluations_rejects_duplicates_and_unknown_color() -> None:
    valid = ArrivalEvaluation("vehicle-1", "main", 0, "green", True, 0, 0)

    with pytest.raises(ValueError, match="duplicate arrival id"):
        validate_evaluations([valid, valid])

    with pytest.raises(ValueError, match="green, yellow, or red"):
        validate_evaluations(
            [ArrivalEvaluation("vehicle-1", "main", 0, "blue", True, 0, 0)]
        )

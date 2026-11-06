"""Validate traffic schedules and evaluate repeating signal cycles."""

from __future__ import annotations

import re

from contract import (
    ArrivalEvaluation,
    IntersectionSchedule,
    TrafficScheduleInput,
    VehicleArrival,
)

REPORT_NAME = "traffic-evaluation.json"
SIGNAL_COLORS = {"green", "yellow", "red"}
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def _validate_identifier(value: str, *, label: str) -> None:
    if not isinstance(value, str) or IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError(
            f"{label} must be 1-64 letters, digits, '.', '_' or '-', "
            "starting with a letter or digit."
        )


def _validate_non_negative_integer(value: int, *, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer.")


def _validate_positive_integer(value: int, *, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer.")


def validate_traffic_input(task: TrafficScheduleInput) -> None:
    """Raise ValueError unless a traffic task is complete and unambiguous."""

    if not task.intersections:
        raise ValueError("intersections must contain at least one schedule.")
    if not task.arrivals:
        raise ValueError("arrivals must contain at least one vehicle arrival.")

    intersection_ids: set[str] = set()
    for index, schedule in enumerate(task.intersections):
        prefix = f"intersections[{index}]"
        _validate_identifier(
            schedule.intersection_id,
            label=f"{prefix}.intersection_id",
        )
        if schedule.intersection_id in intersection_ids:
            raise ValueError(
                f"intersections contains duplicate id {schedule.intersection_id!r}."
            )
        _validate_non_negative_integer(
            schedule.cycle_start,
            label=f"{prefix}.cycle_start",
        )
        _validate_positive_integer(
            schedule.green_seconds,
            label=f"{prefix}.green_seconds",
        )
        _validate_positive_integer(
            schedule.yellow_seconds,
            label=f"{prefix}.yellow_seconds",
        )
        _validate_positive_integer(
            schedule.red_seconds,
            label=f"{prefix}.red_seconds",
        )
        intersection_ids.add(schedule.intersection_id)

    arrival_ids: set[str] = set()
    for index, arrival in enumerate(task.arrivals):
        prefix = f"arrivals[{index}]"
        _validate_identifier(arrival.arrival_id, label=f"{prefix}.arrival_id")
        _validate_identifier(
            arrival.intersection_id,
            label=f"{prefix}.intersection_id",
        )
        if arrival.arrival_id in arrival_ids:
            raise ValueError(f"arrivals contains duplicate id {arrival.arrival_id!r}.")
        if arrival.intersection_id not in intersection_ids:
            raise ValueError(
                f"{prefix}.intersection_id references unknown intersection "
                f"{arrival.intersection_id!r}."
            )
        _validate_non_negative_integer(
            arrival.arrival_time,
            label=f"{prefix}.arrival_time",
        )
        arrival_ids.add(arrival.arrival_id)


def evaluate_arrival(
    schedule: IntersectionSchedule,
    arrival: VehicleArrival,
) -> ArrivalEvaluation:
    """Evaluate one arrival against a green-yellow-red repeating cycle."""

    cycle_seconds = (
        schedule.green_seconds + schedule.yellow_seconds + schedule.red_seconds
    )
    position = (arrival.arrival_time - schedule.cycle_start) % cycle_seconds

    if position < schedule.green_seconds:
        signal_color = "green"
        next_crossing_time = arrival.arrival_time
    elif position < schedule.green_seconds + schedule.yellow_seconds:
        signal_color = "yellow"
        next_crossing_time = arrival.arrival_time + cycle_seconds - position
    else:
        signal_color = "red"
        next_crossing_time = arrival.arrival_time + cycle_seconds - position

    wait_seconds = next_crossing_time - arrival.arrival_time
    return ArrivalEvaluation(
        arrival_id=arrival.arrival_id,
        intersection_id=arrival.intersection_id,
        arrival_time=arrival.arrival_time,
        signal_color=signal_color,
        may_cross=signal_color == "green",
        next_crossing_time=next_crossing_time,
        wait_seconds=wait_seconds,
    )


def build_evaluations(task: TrafficScheduleInput) -> list[ArrivalEvaluation]:
    """Return the canonical evaluation for every arrival in input order."""

    validate_traffic_input(task)
    schedules = {
        schedule.intersection_id: schedule for schedule in task.intersections
    }
    return [
        evaluate_arrival(schedules[arrival.intersection_id], arrival)
        for arrival in task.arrivals
    ]


def validate_evaluations(evaluations: list[ArrivalEvaluation]) -> None:
    """Raise ValueError unless submitted evaluations are structurally valid."""

    seen_arrivals: set[str] = set()
    for index, evaluation in enumerate(evaluations):
        prefix = f"evaluations[{index}]"
        _validate_identifier(evaluation.arrival_id, label=f"{prefix}.arrival_id")
        _validate_identifier(
            evaluation.intersection_id,
            label=f"{prefix}.intersection_id",
        )
        if evaluation.arrival_id in seen_arrivals:
            raise ValueError(
                f"evaluations contains duplicate arrival id "
                f"{evaluation.arrival_id!r}."
            )
        _validate_non_negative_integer(
            evaluation.arrival_time,
            label=f"{prefix}.arrival_time",
        )
        if evaluation.signal_color not in SIGNAL_COLORS:
            raise ValueError(
                f"{prefix}.signal_color must be green, yellow, or red."
            )
        if not isinstance(evaluation.may_cross, bool):
            raise TypeError(f"{prefix}.may_cross must be a boolean.")
        _validate_non_negative_integer(
            evaluation.next_crossing_time,
            label=f"{prefix}.next_crossing_time",
        )
        _validate_non_negative_integer(
            evaluation.wait_seconds,
            label=f"{prefix}.wait_seconds",
        )
        if evaluation.next_crossing_time < evaluation.arrival_time:
            raise ValueError(
                f"{prefix}.next_crossing_time must not precede arrival_time."
            )
        if (
            evaluation.next_crossing_time - evaluation.arrival_time
            != evaluation.wait_seconds
        ):
            raise ValueError(
                f"{prefix}.wait_seconds must equal next_crossing_time minus "
                "arrival_time."
            )
        if evaluation.may_cross != (evaluation.wait_seconds == 0):
            raise ValueError(
                f"{prefix}.may_cross must be true exactly when wait_seconds is zero."
            )
        seen_arrivals.add(evaluation.arrival_id)

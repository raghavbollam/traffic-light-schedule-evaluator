"""Each tool's and task's typed input and output: declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    READ_TRAFFIC_REQUEST = "read_traffic_request"
    WRITE_TRAFFIC_EVALUATION = "write_traffic_evaluation"


class Task(Enum):
    EVALUATE_TRAFFIC_SCHEDULE = "evaluate-traffic-schedule"


@dataclass
class IntersectionSchedule(Output):
    intersection_id: Annotated[str, "Unique identifier for the intersection."]
    cycle_start: Annotated[
        int,
        "Scenario time in whole seconds at which a green phase starts.",
    ]
    green_seconds: Annotated[int, "Positive whole-second green phase duration."]
    yellow_seconds: Annotated[int, "Positive whole-second yellow phase duration."]
    red_seconds: Annotated[int, "Positive whole-second red phase duration."]


@dataclass
class VehicleArrival(Output):
    arrival_id: Annotated[str, "Unique identifier for this vehicle arrival."]
    intersection_id: Annotated[str, "Intersection whose signal controls the vehicle."]
    arrival_time: Annotated[int, "Arrival time in whole seconds on the scenario clock."]


@dataclass
class TrafficScheduleInput(Output):
    intersections: Annotated[
        list[IntersectionSchedule],
        "Signal schedules, each repeating green, yellow, then red.",
    ]
    arrivals: Annotated[
        list[VehicleArrival],
        "Vehicle arrivals to evaluate in this exact order.",
    ]


@dataclass
class ArrivalEvaluation(Output):
    arrival_id: str
    intersection_id: str
    arrival_time: int
    signal_color: Annotated[str, "Signal color at arrival: green, yellow, or red."]
    may_cross: Annotated[bool, "Whether the vehicle may cross immediately."]
    next_crossing_time: Annotated[
        int,
        "Earliest scenario time at which the signal is green.",
    ]
    wait_seconds: Annotated[int, "Whole seconds from arrival until crossing is allowed."]


@dataclass
class TrafficScheduleOutput(Output):
    evaluations: Annotated[
        list[ArrivalEvaluation],
        "One evaluation per arrival, preserving the task's arrival order.",
    ]


@dataclass
class ReadTrafficRequestInput(Output):
    task: Annotated[TrafficScheduleInput, "The traffic-schedule task to inspect."]


@dataclass
class ReadTrafficRequestOutput(Output):
    intersections: list[IntersectionSchedule]
    arrivals: list[VehicleArrival]


@dataclass
class WriteTrafficEvaluationInput(Output):
    task: Annotated[TrafficScheduleInput, "The task input copied exactly as given."]
    evaluations: Annotated[
        list[ArrivalEvaluation],
        "The completed evaluations in the task's arrival order.",
    ]


@dataclass
class WriteTrafficEvaluationOutput(Output):
    report_path: Annotated[str, "Report path written relative to the workspace."]
    report: TrafficScheduleOutput


TOOLS = {
    Tool.READ_TRAFFIC_REQUEST: (ReadTrafficRequestInput, ReadTrafficRequestOutput),
    Tool.WRITE_TRAFFIC_EVALUATION: (
        WriteTrafficEvaluationInput,
        WriteTrafficEvaluationOutput,
    ),
}

TASKS = {
    Task.EVALUATE_TRAFFIC_SCHEDULE: (TrafficScheduleInput, TrafficScheduleOutput),
}

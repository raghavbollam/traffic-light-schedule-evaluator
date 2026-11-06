# Traffic Light Schedule Evaluator

A `nanoagent.plugin/v0001` plugin for the COMP 480/580 verifiable-tasks
milestone. It evaluates fixed, repeating traffic-light schedules for a supplied
set of vehicle arrivals and reports the active signal plus the earliest legal
crossing time.

## Tools

| Tool | Purpose | Code |
|---|---|---|
| `read_traffic_request` | Reads and validates all intersection schedules and arrivals | `src/plugin/tools.py` |
| `write_traffic_evaluation` | Writes the completed result to `traffic-evaluation.json` | `src/plugin/tools.py` |

### Task

| Task | Purpose | Runner |
|---|---|---|
| `evaluate-traffic-schedule` | Evaluates every arrival against its intersection's repeating signal cycle | `agent`, with both tools |

## Schedule rules

Every intersection has:

- a unique `intersection_id`;
- a non-negative `cycle_start` in whole scenario seconds;
- positive whole-second `green_seconds`, `yellow_seconds`, and `red_seconds`.

The cycle repeats forever in this order:

```text
green -> yellow -> red -> green -> ...
```

For an arrival at time `t`, define:

```text
cycle_length = green_seconds + yellow_seconds + red_seconds
position = (t - cycle_start) modulo cycle_length
```

The phase intervals are half-open:

```text
green:  0 <= position < green_seconds
yellow: green_seconds <= position < green_seconds + yellow_seconds
red:    green_seconds + yellow_seconds <= position < cycle_length
```

An arrival exactly at a boundary belongs to the phase beginning at that
boundary. Only green permits immediate crossing. A yellow or red arrival must
wait until position zero of the next cycle:

```text
next_crossing_time = t + cycle_length - position
wait_seconds = next_crossing_time - t
```

For a green arrival, `next_crossing_time` is the arrival time and
`wait_seconds` is zero.

## Example

For a cycle starting at time `0` with 30 seconds green, 5 seconds yellow, and
25 seconds red:

| Arrival time | Signal | Next crossing | Wait |
|---:|---|---:|---:|
| 29 | green | 29 | 0 |
| 30 | yellow | 60 | 30 |
| 35 | red | 60 | 25 |
| 60 | green | 60 | 0 |

## Verification

The verifier does not trust the agent or use an LLM as judge. It validates the
task, independently calculates every expected result, and compares the complete
structured output. It rejects:

- missing, extra, duplicate, or reordered arrivals;
- invalid identifiers, durations, timestamps, signal colors, or booleans;
- incorrect phases, crossing decisions, wait durations, or crossing times;
- reports whose persisted JSON differs from the submitted output.

Scoring is all-or-nothing: every arrival must be correct for the task to pass.

## Reproducibility and limitations

The task is fully offline. All schedules and arrivals are typed task input, the
plugin has no network permission, and integer seconds avoid floating-point and
timezone ambiguity.

The model deliberately represents one signal governing each arrival. It does
not model turn arrows, pedestrians, emergency preemption, sensor-actuated
timing, coordinated corridors, or real-world traffic APIs. Yellow never permits
crossing in this task.

## Layout

```text
.
├── nanoagent.yaml
├── contract.py
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env
├── src/plugin/
├── tests/
├── ui/
├── product/
└── verifier/
```

The tracked `.env` file is required by RUSH Lab. This plugin needs no secret or
runtime environment variables, so the file contains declarations only and no
values.

## Develop and run

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest -q
nanoagent plugin inspect .
```

To publish, push the plugin to a public GitHub repository and submit its URL
through RUSH Lab.

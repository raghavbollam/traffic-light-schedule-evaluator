import { h, statusPill } from "./kit/components.js";

const SIGNAL_TONE = {
  green: "ok",
  yellow: "warn",
  red: "bad",
};

function renderEvaluation(value) {
  const evaluations = Array.isArray(value?.evaluations) ? value.evaluations : [];
  const rows = evaluations.map((entry) =>
    h(
      "tr",
      {},
      h("td", { text: entry.arrival_id }),
      h("td", { text: entry.intersection_id }),
      h("td", { class: "numeric", text: String(entry.arrival_time) }),
      h(
        "td",
        {},
        statusPill(
          entry.signal_color,
          SIGNAL_TONE[entry.signal_color] ?? "info",
        ),
      ),
      h("td", { text: entry.may_cross ? "Yes" : "No" }),
      h("td", {
        class: "numeric",
        text: String(entry.next_crossing_time),
      }),
      h("td", {
        class: "numeric",
        text: `${entry.wait_seconds}s`,
      }),
    ),
  );

  return h(
    "div",
    { class: "traffic-report" },
    h("p", {
      class: "traffic-summary",
      text: `${evaluations.length} vehicle arrival${
        evaluations.length === 1 ? "" : "s"
      } evaluated`,
    }),
    h(
      "div",
      { class: "traffic-table-wrap" },
      h(
        "table",
        { class: "traffic-table" },
        h(
          "thead",
          {},
          h(
            "tr",
            {},
            ["Arrival", "Intersection", "Time", "Signal", "May cross", "Next green", "Wait"].map(
              (label) => h("th", { text: label }),
            ),
          ),
        ),
        h("tbody", {}, rows),
      ),
    ),
  );
}

export default {
  TrafficScheduleOutput: renderEvaluation,
};

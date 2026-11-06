function element(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (name === "className") node.className = value;
    else node.setAttribute(name, value);
  }
  for (const child of children) {
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function renderEvaluation(value) {
  const evaluations = Array.isArray(value?.evaluations) ? value.evaluations : [];
  const table = element("table", { className: "traffic-table" });
  table.append(
    element("thead", {}, [
      element("tr", {}, ["Arrival", "Intersection", "Time", "Signal", "May cross", "Next green", "Wait"].map((label) => element("th", {}, [label]))),
    ]),
  );

  const body = element("tbody");
  for (const entry of evaluations) {
    body.append(
      element("tr", {}, [
        element("td", {}, [entry.arrival_id]),
        element("td", {}, [entry.intersection_id]),
        element("td", { className: "numeric" }, [entry.arrival_time]),
        element("td", {}, [
          element("span", { className: `signal signal-${entry.signal_color}` }, [entry.signal_color]),
        ]),
        element("td", {}, [entry.may_cross ? "Yes" : "No"]),
        element("td", { className: "numeric" }, [entry.next_crossing_time]),
        element("td", { className: "numeric" }, [`${entry.wait_seconds}s`]),
      ]),
    );
  }
  table.append(body);

  return element("div", { className: "traffic-report" }, [
    element("p", { className: "traffic-summary" }, [
      `${evaluations.length} vehicle arrival${evaluations.length === 1 ? "" : "s"} evaluated`,
    ]),
    table,
  ]);
}

export default {
  TrafficScheduleOutput: renderEvaluation,
};

#!/usr/bin/env python3
"""Load and normalize benchmark CSV data for the standalone HTML dashboard."""

import csv
from collections import defaultdict
from pathlib import Path

from analyze import CANDIDATES, TRUE, detect, to_bool


def load_results(csv_path, col_overrides=None):
    """Load benchmark results and group runs by database/system/question."""
    csv_path = Path(csv_path)
    col_overrides = col_overrides or {}

    if not csv_path.is_file():
        raise FileNotFoundError(f"Results CSV not found: {csv_path}")

    with csv_path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        headers = reader.fieldnames or []

    if not rows:
        raise ValueError(f"Results CSV is empty: {csv_path}")

    columns = {
        key: detect(headers, key, col_overrides.get(key))
        for key in CANDIDATES
    }

    infra_col = next(
        (h for h in headers if h.lower() == "infra_error"), None
    )
    category_col = next(
        (h for h in headers if h.lower() == "category"), None
    )

    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    dropped_ambiguous = 0
    dropped_infra = 0
    included_rows = 0

    for row_number, row in enumerate(rows, start=2):
        if category_col and row[category_col].strip().lower() == "ambiguous":
            dropped_ambiguous += 1
            continue

        if (
            infra_col
            and row[infra_col].strip().lower() in TRUE
        ):
            dropped_infra += 1
            continue

        db = row[columns["db"]].strip()
        system = row[columns["system"]].strip()
        question = row[columns["question"]].strip()

        if not db or not system or not question:
            raise ValueError(
                f"Missing database, system, or question at CSV row {row_number}"
            )

        try:
            passed = to_bool(row[columns["passed"]])
        except ValueError as error:
            raise ValueError(
                f"Invalid pass/fail value at CSV row {row_number}: {error}"
            ) from error

        grouped[db][system][question].append(passed)
        included_rows += 1

    databases = {}

    for db in sorted(grouped):
        systems = {}

        for system in sorted(grouped[db]):
            questions = {}

            for question in sorted(grouped[db][system]):
                runs = grouped[db][system][question]
                questions[question] = {
                    "runs": runs,
                    "passed": sum(runs),
                    "total_runs": len(runs),
                    "flaky": 0 < sum(runs) < len(runs),
                }

            systems[system] = questions

        databases[db] = systems

    return {
        "source": csv_path.name,
        "total_rows": len(rows),
        "included_rows": included_rows,
        "dropped_ambiguous": dropped_ambiguous,
        "dropped_infra": dropped_infra,
        "databases": databases,
    }


def majority_score(runs):
    """Return 1 for a strict majority pass, otherwise 0."""
    if not runs:
        return None
    return 1 if sum(runs) * 2 > len(runs) else 0


def bootstrap_accuracy(scores, reps=5000, seed=1):
    """Return a deterministic percentile 95% bootstrap CI for accuracy."""
    import random

    if not scores:
        return None, None

    if reps < 1:
        raise ValueError("Bootstrap repetitions must be greater than zero")

    rng = random.Random(seed)
    n = len(scores)
    estimates = []

    for _ in range(reps):
        sample = [scores[rng.randrange(n)] for _ in range(n)]
        estimates.append(sum(sample) / n * 100)

    estimates.sort()

    low_index = min(int(0.025 * reps), reps - 1)
    high_index = min(int(0.975 * reps), reps - 1)

    return estimates[low_index], estimates[high_index]


def summarize_system(questions, all_questions, reps=5000, seed=1):
    """Summarize accuracy, confidence interval, coverage, and flakiness."""
    scores = []
    assessable_questions = 0
    flaky_questions = 0

    for question in all_questions:
        result = questions.get(question)

        if result is None:
            continue

        score = majority_score(result["runs"])
        if score is not None:
            scores.append(score)

        if result["total_runs"] >= 2:
            assessable_questions += 1
            if result["flaky"]:
                flaky_questions += 1

    total_questions = len(all_questions)
    answered_questions = len(scores)

    if answered_questions:
        accuracy = sum(scores) / answered_questions * 100
        ci_low, ci_high = bootstrap_accuracy(
            scores, reps=reps, seed=seed
        )
    else:
        accuracy = None
        ci_low, ci_high = None, None

    return {
        "accuracy": accuracy,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "answered_questions": answered_questions,
        "total_questions": total_questions,
        "coverage": (
            answered_questions / total_questions * 100
            if total_questions else 0.0
        ),
        "flaky_questions": flaky_questions,
        "assessable_questions": assessable_questions,
        "flakiness_rate": (
            flaky_questions / assessable_questions * 100
            if assessable_questions else None
        ),
    }


def question_status(questions, question):
    """Return pass, fail, flaky, or missing for a heatmap cell."""
    result = questions.get(question)

    if result is None:
        return "missing"

    if result["flaky"]:
        return "flaky"

    return "pass" if majority_score(result["runs"]) else "fail"


def build_dashboard_data(csv_paths, reps=5000, seed=1):
    """Build independent dashboard datasets from raw benchmark CSV files."""
    datasets = []

    for csv_path in sorted(csv_paths):
        loaded = load_results(csv_path)
        databases = {}

        for db, systems_data in loaded["databases"].items():
            all_questions = sorted({
                question
                for questions in systems_data.values()
                for question in questions
            })

            systems = {}
            for index, (system, questions) in enumerate(
                sorted(systems_data.items())
            ):
                systems[system] = {
                    "summary": summarize_system(
                        questions,
                        all_questions,
                        reps=reps,
                        seed=seed + index,
                    ),
                    "questions": {
                        question: {
                            "runs": result["total_runs"],
                            "passed": result["passed"],
                            "flaky": result["flaky"],
                            "status": question_status(
                                questions, question
                            ),
                        }
                        for question, result in questions.items()
                    },
                    "flaky_questions": [
                        question
                        for question, result in questions.items()
                        if result["flaky"]
                    ],
                }

            databases[db] = {
                "question_ids": all_questions,
                "systems": systems,
            }

        datasets.append({
            "source": loaded["source"],
            "total_rows": loaded["total_rows"],
            "included_rows": loaded["included_rows"],
            "dropped_ambiguous": loaded["dropped_ambiguous"],
            "dropped_infra": loaded["dropped_infra"],
            "databases": databases,
        })

    if not datasets:
        raise ValueError("No CSV datasets were found")

    return datasets


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Interactive database evaluation benchmark dashboard">
<title>dbeval Benchmark Dashboard</title>
<style>
:root {
  color-scheme: light;
  --bg:#F3F1EA; --surface:#FFFFFF; --surface-raised:#F8F7F2;
  --text:#18211D; --muted:#65716B; --border:#E2E0D8;
  --accent:#2F6F4E; --accent-strong:#3E805E; --accent-secondary:#DE306E;
  --pass:#2F6F4E; --pass-soft:#EAF2EC;
  --fail:#BE3657; --fail-soft:#FBECEF;
  --flaky:#94600E; --flaky-soft:#F9F0DD;
  --missing:#77827B; --missing-soft:#EDF0ED;
  --header-text:#18211D; --header-muted:#65716B;
  --toggle-bg:rgba(255,255,255,.72); --toggle-border:#D7D8CF;
  --toggle-icon:#D08A20;
  --shadow:0 8px 24px rgba(34,49,39,.055);
  --shadow-hover:0 12px 28px rgba(34,49,39,.09);
}
[data-theme="dark"] {
  color-scheme:dark;
  --bg:#0B1220; --surface:#0D1D2D; --surface-raised:#102638;
  --text:#E8F0FE; --muted:#A7B5C4; --border:#20384A;
  --accent:#4FD1C5; --accent-strong:#68DCD1; --accent-secondary:#EE68A5;
  --pass:#4FD1C5; --pass-soft:#153A3D;
  --fail:#EE68A5; --fail-soft:#3D2638;
  --flaky:#F1BD68; --flaky-soft:#3B3327;
  --missing:#A7B5C4; --missing-soft:#243443;
  --header-text:#E8F0FE; --header-muted:#A7B5C4;
  --toggle-bg:rgba(16,38,56,.82); --toggle-border:#285A61;
  --toggle-icon:#B8A7E8;
  --shadow:0 8px 24px rgba(0,0,0,.16);
  --shadow-hover:0 12px 28px rgba(0,0,0,.24);
}
* {box-sizing:border-box}
html {min-height:100%;scroll-behavior:smooth}
body {
  min-height:100vh;margin:0;
  background:var(--bg);
  color:var(--text);
  font:15px/1.6 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  letter-spacing:.005em;
  transition:background .3s ease,color .25s ease;
}
header {
  padding:22px max(22px,calc((100% - 1200px)/2));
  color:var(--header-text);background:var(--surface-raised);
  border-bottom:1px solid var(--border);
  transition:background .3s ease,color .3s ease,border-color .3s ease;
}
.header-inner {display:flex;align-items:center;justify-content:space-between;gap:18px}
.header-brand {min-width:0}
header h1 {
  margin:0;font-size:clamp(23px,3vw,30px);font-weight:730;
  letter-spacing:-.035em;line-height:1.25;
}
header p {color:var(--header-muted);margin:5px 0 0;font-size:13px}
#theme {
  display:grid;place-items:center;flex:0 0 auto;
  width:40px;height:40px;min-height:40px;padding:0;
  border:1px solid var(--toggle-border);border-radius:12px;
  color:var(--toggle-icon);background:var(--toggle-bg);
  box-shadow:0 1px 2px rgba(20,35,27,.04);
  font-size:19px;line-height:1;
  transition:transform .22s ease,color .25s ease,background .25s ease,
    border-color .25s ease,box-shadow .25s ease;
}
#theme:hover {
  transform:translateY(-1px);
  background:var(--surface);border-color:var(--accent);
  box-shadow:0 4px 12px rgba(20,35,27,.1);
}
#theme:focus-visible {
  outline:3px solid color-mix(in srgb,var(--accent) 35%,transparent);
  outline-offset:3px;
}
main {max-width:1240px;margin:30px auto;padding:0 22px 54px}
.toolbar,.panel,.metric {
  background:var(--surface);border:1px solid var(--border);
  border-radius:16px;box-shadow:var(--shadow);
  transition:background .3s ease,color .3s ease,border-color .3s ease,
    box-shadow .2s ease,transform .2s ease;
}
.toolbar {
  padding:17px 18px;display:flex;gap:14px;align-items:end;
  flex-wrap:wrap;margin-bottom:21px;
  background:var(--surface-raised);
}
.control {display:grid;gap:6px;min-width:200px}
label {font-size:10px;color:var(--muted);font-weight:750;letter-spacing:.11em}
select,button {
  min-height:42px;font:inherit;color:var(--text);background:var(--surface);
  border:1px solid var(--border);border-radius:10px;padding:9px 13px;
  transition:color .25s ease,background .3s ease,border-color .2s ease,box-shadow .2s ease;
}
select {cursor:pointer}
button {
  cursor:pointer;color:var(--surface);font-weight:650;
  border-color:var(--accent);
  background:var(--accent);
  box-shadow:0 3px 9px color-mix(in srgb,var(--accent) 16%,transparent);
}
button:hover {transform:translateY(-1px);filter:brightness(1.08)}
select:hover,select:focus-visible,button:focus-visible {
  border-color:var(--accent);
  outline:3px solid color-mix(in srgb,var(--accent) 22%,transparent);
  outline-offset:2px;
}
.metrics {
  display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
  gap:15px;margin-bottom:21px;
}
.metric {
  position:relative;overflow:hidden;padding:18px 19px 17px;
  background:var(--surface);
}
.metric::before {
  content:"";position:absolute;inset:0 0 auto;height:3px;
  background:var(--accent);
}
.metric:nth-child(2)::before {background:var(--accent-secondary)}
.metric:nth-child(3)::before {background:var(--pass)}
.metric:nth-child(4)::before {background:var(--flaky)}
.metric span {display:block;color:var(--muted);font-size:11px;font-weight:650;letter-spacing:.04em}
.metric strong {display:block;font-size:29px;font-weight:750;letter-spacing:-.035em;margin-top:6px}
.panel {padding:22px;margin-bottom:21px;min-width:0}
.panel h2 {font-size:18px;font-weight:720;letter-spacing:-.02em;margin:0 0 4px}
.sub {color:var(--muted);font-size:13px;margin:0 0 19px}
.chart-wrap {overflow-x:auto}
svg {display:block;width:100%;min-width:450px;height:auto;overflow:visible}
#accuracy rect {filter:drop-shadow(0 2px 3px color-mix(in srgb,var(--accent) 16%,transparent));transition:opacity .2s ease}
#accuracy rect:hover {opacity:1}
.legend {display:flex;gap:18px;flex-wrap:wrap;color:var(--muted);font-size:12px;margin:0 0 12px}
.legend span {display:inline-flex;align-items:center}
.dot {display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px}
.heatmap-wrap {overflow:auto}
table {border-collapse:separate;border-spacing:5px 6px;width:100%;min-width:600px}
th,td {padding:9px 10px;text-align:center;font-size:11px}
th {color:var(--muted);font-size:10px;font-weight:750;letter-spacing:.07em;text-transform:uppercase}
th:first-child,td:first-child {
  text-align:left;position:sticky;left:0;background:var(--surface);z-index:1;
}
th:first-child {background:var(--surface)}
.cell {
  min-width:62px;border:1px solid transparent;border-radius:8px;
  font-size:10px;font-weight:750;letter-spacing:.04em;
  transition:background .3s ease,color .3s ease,border-color .3s ease,
    transform .16s ease,box-shadow .16s ease;
}
.cell:hover {transform:translateY(-1px);box-shadow:0 3px 9px rgba(20,35,27,.1)}
.cell.pass {background:var(--pass-soft);color:var(--pass);border-color:color-mix(in srgb,var(--pass) 17%,transparent)}
.cell.fail {background:var(--fail-soft);color:var(--fail);border-color:color-mix(in srgb,var(--fail) 17%,transparent)}
.cell.flaky {background:var(--flaky-soft);color:var(--flaky);border-color:color-mix(in srgb,var(--flaky) 19%,transparent)}
.cell.missing {background:var(--missing-soft);color:var(--muted);border-color:color-mix(in srgb,var(--missing) 18%,transparent)}
.flaky-list {display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:11px}
.flaky-system {
  padding:14px 15px;border:1px solid var(--border);border-radius:12px;
  background:var(--surface-raised);
  transition:background .3s ease,color .3s ease,border-color .3s ease,box-shadow .2s ease;
}
.flaky-system:hover {border-color:color-mix(in srgb,var(--flaky) 40%,var(--border));box-shadow:var(--shadow)}
.flaky-system strong {display:block;margin-bottom:5px;font-weight:700}
.flaky-system p {margin:0;color:var(--muted);font-size:12px;overflow-wrap:anywhere}
.flaky-system p+p {margin-top:5px}
.note {font-size:12px;color:var(--muted)}
footer {text-align:center;color:var(--muted);font-size:11px;padding:15px 10px}
::selection {background:color-mix(in srgb,var(--accent) 25%,transparent)}
@media(max-width:600px) {
  main {padding:0 13px 36px;margin-top:20px}
  header {padding:18px 19px}
  .panel {padding:16px}
  .toolbar {padding:14px}
  .control {min-width:100%}
  .metric strong {font-size:26px}
}
@media(prefers-reduced-motion:reduce) {
  *,*::before,*::after {scroll-behavior:auto!important;transition:none!important}
}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="header-brand">
      <h1>dbeval Benchmark Dashboard</h1>
      <p>Question-level accuracy, statistical uncertainty and run consistency</p>
    </div>
    <button id="theme" type="button" aria-label="Switch to dark mode"
      title="Switch to dark mode" aria-pressed="false">
      <span id="theme-icon" aria-hidden="true">☀️</span>
    </button>
  </div>
</header>
<main>
  <section class="toolbar">
    <div class="control">
      <label for="dataset">BENCHMARK DATASET</label>
      <select id="dataset"></select>
    </div>
    <div class="control">
      <label for="database">DATABASE</label>
      <select id="database"></select>
    </div>
  </section>

  <section class="metrics" id="metrics"></section>

  <section class="panel">
    <h2>System Accuracy Comparison</h2>
    <p class="sub">Majority-vote accuracy across questions. Error bars show 95% bootstrap confidence intervals.</p>
    <div class="chart-wrap" id="accuracy"></div>
    <p class="note">Only answered questions contribute to accuracy. Coverage is shown separately.</p>
  </section>

  <section class="panel">
    <h2>Flakiness Breakdown</h2>
    <p class="sub">Questions with mixed pass/fail outcomes across repeated runs.</p>
    <div id="flakiness" class="flaky-list"></div>
  </section>

  <section class="panel">
    <h2>Question-Level Pass/Fail Heatmap</h2>
    <p class="sub">Each cell represents a question's majority result. Flaky and missing results are identified separately.</p>
    <div class="legend">
      <span><i class="dot" style="background:var(--pass)"></i>Pass</span>
      <span><i class="dot" style="background:var(--fail)"></i>Fail</span>
      <span><i class="dot" style="background:var(--flaky)"></i>Flaky</span>
      <span><i class="dot" style="background:var(--missing)"></i>N/A</span>
    </div>
    <div class="heatmap-wrap" id="heatmap"></div>
  </section>
  <footer id="metadata"></footer>
</main>

<script id="dashboard-data" type="application/json">__DATA__</script>
<script>
"use strict";
const datasets = JSON.parse(document.getElementById("dashboard-data").textContent);
const datasetSelect = document.getElementById("dataset");
const databaseSelect = document.getElementById("database");

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function current() {
  const dataset = datasets[Number(datasetSelect.value)];
  return {dataset, db:dataset.databases[databaseSelect.value]};
}
function fmt(value) {
  return value === null || value === undefined ? "N/A" : value.toFixed(1) + "%";
}
function populateDatabases() {
  const {dataset} = current();
  databaseSelect.replaceChildren();
  Object.keys(dataset.databases).forEach(db => {
    const option = el("option", db);
    option.value = db;
    databaseSelect.append(option);
  });
  render();
}
function renderMetrics(dataset, db) {
  const summaries = Object.values(db.systems).map(s => s.summary);
  const questions = db.question_ids.length;
  const systems = Object.keys(db.systems).length;
  const flaky = Object.values(db.systems).reduce(
    (sum, s) => sum + s.summary.flaky_questions, 0
  );
  const metrics = [
    ["Systems", String(systems)],
    ["Questions", String(questions)],
    ["Source rows", String(dataset.included_rows)],
    ["Flaky system/question pairs", String(flaky)]
  ];
  const root = document.getElementById("metrics");
  root.replaceChildren();
  metrics.forEach(([label,value]) => {
    const card = el("div", undefined, "metric");
    card.append(el("span",label),el("strong",value));
    root.append(card);
  });
}
function renderAccuracy(db) {
  const entries = Object.entries(db.systems);
  const width = Math.max(560, entries.length * 125 + 100);
  const height = 300, left = 48, right = 18, top = 25, bottom = 75;
  const plotHeight = height - top - bottom;
  const plotWidth = width - left - right;
  const x = i => left + (i + .5) * plotWidth / entries.length;
  const y = value => top + plotHeight * (1 - value / 100);
  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Accuracy chart">`;
  [0,25,50,75,100].forEach(tick => {
    svg += `<line x1="${left}" y1="${y(tick)}" x2="${width-right}" y2="${y(tick)}" stroke="var(--border)"/>`;
    svg += `<text x="${left-9}" y="${y(tick)+4}" text-anchor="end" fill="var(--muted)" font-size="11">${tick}</text>`;
  });
  entries.forEach(([name,system],i) => {
    const s = system.summary;
    if (s.accuracy === null) return;
    const cx = x(i), barWidth = Math.min(48,plotWidth/entries.length*.55);
    const barY = y(s.accuracy);
    const barHeight = y(0)-barY;
    svg += `<rect x="${cx-barWidth/2}" y="${barY}" width="${barWidth}" height="${barHeight}" rx="5" fill="var(--accent)" opacity=".82"/>`;
    if (s.ci_low !== null) {
      const low=y(s.ci_low), high=y(s.ci_high);
      svg += `<line x1="${cx}" y1="${high}" x2="${cx}" y2="${low}" stroke="var(--text)" stroke-width="2"/>`;
      svg += `<line x1="${cx-7}" y1="${high}" x2="${cx+7}" y2="${high}" stroke="var(--text)" stroke-width="2"/>`;
      svg += `<line x1="${cx-7}" y1="${low}" x2="${cx+7}" y2="${low}" stroke="var(--text)" stroke-width="2"/>`;
    }
    svg += `<text x="${cx}" y="${Math.max(14,barY-8)}" text-anchor="middle" fill="var(--text)" font-size="11">${s.accuracy.toFixed(1)}%</text>`;
    svg += `<text x="${cx}" y="${height-48}" text-anchor="middle" fill="var(--text)" font-size="11">${escapeXml(name)}</text>`;
    svg += `<text x="${cx}" y="${height-29}" text-anchor="middle" fill="var(--muted)" font-size="10">${s.answered_questions}/${s.total_questions} answered</text>`;
  });
  svg += "</svg>";
  document.getElementById("accuracy").innerHTML=svg;
}
function escapeXml(value) {
  return String(value).replace(/[&<>"']/g,c=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  })[c]);
}
function renderFlakiness(db) {
  const root=document.getElementById("flakiness");
  root.replaceChildren();
  Object.entries(db.systems).forEach(([name,system]) => {
    const s=system.summary;
    const card=el("div",undefined,"flaky-system");
    const rate=s.flakiness_rate===null
      ? "Not assessable (fewer than two runs)"
      : `${s.flaky_questions} / ${s.assessable_questions} questions (${fmt(s.flakiness_rate)})`;
    card.append(el("strong",name),el("p",rate));
    if(system.flaky_questions.length) {
      card.append(el("p","Questions: "+system.flaky_questions.join(", ")));
    }
    root.append(card);
  });
}
function renderHeatmap(db) {
  const table=el("table");
  const head=el("tr");
  head.append(el("th","Question"));
  const systems=Object.keys(db.systems);
  systems.forEach(name=>head.append(el("th",name)));
  const thead=el("thead"); thead.append(head); table.append(thead);
  const tbody=el("tbody");
  db.question_ids.forEach(question=>{
    const row=el("tr"); row.append(el("td",question));
    systems.forEach(name=>{
      const item=db.systems[name].questions[question];
      const status=item ? item.status : "missing";
      const label=status==="missing" ? "N/A" : status.toUpperCase();
      const cell=el("td",label,"cell "+status);
      cell.title=item
        ? `${item.passed}/${item.runs} runs passed`
        : "No result recorded";
      row.append(cell);
    });
    tbody.append(row);
  });
  table.append(tbody);
  const root=document.getElementById("heatmap");
  root.replaceChildren(table);
}
function render() {
  const {dataset,db}=current();
  renderMetrics(dataset,db);
  renderAccuracy(db);
  renderFlakiness(db);
  renderHeatmap(db);
  document.getElementById("metadata").textContent =
    `Source: ${dataset.source} · ${dataset.total_rows} rows · `+
    `${dataset.dropped_ambiguous} ambiguous and ${dataset.dropped_infra} infrastructure rows excluded`;
}
datasets.forEach((dataset,index)=>{
  const option=el("option",dataset.source);
  option.value=String(index);
  datasetSelect.append(option);
});
datasetSelect.addEventListener("change",populateDatabases);
databaseSelect.addEventListener("change",render);
const themeButton=document.getElementById("theme");
const themeIcon=document.getElementById("theme-icon");
const themeStorageKey="dbeval-dashboard-theme";
try {
  const savedTheme=localStorage.getItem(themeStorageKey);
  if(savedTheme==="light"||savedTheme==="dark") {
    document.documentElement.dataset.theme=savedTheme;
  }
} catch(error) {
  console.warn("Unable to read the saved dashboard theme preference.",error);
}
function updateThemeButton() {
  const dark=document.documentElement.dataset.theme==="dark";
  const action=dark?"Switch to light mode":"Switch to dark mode";
  themeIcon.textContent=dark?"🌙":"☀️";
  themeButton.setAttribute("aria-label",action);
  themeButton.title=action;
  themeButton.setAttribute("aria-pressed",String(dark));
}
themeButton.addEventListener("click",()=>{
  const dark=document.documentElement.dataset.theme!=="dark";
  const theme=dark?"dark":"light";
  document.documentElement.dataset.theme=theme;
  updateThemeButton();
  try {
    localStorage.setItem(themeStorageKey,theme);
  } catch(error) {
    console.warn("Unable to save the dashboard theme preference.",error);
  }
});
updateThemeButton();
populateDatabases();
</script>
</body>
</html>
"""


def render_dashboard(csv_paths, output, reps=5000, seed=1):
    """Generate a self-contained interactive HTML benchmark dashboard."""
    import json
    from pathlib import Path

    datasets = build_dashboard_data(
        csv_paths, reps=reps, seed=seed
    )

    payload = json.dumps(
        datasets, ensure_ascii=False, separators=(",", ":")
    )
    payload = (
        payload.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )

    document = DASHBOARD_HTML.replace("__DATA__", payload)

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    return output


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a standalone interactive dbeval HTML dashboard."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("results/raw"),
        help="Directory containing benchmark CSV files",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("results/benchmark_dashboard.html"),
        help="Output HTML dashboard path",
    )
    parser.add_argument(
        "--reps",
        type=int,
        default=5000,
        help="Number of bootstrap repetitions (default: 5000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Bootstrap random seed (default: 1)",
    )

    args = parser.parse_args(argv)

    if args.reps < 1:
        parser.error("--reps must be greater than zero")

    if not args.input_dir.is_dir():
        parser.error(f"Input directory not found: {args.input_dir}")

    csv_paths = sorted(args.input_dir.glob("*.csv"))

    if not csv_paths:
        parser.error(f"No CSV files found in {args.input_dir}")

    try:
        output = render_dashboard(
            csv_paths,
            args.output,
            reps=args.reps,
            seed=args.seed,
        )
    except (OSError, ValueError, SystemExit) as error:
        parser.error(str(error))

    print(f"[PASS] Dashboard generated: {output}")
    print(f"[INFO] Datasets included: {len(csv_paths)}")
    print(f"[INFO] Bootstrap repetitions: {args.reps}")


if __name__ == "__main__":
    main()

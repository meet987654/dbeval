# Day 5 reviewer guide

Read this whole file first. It is the only instruction file you get.

## Your job

A business has written down its definitions in `docs/business_rules.md`.
Your job is to teach three tools (ktx, Wren Engine, Datus) those definitions, so that an AI that writes SQL
for this business gets the answers right. You do this once per tool per database, with a timer.

Later, **everything you store in a tool's layer is pasted in full into the prompt of a model that writes SQL.**
So exact SQL expressions are worth more than loose prose.

## What you may look at

- `docs/business_rules.md` (the only source of truth)
- each tool's own documentation
- the tool project folders in this copy (`layers/`, `ktx_*`, `wren_*`, `conf/`)
- the database itself, with the read-only `reader` account (to check a column or a value)

## What you must NOT look at

- Anything outside this folder. In particular, do not open the original `dbeval` folder.
- Any question list, gold SQL, result file or failure list. They are not in this copy. If you find one, stop,
  tell the person running the study, and do not use it.
- Do not ask anyone which rules matter more or what a model got wrong.

## The clock

- Use the same budget for every tool and database: **30 minutes**.
- Docs-reading before the timer is allowed, up to 15 minutes per tool. Write down how many minutes you used.
- Record the start time, and check the time often (in PowerShell: `Get-Date`). Write the time in the log
  after each rule. Stop at 30 minutes. Anything unfinished is logged as "ran out of time".
- After you freeze a layer, do not edit it again.

## Order

- appdb: `ktx`, then `wren`, then `datus`
- olist: `datus`, then `wren`, then `ktx`

## What to encode, in this order

Work through the numbered rules in `docs/business_rules.md` for the database you are on, from rule 1 downwards.
For olist, use the olist section's numbered rules in the same way. Do the earlier rules first, so every tool gets
the same chance to fit them in the time.

## How to encode each rule

Use the most structured form the tool supports. Preference order:

1. a **view** with the filter already inside it
2. a **calculated field** with the exact SQL expression
3. a **metric** with the exact SQL expression
4. a column or table **description**, only when nothing structured is available

Write the exact SQL, do not paraphrase it. Test an expression on the database before you store it, if time allows.

## Where each tool keeps its layer (check by looking, these are pointers)

- **ktx:** the project folder for the database, with `semantic-layer/<db>/...` YAML files, plus anything the tool offers for descriptions or knowledge pages.
- **Wren Engine:** the project folder for the database, `models/*/metadata.yml`, `relationships.yml`, then `wren context build` rebuilds `target/mdl.json`.
- **Datus:** `conf/agent.yml` and its stored schema and knowledge data. Find out, from its docs, where it keeps descriptions, metrics and reference SQL.

## The log

Fill `notes/day5_review_log.md`. One row per rule, per tool, per database:

| rule | tool | db | form used (view / calculated / metric / description / not possible / ran out of time) | minutes |
|---|---|---|---|---|

Also write: the tool version, the docs-reading minutes, the start and end time, and anything you could not express.

## When you finish a tool

1. Copy the finished layer to `layers/<tool>/<db>_reviewed/`.
2. Do not run any test questions. You do not have any, and that is on purpose.
3. Move to the next tool in the order above.

Do not tune a layer to make it "look" better. Encode the rules as written, nothing more.

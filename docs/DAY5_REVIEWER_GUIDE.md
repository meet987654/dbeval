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
- the tool layers in `layers/` and the Datus settings in `conf/`
- the database itself, with the read-only `reader` account (to check a column or a value)

## What you must NOT look at

- Anything outside this folder. In particular, do not open the original `dbeval` folder.
- Any question list, gold SQL, result file or failure list. They are not in this copy. If you find one, stop,
  tell the person running the study, and do not use it.
- Do not ask anyone which rules matter more or what a model got wrong.

## The clock

- Use the same budget for every tool and database: **30 minutes**.
- Docs-reading before the timer is allowed, up to 15 minutes per tool. Write down how many minutes you used.
- Record the start time, and check the time often (in PowerShell: `Get-Date`). Write the start and end time
  in the log for each tool. Stop at 30 minutes. Anything unfinished is logged as "ran out of time".
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

## Where you work

For every tool and database, make your working copy from the starting folder you were given:

- Copy `layers/<tool>/<start folder>` to `layers/<tool>/<database>_reviewed`, and work only in the copy.
- The finished copy is your output. Nothing else needs to be moved.

### ktx

The copy is a ktx project directory. Run all ktx commands from inside the copy.

The editable file is `semantic-layer/<db>/_schema/public.yaml`. Within each table block you can add:

```yaml
  accounts:
    description: "Real account: is_test = false AND deleted_at IS NULL."
    columns:
      - name: plan_tier
        description: "Current plan. Use plan_tier, not plan (plan is the old signup value)."
    metrics:
      - name: gross_revenue_usd
        sql: "SUM(CASE WHEN i.status='paid' THEN i.amount_cents::numeric/100*f.usd_per_unit END)"
        description: "Paid invoices in period, real accounts only, USD."
```

The `description:` field exists at table level and at column level. The `metrics:` block is the only
structured numeric form ktx offers natively in the YAML. If ktx offers knowledge pages (`ktx knowledge add`),
you may use those too; log the form as `description`.

Do not touch `.ktx/` (the internal state store) or `raw-sources/`. Do not re-run `ktx scan`.

### Wren Engine

The copy is a Wren project. Source files are:

- `models/<table>/metadata.yml` — one file per table; this is where you work
- `relationships.yml` — join conditions; do not edit unless a join is missing

The `target/mdl.json` file is **generated** — do not edit it by hand. After you finish editing
source files, rebuild it with:

```
wren context build
```

Run that command from inside the copy directory.

Within a `metadata.yml` column block, add a `description:` key and/or convert to a calculated column:

```yaml
# Description on a plain column
- name: plan_tier
  type: VARCHAR
  is_calculated: false
  not_null: false
  is_primary_key: false
  description: "Current plan. Use plan_tier, not plan."
  properties: {}

# Calculated column (is_calculated: true + expression:)
- name: amount_usd
  type: DOUBLE
  is_calculated: true
  not_null: false
  is_primary_key: false
  expression: "amount_cents::numeric / 100 * fx_rates.usd_per_unit"
  description: "Invoice amount in USD."
  properties: {}
```

Table-level description goes under the top-level `properties:` key as `description:`:

```yaml
properties:
  description: "Real account: is_test = false AND deleted_at IS NULL."
```

### Datus

The layer is the `schema_metadata.json` file in the copy. The runner reads **only** `schema_metadata.json`
and `schema_value.json` as JSON — the `.parquet` files in the folder are not read by the runner and must
not be touched.

The **only edit allowed** is the text of the `definition` field for each table object. Append your rules
as a SQL comment after the existing CREATE TABLE statement:

```json
{
  "identifier": "appdb.public.accounts",
  "table_name": "accounts",
  "definition": "CREATE TABLE ... ;\n-- BUSINESS RULES:\n-- Real account: is_test = false AND deleted_at IS NULL.\n-- Current plan: use plan_tier (not plan).",
  ...
}
```

Do not add rows, do not change any key except `definition`, do not touch `schema_value.json`.

The `agent.yml` file in the same folder contains only connection config (no `instructions` or `rules` keys);
the runner skips it. If you want to add free-text rules that apply to all tables, you may drop a `rules.md`
file into the copy folder — the runner will include it verbatim. Log its form as `description`.

## Integrity rules

- **Work only inside this folder.** Run `Get-Location` first and write the path at the top of the log. If your
  working path is not the `dbeval-day5` folder, stop.
- **Never write a list of values, a column meaning or a code from memory.** Query the database with the `reader`
  account first, then write what you found.
- **Use only places the tool really reads.** Do not edit exported files by hand (the one exception is the Datus
  `definition` text described above), do not add files the tool does not load, and do not copy a placeholder
  vector or other dummy data into a store. If a tool has no native place for a rule, log it as `description`
  only if that tool's own files hold descriptions, otherwise as `not possible`.
- **A view is only a view if the tool defines it.** If the tool cannot define a view, write the filter into a
  description and log the form as `description`.
- **Time:** write the start and end time (from `Get-Date`) for each tool and database. Do not estimate minutes per rule.
- **Versions:** run the tool's own version command (for example `pip show <package>` or `ktx --version`) and copy the output.

## The log

Fill `notes/day5_review_log.md`. One row per rule, per tool, per database:

| rule | tool | db | form used | rule timestamp (`Get-Date`) |
|---|---|---|---|---|

`form used` values: `view` / `calculated` / `metric` / `description` / `not possible` / `ran out of time`

Also write at the top of each tool block: the tool version, docs-reading minutes, start time, and end time.

## When you finish a tool

1. Check that your finished layer is in `layers/<tool>/<db>_reviewed/` (your working copy). Do not edit it after this.
2. Do not run any test questions. You do not have any, and that is on purpose.
3. Move to the next tool in the order above.

Do not tune a layer to make it "look" better. Encode the rules as written, nothing more.

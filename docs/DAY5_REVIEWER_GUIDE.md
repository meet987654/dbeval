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

## Where you work

For every tool and database, make your working copy from the starting folder you were given:

- Copy `layers/<tool>/<start folder>` to `layers/<tool>/<database>_reviewed`, and work only in the copy.
- The finished copy is your output. Nothing else needs to be moved.

How each tool keeps things (check by looking, these are pointers):

- **ktx:** the copy is a ktx project. Use it as the project directory for ktx commands. The layer is the YAML under `semantic-layer/<db>/...` and whatever descriptions or knowledge pages ktx offers.
- **Wren Engine:** the copy is a Wren project: `models/*/metadata.yml`, `relationships.yml`, and views as the Wren docs describe. Run `wren context build` inside the copy to rebuild `target/mdl.json`.
- **Datus:** the layer is the exported `schema_metadata.json` in the copy. The only edit allowed there is the text of the `definition` fields (descriptions as SQL comments, and SQL snippets as comments). If Datus's docs show a file-based knowledge feature (metrics, reference SQL), use that as well. Do not touch the Parquet files or vectors, and do not add rows.

## Integrity rules

- **Work only inside this folder.** Run `Get-Location` first and write the path at the top of the log. If your
  working path is not the `dbeval-day5` folder, stop.
- **Never write a list of values, a column meaning or a code from memory.** Query the database with the `reader`
  account first, then write what you found.
- **Use only places the tool really reads.** Do not edit exported JSON or Parquet files by hand, do not add files
  the tool does not load, and do not copy a placeholder vector or other dummy data into a store. If a tool has no
  native place for a rule, log it as `description` only if that tool's own files hold descriptions, otherwise as
  `not possible`.
- **A view is only a view if the tool defines it.** If the tool cannot define a view, write the filter into a description
  and log the form as `description`.
- **Time:** write the start and end time (from `Get-Date`) for each tool and database. Do not estimate minutes per rule.
- **Versions:** run the tool's own version command (for example `pip show <package>` or `ktx --version`) and copy the output.

## The log

Fill `notes/day5_review_log.md`. One row per rule, per tool, per database:

| rule | tool | db | form used (view / calculated / metric / description / not possible / ran out of time) | minutes |
|---|---|---|---|---|

Also write: the tool version, the docs-reading minutes, the start and end time, and anything you could not express.

## When you finish a tool

1. The finished copy at `layers/<tool>/<db>_reviewed/` is your output. Do not move anything further.
2. Do not run any test questions. You do not have any, and that is on purpose.
3. Move to the next tool in the order above.

Do not tune a layer to make it "look" better. Encode the rules as written, nothing more.

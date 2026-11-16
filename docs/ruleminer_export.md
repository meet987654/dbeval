# Exporting RuleMiner rules to dbt MetricFlow and Wren Engine

RuleMiner finds soft-delete and test-account filters, join keys, money scales and status values.
`export` compiles those findings into files that existing semantic layers can load.

```bash
python -m ruleminer.cli export --format dbt  --out dbt_models/
python -m ruleminer.cli export --format wren --out wren_models/ --min-confidence 0.9
# inspect any database SQLAlchemy can reach (default: the reader DB, else db/<db>.sqlite)
python -m ruleminer.cli export --format dbt --out dbt_models/ --url duckdb:///db/appdb.duckdb
```

| option | meaning |
|---|---|
| `--format dbt\|wren` | target format (required) |
| `--out DIR` | output directory (created) |
| `--db`, `--url` | which database to inspect for columns, types and schema signals |
| `--query-log`, `--min-support` | mining inputs (same as the main command) |
| `--min-confidence X` | export only rules with confidence >= X (default 0, export everything) |

## What is produced

| RuleMiner rule | dbt (`ruleminer_semantic_models.yml`) | Wren (`manifest.json`) |
|---|---|---|
| entity filter (`deleted_at IS NULL`, `is_test = FALSE`) | metric `real_<table>` with a `filter:` using `{{ Dimension('<entity>__<col>') }}` | view `real_<table>` = `SELECT * FROM <table> WHERE ...` |
| relationship (`a.id = b.a_id`) | primary entity on the `id` side, foreign entity on the other | `MANY_TO_ONE` relationship plus primary key |
| money scale (`*_cents`) | measure `<col>_sum_scaled` = `sum(col::numeric / 100)` | calculated column `<name>_units` = `CAST(col AS DECIMAL) / 100` |
| lifecycle states | description on the `status` dimension | not exported (no equivalent field) |

Every exported object records the rule's confidence and evidence source: `meta.ruleminer` in dbt,
`properties.ruleminer_confidence` / `ruleminer_source` in Wren. Without a reachable database the
export still works, but columns are limited to those the rules mention and Wren types are guessed
from column names.

## Design notes (the RFC's discussion points)

**Which format is more expressive for multi-table netting rules?** Neither expresses them well from
mined rules alone. MetricFlow can express them (derived and ratio metrics, filters across entities)
and is the better target for metrics. Wren MDL is stronger for modelling joins and calculated
columns. RuleMiner currently mines single-table filters, joins and unit scales, so the export
stays within what both formats cover. "Net revenue = paid - refunds with separate date filters" is
a rule a human still has to write.

**How should confidence be exposed?** Two ways: `--min-confidence` drops weak rules before export,
and the confidence and source stay in each object's metadata so a reviewer can find the
lower-confidence ones in the generated files instead of trusting them blindly.

## Known limits

- The dbt output has not been validated with the `dbt`/`mf` tools (they are not a dependency here);
  tests check internal consistency (every metric points at an existing measure, every
  `Dimension()` entity exists, one primary entity per model). Run `mf validate-configs` on the
  output before relying on it.
- The generated Wren manifest has not been compiled or run through Wren Engine.
- The "round-trip" benchmark (re-running dbeval with the generated layers and comparing accuracy
  to the hand-written ones) is not done: it needs a live LLM and the generated layers wired into
  `runners/wren_run.py` / a dbt runner. The export is the prerequisite for that comparison.
- A table has one primary entity: when a table is the "one" side of several joins, the first join
  key found is used. Joins that are not a simple `a.col = b.col` are skipped.

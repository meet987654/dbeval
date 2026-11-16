"""Export RuleMiner's synthesized rules to open semantic-layer formats.

    dbt MetricFlow  -> one YAML file (semantic_models + metrics) with `real_<table>` filtered metrics,
                       relationship entities and money-scale measures.
    Wren Engine MDL -> a manifest.json (models, relationships, calculated columns, `real_<table>` views).

Every exported object carries the rule's confidence and evidence source (`meta.ruleminer` in dbt,
`properties` in Wren), and `min_confidence` drops weak rules before export, so a developer decides
how much to trust automatic discovery.

Design notes and known limits are in docs/ruleminer_export.md.
"""

import json
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import sqlglot
import yaml
from sqlglot import exp

from ruleminer.synthesizer import SynthesizedRule

# Map a SQL type name (any case, any dialect) to Wren MDL / dbt dimension kinds.
_TIME_HINTS = ("timestamp", "date", "time")


def filter_rules(rules: List[SynthesizedRule], min_confidence: float = 0.0) -> List[SynthesizedRule]:
    """Keep rules whose confidence is at least `min_confidence`."""
    return [r for r in rules if r.confidence >= min_confidence]


def _meta(rule: SynthesizedRule) -> Dict[str, Any]:
    return {"confidence": round(rule.confidence, 3), "source": rule.support_source}


def parse_join(join_sql: str) -> Optional[Tuple[str, str, str, str]]:
    """Parse `a.col = b.col` into (one_table, one_col, many_table, many_col).

    The side whose column is `id` is the "one" side; otherwise the left side is.
    Returns None if the predicate is not a simple equi-join of two qualified columns.
    """
    try:
        node = sqlglot.parse_one(join_sql, read="postgres")
    except Exception:
        return None
    if not isinstance(node, exp.EQ):
        return None
    left, right = node.left, node.right
    if not (isinstance(left, exp.Column) and isinstance(right, exp.Column) and left.table and right.table):
        return None
    l, r = (left.table, left.name), (right.table, right.name)
    if r[1].lower() == "id" and l[1].lower() != "id":
        l, r = r, l
    return l[0], l[1], r[0], r[1]


def predicate_columns(predicate: str, default_table: str) -> List[Tuple[str, str]]:
    """(table, column) pairs referenced by a predicate; unqualified columns belong to `default_table`."""
    node = sqlglot.parse_one(predicate, read="postgres")
    seen: List[Tuple[str, str]] = []
    for c in node.find_all(exp.Column):
        pair = (c.table or default_table, c.name)
        if pair not in seen:
            seen.append(pair)
    return seen


def _dbt_filter(predicate: str, default_table: str, entity_of: Dict[str, str]) -> str:
    """Rewrite a SQL predicate with MetricFlow `{{ Dimension('<entity>__<col>') }}` references.

    `entity_of` maps a table to the name of its primary entity (MetricFlow addresses a dimension
    through an entity).
    """
    node = sqlglot.parse_one(predicate, read="postgres")

    def swap(n):
        if isinstance(n, exp.Column):
            table = n.table or default_table
            return exp.column(f"__DIM__{entity_of.get(table, table)}__{n.name}__")
        return n

    text = node.transform(swap).sql(dialect="postgres")
    return re.sub(r"__DIM__(\w+?)__(\w+?)__(?![A-Za-z0-9])", lambda m: "{{ Dimension('%s__%s') }}" % (m.group(1), m.group(2)), text)


def _kind(col: str, types: Dict[str, str]) -> str:
    t = types.get(col, "").lower()
    if any(h in t for h in _TIME_HINTS) or col.endswith("_at"):
        return "time"
    return "categorical"


def _tables(rules: List[SynthesizedRule], schema: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """table -> {column: type} for every table touched by a rule (schema first, then rule references)."""
    tables: Dict[str, Dict[str, str]] = defaultdict(dict)
    for t, cols in (schema or {}).items():
        tables[t].update(cols)
    for r in rules:
        tables[r.target_table]  # noqa: B018 - ensure present
        if r.category == "entity_filter":
            for t, c in predicate_columns(r.sql_predicate_or_expr, r.target_table):
                tables[t].setdefault(c, "")
        elif r.category == "relationship":
            j = parse_join(r.sql_predicate_or_expr)
            if j:
                tables[j[0]].setdefault(j[1], "")
                tables[j[2]].setdefault(j[3], "")
        elif r.category == "currency_scale":
            m = re.match(r"(\w+)\.(\w+)::", r.sql_predicate_or_expr)
            if m:
                tables[m.group(1)].setdefault(m.group(2), "")
        elif r.category == "lifecycle_state":
            tables[r.target_table].setdefault("status", "")
    return tables


# ---------------------------------------------------------------------------
# dbt MetricFlow
# ---------------------------------------------------------------------------

def to_dbt(rules: List[SynthesizedRule], schema: Optional[Dict[str, Dict[str, str]]] = None,
           min_confidence: float = 0.0) -> Dict[str, Any]:
    """Build a dbt MetricFlow spec dict (`semantic_models` + `metrics`) from synthesized rules."""
    rules = filter_rules(rules, min_confidence)
    tables = _tables(rules, schema or {})

    entities: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    measures: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    dim_notes: Dict[Tuple[str, str], str] = {}
    metrics: List[Dict[str, Any]] = []
    entity_of: Dict[str, str] = {}  # table -> name of its primary entity
    measure_sources = set()  # (table, column) used inside a measure, so not exposed as a dimension

    for r in rules:
        if r.category == "relationship":
            j = parse_join(r.sql_predicate_or_expr)
            if not j:
                continue
            one_t, one_c, many_t, many_c = j
            ename = f"{one_t}_{one_c}"
            if one_t not in entity_of:  # a table has exactly one primary entity: the first join key wins
                entity_of[one_t] = ename
                entities[one_t].append({"name": ename, "type": "primary", "expr": one_c, "meta": {"ruleminer": _meta(r)}})
            if entity_of[one_t] == ename:
                entities[many_t].append({"name": ename, "type": "foreign", "expr": many_c, "meta": {"ruleminer": _meta(r)}})
        elif r.category == "currency_scale":
            m = re.match(r"(\w+)\.(\w+)::numeric / (\d+)", r.sql_predicate_or_expr)
            if m:
                t, c, scale = m.group(1), m.group(2), m.group(3)
                measure_sources.add((t, c))
                measures[t].append({
                    "name": f"{c}_sum_scaled",
                    "description": f"Sum of {c} divided by {scale} with numeric division (stored in minor units).",
                    "agg": "sum",
                    "expr": f"{c}::numeric / {scale}",
                    "meta": {"ruleminer": _meta(r)},
                })
        elif r.category == "lifecycle_state":
            dim_notes[(r.target_table, "status")] = r.rule_statement

    # entity filters are rendered last because their Dimension() references need every table's entity name
    for r in rules:
        if r.category == "entity_filter":
            metrics.append({
                "name": f"real_{r.target_table}",
                "description": r.rule_statement,
                "type": "simple",
                "type_params": {"measure": f"{r.target_table}_count"},
                "filter": _dbt_filter(r.sql_predicate_or_expr, r.target_table, entity_of),
                "meta": {"ruleminer": _meta(r)},
            })

    semantic_models = []
    for t in sorted(tables):
        cols = tables[t]
        ents = list(entities.get(t, []))
        # one entity per (name, type); a table cannot declare a primary entity twice
        uniq, seen = [], set()
        for e in ents:
            key = (e["name"], e["type"])
            if key not in seen:
                seen.add(key)
                uniq.append(e)
        referenced = {c for c in cols if c not in {e["expr"] for e in uniq} and (t, c) not in measure_sources}
        dims = []
        for c in sorted(referenced):
            d = {"name": c, "type": _kind(c, cols)}
            if d["type"] == "time":
                d["type_params"] = {"time_granularity": "day"}
            if (t, c) in dim_notes:
                d["description"] = dim_notes[(t, c)]
            dims.append(d)
        sm = {
            "name": t,
            "model": f"ref('{t}')",
            "entities": uniq if any(e["type"] == "primary" for e in uniq) else
            [{"name": entity_of.setdefault(t, t), "type": "primary", "expr": "id"}] + uniq,
            "dimensions": dims,
            "measures": [{"name": f"{t}_count", "agg": "count", "expr": "1"}] + measures.get(t, []),
        }
        semantic_models.append(sm)

    # metrics need their measure; keep only those whose table has a semantic model (always true)
    return {"version": 2, "semantic_models": semantic_models, "metrics": metrics}


# ---------------------------------------------------------------------------
# Wren Engine MDL
# ---------------------------------------------------------------------------

_WREN_TYPE_ALIASES = {
    "TIMESTAMP WITH TIME ZONE": "TIMESTAMPTZ",
    "TIMESTAMP WITHOUT TIME ZONE": "TIMESTAMP",
    "DOUBLE PRECISION": "DOUBLE",
    "CHARACTER VARYING": "VARCHAR",
    "TEXT": "VARCHAR",
}


def _wren_type(col: str, types: Dict[str, str]) -> str:
    """Declared type if the schema is known, otherwise a name-based guess (VARCHAR when unsure)."""
    t = types.get(col, "").upper()
    if t:
        return _WREN_TYPE_ALIASES.get(t, t)
    c = col.lower()
    if c.endswith("_at") or c.endswith("_date"):
        return "TIMESTAMP"
    if c == "id" or c.endswith("_id") or c.endswith("_cents"):
        return "INTEGER"
    if c.startswith("is_") or c in ("deleted", "archived"):
        return "BOOLEAN"
    return "VARCHAR"


def to_wren(rules: List[SynthesizedRule], schema: Optional[Dict[str, Dict[str, str]]] = None,
            min_confidence: float = 0.0, catalog: str = "wren", schema_name: str = "public") -> Dict[str, Any]:
    """Build a Wren Engine MDL manifest dict from synthesized rules."""
    rules = filter_rules(rules, min_confidence)
    tables = _tables(rules, schema or {})

    pks: Dict[str, set] = defaultdict(set)
    relationships: List[Dict[str, Any]] = []
    calculated: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    views: List[Dict[str, Any]] = []

    for r in rules:
        if r.category == "relationship":
            j = parse_join(r.sql_predicate_or_expr)
            if not j:
                continue
            one_t, one_c, many_t, many_c = j
            pks[one_t].add(one_c)
            relationships.append({
                "name": f"{many_t}_{many_c}__{one_t}_{one_c}",
                "models": [many_t, one_t],
                "joinType": "MANY_TO_ONE",
                "condition": f"{many_t}.{many_c} = {one_t}.{one_c}",
                "properties": {"ruleminer_confidence": str(round(r.confidence, 3)), "ruleminer_source": r.support_source},
            })
        elif r.category == "currency_scale":
            m = re.match(r"(\w+)\.(\w+)::numeric / (\d+)", r.sql_predicate_or_expr)
            if m:
                t, c, scale = m.group(1), m.group(2), m.group(3)
                base = c[:-6] if c.endswith("_cents") else c
                calculated[t].append({
                    "name": f"{base}_units",
                    "type": "DECIMAL",
                    "isCalculated": True,
                    "expression": f"CAST({c} AS DECIMAL) / {scale}",
                    "notNull": False,
                    "isPrimaryKey": False,
                    "properties": {"description": r.rule_statement, "ruleminer_confidence": str(round(r.confidence, 3))},
                })
        elif r.category == "entity_filter":
            where = re.sub(rf"\b{re.escape(r.target_table)}\.", "", r.sql_predicate_or_expr)
            views.append({
                "name": f"real_{r.target_table}",
                "statement": f"SELECT * FROM {r.target_table} WHERE {where}",
                "properties": {
                    "description": r.rule_statement,
                    "ruleminer_confidence": str(round(r.confidence, 3)),
                    "ruleminer_source": r.support_source,
                },
            })

    models = []
    for t in sorted(tables):
        cols = tables[t]
        columns = [{
            "name": c,
            "type": _wren_type(c, cols),
            "isCalculated": False,
            "notNull": False,
            "isPrimaryKey": c in pks.get(t, set()),
            "properties": {},
        } for c in sorted(cols)]
        columns += calculated.get(t, [])
        models.append({
            "name": t,
            "tableReference": {"catalog": "", "schema": schema_name, "table": t},
            "columns": columns,
            "primaryKey": next(iter(sorted(pks[t])), None) if pks.get(t) else None,
            "properties": {},
        })
    for m in models:
        if m["primaryKey"] is None:
            del m["primaryKey"]

    return {"catalog": catalog, "schema": schema_name, "models": models, "relationships": relationships, "views": views}


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def export_files(fmt: str, rules: List[SynthesizedRule], schema: Optional[Dict[str, Dict[str, str]]] = None,
                 min_confidence: float = 0.0) -> Dict[str, str]:
    """Return {relative filename: text} for the chosen format ('dbt' or 'wren')."""
    if fmt == "dbt":
        return {"ruleminer_semantic_models.yml": yaml.safe_dump(to_dbt(rules, schema, min_confidence), sort_keys=False)}
    if fmt == "wren":
        return {"manifest.json": json.dumps(to_wren(rules, schema, min_confidence), indent=2) + "\n"}
    raise ValueError(f"unknown export format {fmt!r} (expected 'dbt' or 'wren')")

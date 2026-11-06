"""Query log mining: parses SQL queries using sqlglot, normalizes aliases,
extracts invariant filtering predicates and join conditions, and calculates empirical support.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import os
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml

import sqlglot
from sqlglot import exp


@dataclass
class MinedPredicate:
    table: str
    predicate_sql: str
    canonical_sql: str
    occurrences: int
    table_queries: int
    support: float
    is_invariant: bool
    is_soft_delete: bool = False
    is_test_filter: bool = False


@dataclass
class MinedJoin:
    table_a: str
    col_a: str
    table_b: str
    col_b: str
    join_sql: str
    occurrences: int
    confidence: float


@dataclass
class MinedMetricTransformation:
    table: str
    column: str
    operation: str  # e.g. "divide_100", "numeric_cast"
    expression_sample: str
    occurrences: int


@dataclass
class MiningResults:
    total_queries: int
    table_query_counts: Dict[str, int]
    predicates: List[MinedPredicate]
    invariants: List[MinedPredicate]
    joins: List[MinedJoin]
    metrics: List[MinedMetricTransformation]
    status_values: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))


class QueryLogMiner:
    """Parses historical queries to discover invariant filters, join keys, and column transformations."""

    def __init__(self, min_support: float = 0.5, dialect: str = "postgres"):
        self.min_support = min_support
        self.dialect = dialect

    def mine_queries(
        self,
        queries: List[str],
        schema_metadata: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> MiningResults:
        """Analyze a list of SQL queries."""
        total_queries = 0
        table_query_counts: Counter = Counter()
        predicate_query_counts: Dict[str, Tuple[str, Counter]] = {}  # table -> Counter(predicate_str)
        join_counts: Counter = Counter()
        metric_counts: Counter = Counter()
        status_values: Dict[str, Set[str]] = defaultdict(set)

        # Build column -> tables lookup if schema metadata is provided
        col_to_tables: Dict[str, Set[str]] = defaultdict(set)
        if schema_metadata:
            for tbl, cols in schema_metadata.items():
                for c in cols:
                    c_name = c["name"] if isinstance(c, dict) else str(c)
                    col_to_tables[c_name.lower()].add(tbl)

        for query_idx, sql_raw in enumerate(queries):
            if not sql_raw or not sql_raw.strip():
                continue

            try:
                tree = sqlglot.parse_one(sql_raw, read=self.dialect)
            except Exception:
                try:
                    tree = sqlglot.parse_one(sql_raw)
                except Exception:
                    continue

            total_queries += 1

            # 1. Resolve table aliases and CTEs
            alias_to_table: Dict[str, str] = {}
            referenced_tables: Set[str] = set()
            cte_names: Set[str] = {cte.alias for cte in tree.find_all(exp.CTE) if cte.alias}

            for table_node in tree.find_all(exp.Table):
                t_name = table_node.name
                if not t_name or t_name in cte_names:
                    continue
                referenced_tables.add(t_name)
                alias_to_table[t_name] = t_name
                if table_node.alias:
                    alias_to_table[table_node.alias] = t_name

            for t in referenced_tables:
                table_query_counts[t] += 1

            # 2. Extract Joins from JOIN ... ON ...
            query_joins_seen: Set[Tuple[str, str, str, str]] = set()
            for join_node in tree.find_all(exp.Join):
                on_clause = join_node.args.get("on")
                if on_clause:
                    conds = on_clause.flatten() if isinstance(on_clause, exp.And) else [on_clause]
                    for cond in conds:
                        canon_join = self._canonicalize_join(cond, alias_to_table, cte_names)
                        if canon_join and canon_join not in query_joins_seen:
                            join_counts[canon_join] += 1
                            query_joins_seen.add(canon_join)

            # 3. Extract WHERE conjuncts
            query_preds_seen: Set[Tuple[str, str]] = set()
            for where_node in tree.find_all(exp.Where):
                conds = (
                    where_node.this.flatten()
                    if isinstance(where_node.this, exp.And)
                    else [where_node.this]
                )
                for conjunct in conds:
                    # Check if this conjunct in WHERE is actually an explicit join (e.g. a.id = b.a_id)
                    canon_join = self._canonicalize_join(conjunct, alias_to_table, cte_names)
                    if canon_join:
                        if canon_join not in query_joins_seen:
                            join_counts[canon_join] += 1
                            query_joins_seen.add(canon_join)
                        continue

                    # Filter out query-specific dynamic or temporal filters (e.g. date windows, specific IDs)
                    if self._is_ad_hoc_filter(conjunct):
                        continue

                    # Otherwise, it's a filtering predicate
                    pred_res = self._normalize_predicate(
                        conjunct, alias_to_table, referenced_tables, col_to_tables
                    )
                    if pred_res:
                        tbl, norm_pred = pred_res
                        if tbl in cte_names:
                            continue
                        pair = (tbl, norm_pred)
                        if pair not in query_preds_seen:
                            if tbl not in predicate_query_counts:
                                predicate_query_counts[tbl] = Counter()
                            predicate_query_counts[tbl][norm_pred] += 1
                            query_preds_seen.add(pair)

                        # Check for status / state literal values
                        if "status" in norm_pred.lower():
                            for lit in conjunct.find_all(exp.Literal):
                                if lit.is_string:
                                    status_values[tbl].add(lit.this)

            # 4. Check for currency division transformations (e.g. amount_cents / 100)
            query_metrics_seen: Set[Tuple[str, str, str]] = set()
            for div_node in tree.find_all(exp.Div):
                right = div_node.right
                left = div_node.left
                if isinstance(right, exp.Literal) and right.this == "100":
                    for col in left.find_all(exp.Column):
                        c_name = col.name
                        tbl = alias_to_table.get(col.table or "")
                        if not tbl and c_name.lower() in col_to_tables:
                            cand = col_to_tables[c_name.lower()] & referenced_tables
                            if len(cand) == 1:
                                tbl = next(iter(cand))
                        if tbl:
                            tup = (tbl, c_name, "divide_100")
                            if tup not in query_metrics_seen:
                                metric_counts[tup] += 1
                                query_metrics_seen.add(tup)

        # Build MinedPredicate objects
        all_predicates: List[MinedPredicate] = []
        invariants: List[MinedPredicate] = []

        for tbl, counts in predicate_query_counts.items():
            tbl_queries = table_query_counts.get(tbl, 0)
            if tbl_queries == 0:
                continue

            for pred_sql, count in counts.items():
                support = round(count / tbl_queries, 4)
                is_inv = support >= self.min_support
                is_soft_del = "deleted_at is null" in pred_sql.lower() or "deleted = false" in pred_sql.lower()
                is_test = "is_test = false" in pred_sql.lower() or "test = false" in pred_sql.lower()

                mp = MinedPredicate(
                    table=tbl,
                    predicate_sql=pred_sql,
                    canonical_sql=pred_sql,
                    occurrences=count,
                    table_queries=tbl_queries,
                    support=support,
                    is_invariant=is_inv,
                    is_soft_delete=is_soft_del,
                    is_test_filter=is_test,
                )
                all_predicates.append(mp)
                if is_inv:
                    invariants.append(mp)

        # Sort invariants by support descending
        invariants.sort(key=lambda p: (p.support, p.occurrences), reverse=True)
        all_predicates.sort(key=lambda p: (p.support, p.occurrences), reverse=True)

        # Build MinedJoin objects
        mined_joins: List[MinedJoin] = []
        for (t1, c1, t2, c2), count in join_counts.items():
            max_tbl_q = max(table_query_counts.get(t1, 1), table_query_counts.get(t2, 1))
            confidence = round(count / max_tbl_q, 4)
            mined_joins.append(
                MinedJoin(
                    table_a=t1,
                    col_a=c1,
                    table_b=t2,
                    col_b=c2,
                    join_sql=f"{t1}.{c1} = {t2}.{c2}",
                    occurrences=count,
                    confidence=confidence,
                )
            )
        mined_joins.sort(key=lambda j: j.occurrences, reverse=True)

        # Build MinedMetricTransformation objects
        mined_metrics: List[MinedMetricTransformation] = []
        for (tbl, col, op), count in metric_counts.items():
            mined_metrics.append(
                MinedMetricTransformation(
                    table=tbl,
                    column=col,
                    operation=op,
                    expression_sample=f"{tbl}.{col}::numeric / 100",
                    occurrences=count,
                )
            )

        return MiningResults(
            total_queries=total_queries,
            table_query_counts=dict(table_query_counts),
            predicates=all_predicates,
            invariants=invariants,
            joins=mined_joins,
            metrics=mined_metrics,
            status_values=dict(status_values),
        )

    def mine_file(
        self,
        path: str,
        schema_metadata: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> MiningResults:
        """Ingest queries from a YAML, JSON, or SQL file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        queries: List[str] = []
        ext = os.path.splitext(path)[1].lower()

        with open(path, "r", encoding="utf-8") as f:
            if ext in (".yaml", ".yml"):
                data = yaml.safe_load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            sql = item.get("gold_sql") or item.get("sql") or item.get("query")
                            if sql:
                                queries.append(sql)
                        elif isinstance(item, str):
                            queries.append(item)
            elif ext == ".json":
                import json

                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            sql = item.get("gold_sql") or item.get("sql") or item.get("query")
                            if sql:
                                queries.append(sql)
            else:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("--"):
                        queries.append(line)

        return self.mine_queries(queries, schema_metadata=schema_metadata)

    def _is_ad_hoc_filter(self, expr: exp.Expression) -> bool:
        """Identify query-specific transient filters (temporal intervals, exact row IDs) vs invariant rules."""
        import re

        sql_str = expr.sql()
        # 1. Date/timestamp pattern checks (e.g. '2026-07-01')
        if re.search(r"\d{4}-\d{2}-\d{2}", sql_str):
            return True

        # 2. Inequalities (<, >, <=, >=) or BETWEEN on temporal / date columns
        if isinstance(expr, (exp.GT, exp.GTE, exp.LT, exp.LTE, exp.Between)):
            for col in expr.find_all(exp.Column):
                if any(k in col.name.lower() for k in ("_at", "date", "time", "timestamp")):
                    return True

        # 3. Specific integer or single-entity ID checks (e.g. id = 42 or order_id = 'xxx')
        if isinstance(expr, exp.EQ):
            for col in expr.find_all(exp.Column):
                if col.name.lower() in ("id", "uuid") and any(
                    isinstance(l, exp.Literal) for l in (expr.left, expr.right)
                ):
                    return True

        return False

    def _canonicalize_join(
        self,
        expr: exp.Expression,
        alias_to_table: Dict[str, str],
        cte_names: Optional[Set[str]] = None,
    ) -> Optional[Tuple[str, str, str, str]]:
        """If expr is an equality join like t1.col1 = t2.col2 across different tables, return canonical tuple."""
        if not isinstance(expr, exp.EQ):
            return None

        left, right = expr.left, expr.right
        if not (isinstance(left, exp.Column) and isinstance(right, exp.Column)):
            return None

        t1 = alias_to_table.get(left.table or "")
        t2 = alias_to_table.get(right.table or "")
        if not t1 or not t2 or t1 == t2:
            return None

        if cte_names and (t1 in cte_names or t2 in cte_names):
            return None

        c1 = left.name
        c2 = right.name

        # Canonical ordering so (t1, c1) <= (t2, c2)
        if (t1, c1) <= (t2, c2):
            return (t1, c1, t2, c2)
        else:
            return (t2, c2, t1, c1)

    def _normalize_predicate(
        self,
        expr: exp.Expression,
        alias_to_table: Dict[str, str],
        referenced_tables: Set[str],
        col_to_tables: Dict[str, Set[str]],
    ) -> Optional[Tuple[str, str]]:
        """Rewrite aliases in a predicate to full table names, and determine its owning table."""
        copy_expr = expr.copy()
        cols = list(copy_expr.find_all(exp.Column))
        if not cols:
            return None

        # Determine target table
        target_table: Optional[str] = None
        for col in cols:
            if col.table and col.table in alias_to_table:
                target_table = alias_to_table[col.table]
                col.set("table", exp.to_identifier(target_table))
            elif not col.table:
                c_lower = col.name.lower()
                matching_tables = col_to_tables.get(c_lower, set()) & referenced_tables
                if len(matching_tables) == 1:
                    target_table = next(iter(matching_tables))
                    col.set("table", exp.to_identifier(target_table))
                elif len(referenced_tables) == 1:
                    target_table = next(iter(referenced_tables))
                    col.set("table", exp.to_identifier(target_table))

        if not target_table:
            return None

        # Format canonical SQL
        pred_sql = copy_expr.sql()
        return (target_table, pred_sql)

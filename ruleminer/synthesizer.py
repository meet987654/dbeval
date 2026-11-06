"""Rule synthesis: correlates schema signals with query log mining results,
resolves conflicts, and generates prompt-ready business rules in markdown, YAML, or JSON.
"""

from collections import defaultdict
from dataclasses import asdict, dataclass, field
import json
from typing import Any, Dict, List, Optional, Set
import yaml

from ruleminer.query_log_miner import MiningResults
from ruleminer.schema_signals import SchemaSignal


@dataclass
class SynthesizedRule:
    category: str  # "entity_filter", "currency_scale", "relationship", "lifecycle_state"
    target_table: str
    rule_statement: str
    sql_predicate_or_expr: str
    confidence: float
    support_source: str  # "schema_heuristic", "query_mining", "corroborated"
    notes: Optional[str] = None


class RuleSynthesizer:
    """Synthesizes induced business rules from schema signals and mined query logs."""

    def __init__(
        self,
        schema_signals: Optional[List[SchemaSignal]] = None,
        mining_results: Optional[MiningResults] = None,
    ):
        self.schema_signals = schema_signals or []
        self.mining_results = mining_results
        self.rules: List[SynthesizedRule] = []

    def synthesize(self) -> List[SynthesizedRule]:
        """Correlate schema signals and query logs into consolidated business rules."""
        rules: List[SynthesizedRule] = []

        # Group schema signals by (table, signal_type)
        signals_by_table_type: Dict[str, Dict[str, List[SchemaSignal]]] = defaultdict(lambda: defaultdict(list))
        for sig in self.schema_signals:
            signals_by_table_type[sig.table][sig.signal_type].append(sig)

        # Invariant predicates from mining results
        mined_invariants_by_table: Dict[str, List[Any]] = defaultdict(list)
        if self.mining_results:
            for inv in self.mining_results.invariants:
                mined_invariants_by_table[inv.table].append(inv)

        # 1. Real entity & filtering rules (Combining soft deletes + test filters per table)
        all_tables = set(signals_by_table_type.keys())
        if self.mining_results:
            all_tables.update(mined_invariants_by_table.keys())

        for tbl in sorted(all_tables):
            has_soft_del_signal = bool(signals_by_table_type[tbl].get("soft_delete"))
            has_test_signal = bool(signals_by_table_type[tbl].get("test_filter"))

            # Check mined predicates for this table
            mined_preds = mined_invariants_by_table.get(tbl, [])
            mined_soft_del = [p for p in mined_preds if p.is_soft_delete]
            mined_test = [p for p in mined_preds if p.is_test_filter]

            entity_clauses: List[str] = []
            confidence = 0.8
            source_parts = []

            # Soft delete clause
            if has_soft_del_signal and mined_soft_del:
                entity_clauses.append(f"{tbl}.deleted_at IS NULL")
                confidence = max(confidence, 1.0)
                source_parts.append("corroborated_soft_delete")
            elif mined_soft_del:
                entity_clauses.append(mined_soft_del[0].predicate_sql)
                confidence = max(confidence, 0.95)
                source_parts.append("mined_soft_delete")
            elif has_soft_del_signal:
                sig = signals_by_table_type[tbl]["soft_delete"][0]
                if sig.suggested_predicate:
                    entity_clauses.append(sig.suggested_predicate)
                confidence = max(confidence, 0.85)
                source_parts.append("schema_soft_delete")

            # Test account clause
            if has_test_signal and mined_test:
                entity_clauses.append(f"{tbl}.is_test = FALSE")
                confidence = max(confidence, 1.0)
                source_parts.append("corroborated_test_filter")
            elif mined_test:
                entity_clauses.append(mined_test[0].predicate_sql)
                confidence = max(confidence, 0.95)
                source_parts.append("mined_test_filter")
            elif has_test_signal:
                sig = signals_by_table_type[tbl]["test_filter"][0]
                if sig.suggested_predicate:
                    entity_clauses.append(sig.suggested_predicate)
                confidence = max(confidence, 0.85)
                source_parts.append("schema_test_filter")

            if entity_clauses:
                combined_sql = " AND ".join(entity_clauses)
                rules.append(
                    SynthesizedRule(
                        category="entity_filter",
                        target_table=tbl,
                        rule_statement=f"Real {tbl}: Always filter `{combined_sql}` to exclude deleted or test records.",
                        sql_predicate_or_expr=combined_sql,
                        confidence=confidence,
                        support_source="+".join(source_parts),
                        notes=f"Derived from {len(source_parts)} schema/log signals.",
                    )
                )

        # 2. Currency scale rules
        for sig in self.schema_signals:
            if sig.signal_type == "currency_scale":
                tbl = sig.table
                col = sig.column
                mined_div = False
                if self.mining_results:
                    for m in self.mining_results.metrics:
                        if m.table == tbl and m.column == col and m.operation == "divide_100":
                            mined_div = True
                            break

                source = "corroborated" if mined_div else "schema_heuristic"
                confidence = 1.0 if mined_div else 0.95
                scale = sig.metadata.get("scale", 100)
                expr = f"{tbl}.{col}::numeric / {scale}"

                rules.append(
                    SynthesizedRule(
                        category="currency_scale",
                        target_table=tbl,
                        rule_statement=f"Money scale on `{tbl}.{col}`: Stored in cents. Always convert using numeric division: `{expr}`.",
                        sql_predicate_or_expr=expr,
                        confidence=confidence,
                        support_source=source,
                        notes=f"Divide by {scale} with numeric casting to preserve precision.",
                    )
                )

        # 3. Relationships & Joins (Implicit FKs + Mined Joins)
        seen_joins: Set[str] = set()

        # From query mining (high confidence)
        if self.mining_results:
            for j in self.mining_results.joins:
                if j.occurrences >= 2 or j.confidence >= 0.2:
                    seen_joins.add(j.join_sql)
                    rules.append(
                        SynthesizedRule(
                            category="relationship",
                            target_table=j.table_a,
                            rule_statement=f"Join relationship: `{j.join_sql}`.",
                            sql_predicate_or_expr=j.join_sql,
                            confidence=min(0.7 + (j.confidence * 0.3), 0.98),
                            support_source="query_mining",
                            notes=f"Observed in {j.occurrences} historical queries.",
                        )
                    )

        # From schema implicit foreign keys
        for sig in self.schema_signals:
            if sig.signal_type == "implicit_fk":
                join_pred = sig.suggested_predicate
                if join_pred and join_pred not in seen_joins:
                    seen_joins.add(join_pred)
                    rules.append(
                        SynthesizedRule(
                            category="relationship",
                            target_table=sig.table,
                            rule_statement=f"Implicit join path: `{join_pred}`.",
                            sql_predicate_or_expr=join_pred,
                            confidence=sig.confidence,
                            support_source="schema_heuristic",
                            notes="Inferred from column naming convention without explicit foreign key constraint.",
                        )
                    )

        # 4. Lifecycle status states
        if self.mining_results and self.mining_results.status_values:
            for tbl, vals in self.mining_results.status_values.items():
                if vals:
                    val_str = ", ".join(f"'{v}'" for v in sorted(vals))
                    stmt = f"Observed lifecycle states for `{tbl}.status`: [{val_str}]. Filter according to question semantics (e.g. active vs canceled/paid)."
                    rules.append(
                        SynthesizedRule(
                            category="lifecycle_state",
                            target_table=tbl,
                            rule_statement=stmt,
                            sql_predicate_or_expr=f"{tbl}.status IN ({val_str})",
                            confidence=0.85,
                            support_source="query_mining",
                            notes="Mined from status predicates in historical queries.",
                        )
                    )

        self.rules = rules
        return rules

    def to_markdown(self, db_name: str = "database") -> str:
        """Render synthesized rules into a clean markdown document formatted for prompt injection."""
        if not self.rules:
            self.synthesize()

        lines = [f"## {db_name} (Discovered Business Rules & Schema Invariants)\n"]
        lines.append(
            "> Automatically extracted by RuleMiner from database schema signals and historical query logs.\n"
        )

        # Group rules by category
        by_cat: Dict[str, List[SynthesizedRule]] = defaultdict(list)
        for r in self.rules:
            by_cat[r.category].append(r)

        rule_idx = 1

        # Category 1: Entity Filters & Soft Deletes
        if by_cat.get("entity_filter"):
            lines.append("### 1. Real Entities & Exclusion Predicates")
            for r in by_cat["entity_filter"]:
                lines.append(f"{rule_idx}. **{r.rule_statement}**")
                rule_idx += 1
            lines.append("")

        # Category 2: Currency & Unit Scales
        if by_cat.get("currency_scale"):
            lines.append("### 2. Monetary & Numeric Scales")
            for r in by_cat["currency_scale"]:
                lines.append(f"{rule_idx}. **{r.rule_statement}**")
                rule_idx += 1
            lines.append("")

        # Category 3: Relationships & Joins
        if by_cat.get("relationship"):
            lines.append("### 3. Discovered Join Paths & Foreign Keys")
            for r in by_cat["relationship"]:
                lines.append(f"{rule_idx}. **{r.rule_statement}**")
                rule_idx += 1
            lines.append("")

        # Category 4: Lifecycle States
        if by_cat.get("lifecycle_state"):
            lines.append("### 4. Lifecycle States & Status Semantics")
            for r in by_cat["lifecycle_state"]:
                lines.append(f"{rule_idx}. **{r.rule_statement}**")
                rule_idx += 1
            lines.append("")

        return "\n".join(lines).strip()

    def to_dict(self) -> Dict[str, Any]:
        """Export synthesized rules as a dictionary."""
        if not self.rules:
            self.synthesize()
        return {"rules": [asdict(r) for r in self.rules]}

    def to_yaml(self) -> str:
        """Export synthesized rules as YAML."""
        return yaml.dump(self.to_dict(), sort_keys=False)

    def to_json(self, indent: int = 2) -> str:
        """Export synthesized rules as JSON."""
        return json.dumps(self.to_dict(), indent=indent)


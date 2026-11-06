"""Schema signals extraction: heuristics to detect soft-delete patterns,
test account flags, currency scale columns, lifecycle statuses, and implicit foreign keys.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional


@dataclass
class SchemaSignal:
    table: str
    column: str
    signal_type: str  # "soft_delete", "test_filter", "currency_scale", "boolean_flag", "implicit_fk", "status_enum"
    suggested_predicate: Optional[str]
    description: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class SchemaSignalExtractor:
    """Analyzes table schemas to discover potential business rules and invariants."""

    SOFT_DELETE_PATTERNS = [
        (re.compile(r"^(?:is_)?deleted(?:_at)?$", re.IGNORECASE), "timestamp", "{table}.deleted_at IS NULL"),
        (re.compile(r"^deleted$", re.IGNORECASE), "boolean", "{table}.deleted = FALSE"),
        (re.compile(r"^is_deleted$", re.IGNORECASE), "boolean", "{table}.is_deleted = FALSE"),
        (re.compile(r"^archived(?:_at)?$", re.IGNORECASE), "timestamp", "{table}.archived_at IS NULL"),
        (re.compile(r"^is_archived$", re.IGNORECASE), "boolean", "{table}.is_archived = FALSE"),
    ]

    TEST_PATTERNS = [
        (re.compile(r"^is_test$", re.IGNORECASE), "{table}.is_test = FALSE"),
        (re.compile(r"^test(?:_account|_mode|_data)?$", re.IGNORECASE), "{table}.{column} = FALSE"),
        (re.compile(r"^is_mock$", re.IGNORECASE), "{table}.is_mock = FALSE"),
    ]

    CURRENCY_SCALE_PATTERNS = [
        (re.compile(r"^(.*)_cents$", re.IGNORECASE), 100, "{table}.{column}::numeric / 100"),
        (re.compile(r"^(.*)_in_cents$", re.IGNORECASE), 100, "{table}.{column}::numeric / 100"),
        (re.compile(r"^(.*)_pence$", re.IGNORECASE), 100, "{table}.{column}::numeric / 100"),
        (re.compile(r"^(.*)_amount_cents$", re.IGNORECASE), 100, "{table}.{column}::numeric / 100"),
    ]

    BOOLEAN_ACTIVE_PATTERNS = [
        (re.compile(r"^is_active$", re.IGNORECASE), "{table}.is_active = TRUE"),
        (re.compile(r"^is_enabled$", re.IGNORECASE), "{table}.is_enabled = TRUE"),
        (re.compile(r"^is_published$", re.IGNORECASE), "{table}.is_published = TRUE"),
    ]

    STATUS_COLUMN_NAMES = {"status", "state", "lifecycle_state", "order_status", "plan_tier", "tier"}

    def extract_from_metadata(self, tables_metadata: Dict[str, List[Dict[str, Any]]], foreign_keys: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> List[SchemaSignal]:
        """Extract signals from in-memory schema metadata.
        
        tables_metadata: {table_name: [{"name": col_name, "type": type_str, "nullable": bool}, ...]}
        foreign_keys: {table_name: [{"constrained_columns": [...], "referred_table": "...", "referred_columns": [...]}]}
        """
        signals: List[SchemaSignal] = []
        foreign_keys = foreign_keys or {}
        all_tables = set(tables_metadata.keys())

        # Track existing explicit foreign keys: set of (table, col)
        explicit_fks = set()
        for tbl, fks in foreign_keys.items():
            for fk in fks:
                for c in fk.get("constrained_columns", []):
                    explicit_fks.add((tbl, c))

        for table, cols in tables_metadata.items():
            for col in cols:
                c_name = col.get("name", "")
                c_type = str(col.get("type", "")).lower()

                # 1. Soft Delete Check
                for pattern, expected_kind, pred_tmpl in self.SOFT_DELETE_PATTERNS:
                    if pattern.match(c_name):
                        pred = pred_tmpl.format(table=table, column=c_name)
                        signals.append(
                            SchemaSignal(
                                table=table,
                                column=c_name,
                                signal_type="soft_delete",
                                suggested_predicate=pred,
                                description=f"Soft delete column detected: records with `{pred}` should typically be excluded from active business reporting.",
                                confidence=0.85,
                                metadata={"column_type": c_type},
                            )
                        )
                        break

                # 2. Test Account / Flag Check
                for pattern, pred_tmpl in self.TEST_PATTERNS:
                    if pattern.match(c_name):
                        pred = pred_tmpl.format(table=table, column=c_name)
                        signals.append(
                            SchemaSignal(
                                table=table,
                                column=c_name,
                                signal_type="test_filter",
                                suggested_predicate=pred,
                                description=f"Test entity flag detected: test records (`{pred}`) should typically be excluded from production metrics.",
                                confidence=0.90,
                                metadata={"column_type": c_type},
                            )
                        )
                        break

                # 3. Currency Scale Check
                for pattern, scale, pred_tmpl in self.CURRENCY_SCALE_PATTERNS:
                    if pattern.match(c_name):
                        pred = pred_tmpl.format(table=table, column=c_name)
                        signals.append(
                            SchemaSignal(
                                table=table,
                                column=c_name,
                                signal_type="currency_scale",
                                suggested_predicate=pred,
                                description=f"Monetary value stored in sub-units ({c_name}): scale is {scale}x. Convert using numeric division: `{pred}`.",
                                confidence=0.95,
                                metadata={"scale": scale, "column_type": c_type},
                            )
                        )
                        break

                # 4. Boolean Active Flags
                for pattern, pred_tmpl in self.BOOLEAN_ACTIVE_PATTERNS:
                    if pattern.match(c_name):
                        pred = pred_tmpl.format(table=table, column=c_name)
                        signals.append(
                            SchemaSignal(
                                table=table,
                                column=c_name,
                                signal_type="boolean_flag",
                                suggested_predicate=pred,
                                description=f"Boolean state flag `{c_name}`: queries asking for active entities should check `{pred}`.",
                                confidence=0.75,
                                metadata={"column_type": c_type},
                            )
                        )
                        break

                # 5. Status / Lifecycle States
                if c_name.lower() in self.STATUS_COLUMN_NAMES:
                    signals.append(
                        SchemaSignal(
                            table=table,
                            column=c_name,
                            signal_type="status_enum",
                            suggested_predicate=None,
                            description=f"Status column `{table}.{c_name}` represents entity lifecycle states (e.g. active, paid, canceled, delivered). Verify question-specific filtering.",
                            confidence=0.70,
                            metadata={"column_type": c_type},
                        )
                    )

                # 6. Implicit Foreign Keys (naming convention without declared constraint)
                if (table, c_name) not in explicit_fks and c_name.endswith("_id") and c_name != "id":
                    prefix = c_name[:-3]
                    # Heuristic: prefix matches table name or plural form (e.g. invoice_id -> invoices, account_id -> accounts)
                    candidate_tables = [
                        t for t in all_tables 
                        if t != table and (
                            t == prefix 
                            or t == f"{prefix}s" 
                            or t == f"{prefix}es" 
                            or (prefix.endswith("y") and t == f"{prefix[:-1]}ies")
                        )
                    ]
                    for target_table in candidate_tables:
                        join_pred = f"{table}.{c_name} = {target_table}.id"
                        signals.append(
                            SchemaSignal(
                                table=table,
                                column=c_name,
                                signal_type="implicit_fk",
                                suggested_predicate=join_pred,
                                description=f"Undeclared foreign key join path: `{join_pred}`.",
                                confidence=0.80,
                                metadata={"target_table": target_table, "target_column": "id"},
                            )
                        )

        return signals

    def extract_from_engine(self, engine, db_name: Optional[str] = None) -> List[SchemaSignal]:
        """Extract schema signals directly from a live SQLAlchemy engine."""
        from sqlalchemy import inspect

        insp = inspect(engine)
        tables = insp.get_table_names()

        tables_metadata: Dict[str, List[Dict[str, Any]]] = {}
        foreign_keys: Dict[str, List[Dict[str, Any]]] = {}

        for table in tables:
            tables_metadata[table] = insp.get_columns(table)
            try:
                foreign_keys[table] = insp.get_foreign_keys(table)
            except Exception:
                foreign_keys[table] = []

        return self.extract_from_metadata(tables_metadata, foreign_keys)


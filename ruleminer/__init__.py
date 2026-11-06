"""RuleMiner: Automated rule discovery from database schemas and query logs.
"""

import os
from typing import Optional

from ruleminer.query_log_miner import MiningResults, QueryLogMiner
from ruleminer.schema_signals import SchemaSignal, SchemaSignalExtractor
from ruleminer.synthesizer import RuleSynthesizer, SynthesizedRule

__version__ = "0.1.0"
__all__ = [
    "SchemaSignal",
    "SchemaSignalExtractor",
    "QueryLogMiner",
    "MiningResults",
    "RuleSynthesizer",
    "SynthesizedRule",
    "mine_rules",
]


def mine_rules(
    db: str = "appdb",
    engine=None,
    query_log_path: Optional[str] = None,
    min_support: float = 0.5,
) -> RuleSynthesizer:
    """Convenience pipeline to mine rules for a database from schema signals and query logs."""
    # 1. Extract schema signals
    extractor = SchemaSignalExtractor()
    signals = []
    if engine is not None:
        try:
            signals = extractor.extract_from_engine(engine, db_name=db)
        except Exception:
            signals = []

    # 2. Extract from query logs if available
    mining_results = None
    if query_log_path and os.path.exists(query_log_path):
        miner = QueryLogMiner(min_support=min_support)
        mining_results = miner.mine_file(query_log_path)

    # 3. Synthesize
    synthesizer = RuleSynthesizer(schema_signals=signals, mining_results=mining_results)
    synthesizer.synthesize()
    return synthesizer


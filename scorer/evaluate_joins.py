import yaml
import re
from pathlib import Path

def normalize_edge(c1, c2):
    """Normalize a pair of column references into a canonical sorted tuple."""
    c1 = c1.strip().lower()
    c2 = c2.strip().lower()
    return tuple(sorted([c1, c2]))

def extract_ktx_joins(schema_yaml_path):
    with open(schema_yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    unique_edges = set()
    raw_joins = []
    
    tables = data.get('tables', {})
    for table_name, t_meta in tables.items():
        for j in t_meta.get('joins', []):
            on_expr = j.get('on', '')
            # Match patterns like: table1.col1 = table2.col2
            m = re.match(r'([\w\.]+)\s*=\s*([\w\.]+)', on_expr)
            if m:
                col_a = m.group(1).replace('public.', '')
                col_b = m.group(2).replace('public.', '')
                edge = normalize_edge(col_a, col_b)
                if edge not in unique_edges:
                    unique_edges.add(edge)
                    raw_joins.append({
                        'edge': edge,
                        'source': j.get('source'),
                        'relationship': j.get('relationship'),
                        'on': on_expr
                    })
    return unique_edges, raw_joins

def evaluate_db(db_name, ktx_schema_path, true_joins_data):
    db_truth = true_joins_data.get(db_name, [])
    
    core_truth = set()
    weak_truth = set()
    
    for item in db_truth:
        edge = normalize_edge(item['a'], item['b'])
        if item.get('kind') == 'weak':
            weak_truth.add(edge)
        else:
            core_truth.add(edge)
            
    all_truth = core_truth | weak_truth
    
    inferred_edges, raw_joins = extract_ktx_joins(ktx_schema_path)
    
    print(f"\n=======================================================")
    print(f"DATABASE: {db_name.upper()}")
    print(f"=======================================================")
    print(f"Ground-Truth Joins: {len(all_truth)} total ({len(core_truth)} core, {len(weak_truth)} weak)")
    print(f"ktx Inferred Unique Joins: {len(inferred_edges)}")
    
    print("\n--- ktx Inferred Joins ---")
    for r in sorted(raw_joins, key=lambda x: str(x['edge'])):
        status = "CORE MATCH" if r['edge'] in core_truth else ("WEAK MATCH" if r['edge'] in weak_truth else "EXTRA (NOT IN TRUTH)")
        print(f"  {r['edge'][0]} <--> {r['edge'][1]} [{status}]")
        
    print("\n--- Ground-Truth Coverage ---")
    for edge in sorted(all_truth):
        kind = "weak" if edge in weak_truth else "core"
        found = "FOUND" if edge in inferred_edges else "MISSED"
        print(f"  [{found}] ({kind}) {edge[0]} <--> {edge[1]}")

    # Mode 1: Core + Weak
    tp_all = len(inferred_edges & all_truth)
    fp_all = len(inferred_edges - all_truth)
    fn_all = len(all_truth - inferred_edges)
    prec_all = tp_all / (tp_all + fp_all) if (tp_all + fp_all) > 0 else 0
    rec_all = tp_all / (tp_all + fn_all) if (tp_all + fn_all) > 0 else 0
    f1_all = 2 * prec_all * rec_all / (prec_all + rec_all) if (prec_all + rec_all) > 0 else 0
    
    # Mode 2: Core only (weak joins in inferred set ignored from denominator or treated as FP)
    # Strict: weak joins treated as FP if not in core truth
    tp_core = len(inferred_edges & core_truth)
    fp_core = len(inferred_edges - core_truth)
    fn_core = len(core_truth - inferred_edges)
    prec_core = tp_core / (tp_core + fp_core) if (tp_core + fp_core) > 0 else 0
    rec_core = tp_core / (tp_core + fn_core) if (tp_core + fn_core) > 0 else 0
    f1_core = 2 * prec_core * rec_core / (prec_core + rec_core) if (prec_core + rec_core) > 0 else 0

    # Mode 3: Declared FKs vs Undeclared Joins
    declared_fks = set()
    undeclared_core = set()
    undeclared_all = set()
    
    for item in db_truth:
        edge = normalize_edge(item['a'], item['b'])
        if item.get('declared_fk'):
            declared_fks.add(edge)
        else:
            undeclared_all.add(edge)
            if item.get('kind') != 'weak':
                undeclared_core.add(edge)

    tp_declared = len(inferred_edges & declared_fks)
    rec_declared = tp_declared / len(declared_fks) if len(declared_fks) > 0 else None
    
    tp_undec_core = len(inferred_edges & undeclared_core)
    rec_undec_core = tp_undec_core / len(undeclared_core) if len(undeclared_core) > 0 else 0
    
    tp_undec_all = len(inferred_edges & undeclared_all)
    rec_undec_all = tp_undec_all / len(undeclared_all) if len(undeclared_all) > 0 else 0

    print("\n--- METRICS SUMMARY ---")
    print(f"Overall (Core + Weak):")
    print(f"  True Positives : {tp_all}")
    print(f"  False Positives: {fp_all}")
    print(f"  False Negatives: {fn_all}")
    print(f"  Precision      : {prec_all:.1%} ({tp_all}/{tp_all + fp_all})")
    print(f"  Recall         : {rec_all:.1%} ({tp_all}/{tp_all + fn_all})")
    print(f"  F1 Score       : {f1_all:.3f}")
    
    print(f"\nOverall Core Only (Strict):")
    print(f"  True Positives : {tp_core}")
    print(f"  False Positives: {fp_core} (includes any weak or extra joins)")
    print(f"  False Negatives: {fn_core}")
    print(f"  Precision      : {prec_core:.1%} ({tp_core}/{tp_core + fp_core})")
    print(f"  Recall         : {rec_core:.1%} ({tp_core}/{tp_core + fn_core})")
    print(f"  F1 Score       : {f1_core:.3f}")

    print(f"\nDeclared vs Undeclared Joins Breakdown:")
    if declared_fks:
        print(f"  Declared FK Recall        : {rec_declared:.1%} ({tp_declared}/{len(declared_fks)})")
    else:
        print(f"  Declared FK Recall        : N/A (0 declared FKs in schema)")
    print(f"  Undeclared Core Recall    : {rec_undec_core:.1%} ({tp_undec_core}/{len(undeclared_core)})")
    print(f"  Undeclared All Recall     : {rec_undec_all:.1%} ({tp_undec_all}/{len(undeclared_all)})")
    
    return {
        'all': {'tp': tp_all, 'fp': fp_all, 'fn': fn_all, 'p': prec_all, 'r': rec_all, 'f1': f1_all},
        'core': {'tp': tp_core, 'fp': fp_core, 'fn': fn_core, 'p': prec_core, 'r': rec_core, 'f1': f1_core},
        'undeclared_core': {'tp': tp_undec_core, 'total': len(undeclared_core), 'r': rec_undec_core},
        'declared': {'tp': tp_declared, 'total': len(declared_fks), 'r': rec_declared}
    }

def main():
    with open('questions/true_joins.yaml', 'r', encoding='utf-8') as f:
        true_joins = yaml.safe_load(f)
        
    olist_res = evaluate_db('olist', 'layers/ktx/olist/semantic-layer/olist/_schema/public.yaml', true_joins)
    appdb_res = evaluate_db('appdb', 'layers/ktx/appdb_v2/semantic-layer/appdb/_schema/public.yaml', true_joins)

if __name__ == '__main__':
    main()

# dbeval analysis (question-level)

Source: `results/raw/suite_results_all.csv`. Rows dropped for infrastructure errors: 0.


## appdb  (32 questions)

| system | questions passed | accuracy | flaky questions* |
|---|---|---|---|
| baseline | 4/32 | 12.5% | 0 |
| baseline_rules | 28/32 | 87.5% | 2 |
| datus | 5/32 | 15.6% | 0 |
| datus_reviewed | 26.3333/32 | 82.3% | 3 |
| datus_reviewed_defonly | 25.3333/32 | 79.2% | 4 |
| ktx | 4/32 | 12.5% | 0 |
| ktx_reviewed | 26.3333/32 | 82.3% | 3 |
| schema_only | 3/32 | 9.4% | 0 |
| schema_true_joins | 4/32 | 12.5% | 0 |
| wren | 4/32 | 12.5% | 0 |
| wren_reviewed | 28/32 | 87.5% | 3 |
| wren_reviewed_unresolved | 25/32 | 78.1% | 8 |

*flaky = passed in some runs but not all.


Paired comparison against `baseline` (question score: pass rate across runs):

| system | fixed (tool right, baseline wrong) | broke (baseline right, tool wrong) | net questions | diff (points) | 95% bootstrap interval | sign-test p |
|---|---|---|---|---|---|---|
| baseline_rules | 25 | 0 | +24 | +75.0 | [+60.9, +89.1] | 0.000 |
| datus | 1 | 0 | +1 | +3.1 | [+0.0, +9.4] | 1.000 |
| datus_reviewed | 25 | 1 | +22.3333 | +69.8 | [+52.1, +86.5] | 0.000 |
| datus_reviewed_defonly | 24 | 1 | +21.3333 | +66.7 | [+47.9, +83.3] | 0.000 |
| ktx | 0 | 0 | +0 | +0.0 | [+0.0, +0.0] | 1.000 |
| ktx_reviewed | 24 | 0 | +22.3333 | +69.8 | [+54.2, +84.4] | 0.000 |
| schema_only | 0 | 1 | -1 | -3.1 | [-9.4, +0.0] | 1.000 |
| schema_true_joins | 0 | 0 | +0 | +0.0 | [+0.0, +0.0] | 1.000 |
| wren | 0 | 0 | +0 | +0.0 | [+0.0, +0.0] | 1.000 |
| wren_reviewed | 25 | 0 | +24 | +75.0 | [+60.4, +88.5] | 0.000 |
| wren_reviewed_unresolved | 25 | 1 | +21 | +65.6 | [+50.0, +80.2] | 0.000 |

One question is worth 3.1 points on this database. An interval that includes 0, or p above 0.05, means the difference is not distinguishable from noise.


## olist  (18 questions)

| system | questions passed | accuracy | flaky questions* |
|---|---|---|---|
| baseline | 13/18 | 72.2% | 0 |
| baseline_rules | 15/18 | 83.3% | 0 |
| datus | 13/18 | 72.2% | 2 |
| datus_reviewed | 16.3333/18 | 90.7% | 1 |
| datus_reviewed_defonly | 14.6667/18 | 81.5% | 1 |
| ktx | 14/18 | 77.8% | 0 |
| ktx_reviewed | 15/18 | 83.3% | 0 |
| schema_only | 11/18 | 61.1% | 0 |
| schema_true_joins | 12.5/18 | 69.4% | 1 |
| wren | 14/18 | 77.8% | 2 |
| wren_reviewed | 14/18 | 77.8% | 2 |
| wren_reviewed_unresolved | 13.3333/18 | 74.1% | 2 |

*flaky = passed in some runs but not all.


Paired comparison against `baseline` (question score: pass rate across runs):

| system | fixed (tool right, baseline wrong) | broke (baseline right, tool wrong) | net questions | diff (points) | 95% bootstrap interval | sign-test p |
|---|---|---|---|---|---|---|
| baseline_rules | 3 | 1 | +2 | +11.1 | [-11.1, +33.3] | 0.625 |
| datus | 2 | 3 | +0 | +0.0 | [-19.4, +22.2] | 1.000 |
| datus_reviewed | 5 | 2 | +3.33333 | +18.5 | [-7.4, +44.4] | 0.453 |
| datus_reviewed_defonly | 3 | 2 | +1.66667 | +9.3 | [-13.0, +31.5] | 1.000 |
| ktx | 2 | 1 | +1 | +5.6 | [-11.1, +22.2] | 1.000 |
| ktx_reviewed | 2 | 0 | +2 | +11.1 | [+0.0, +27.8] | 0.500 |
| schema_only | 0 | 2 | -2 | -11.1 | [-27.8, +0.0] | 0.500 |
| schema_true_joins | 0 | 1 | -0.5 | -2.8 | [-8.3, +0.0] | 1.000 |
| wren | 2 | 2 | +1 | +5.6 | [-11.1, +25.0] | 1.000 |
| wren_reviewed | 3 | 2 | +1 | +5.6 | [-14.8, +27.8] | 1.000 |
| wren_reviewed_unresolved | 3 | 2 | +0.333333 | +1.9 | [-20.4, +22.2] | 1.000 |

One question is worth 5.6 points on this database. An interval that includes 0, or p above 0.05, means the difference is not distinguishable from noise.

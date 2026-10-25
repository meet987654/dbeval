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


Paired comparison against `baseline_rules` (question score: pass rate across runs):

| system | fixed (tool right, baseline wrong) | broke (baseline right, tool wrong) | net questions | diff (points) | 95% bootstrap interval | sign-test p |
|---|---|---|---|---|---|---|
| baseline | 0 | 25 | -24 | -75.0 | [-89.1, -60.9] | 0.000 |
| datus | 0 | 24 | -23 | -71.9 | [-85.9, -56.2] | 0.000 |
| datus_reviewed | 2 | 4 | -1.66667 | -5.2 | [-15.1, +3.6] | 0.688 |
| datus_reviewed_defonly | 2 | 6 | -2.66667 | -8.3 | [-19.8, +2.1] | 0.289 |
| ktx | 0 | 25 | -24 | -75.0 | [-89.1, -60.9] | 0.000 |
| ktx_reviewed | 1 | 4 | -1.66667 | -5.2 | [-13.0, +1.6] | 0.375 |
| schema_only | 0 | 26 | -25 | -78.1 | [-90.6, -64.1] | 0.000 |
| schema_true_joins | 0 | 25 | -24 | -75.0 | [-89.1, -60.9] | 0.000 |
| wren | 0 | 25 | -24 | -75.0 | [-89.1, -60.9] | 0.000 |
| wren_reviewed | 2 | 3 | +0 | +0.0 | [-5.2, +5.7] | 1.000 |
| wren_reviewed_unresolved | 2 | 7 | -3 | -9.4 | [-18.8, -1.0] | 0.180 |

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


Paired comparison against `baseline_rules` (question score: pass rate across runs):

| system | fixed (tool right, baseline wrong) | broke (baseline right, tool wrong) | net questions | diff (points) | 95% bootstrap interval | sign-test p |
|---|---|---|---|---|---|---|
| baseline | 1 | 3 | -2 | -11.1 | [-33.3, +11.1] | 0.625 |
| datus | 0 | 3 | -2 | -11.1 | [-25.0, +0.0] | 0.250 |
| datus_reviewed | 2 | 1 | +1.33333 | +7.4 | [-7.4, +25.9] | 1.000 |
| datus_reviewed_defonly | 0 | 1 | -0.333333 | -1.9 | [-5.6, +0.0] | 1.000 |
| ktx | 0 | 1 | -1 | -5.6 | [-16.7, +0.0] | 1.000 |
| ktx_reviewed | 1 | 1 | +0 | +0.0 | [-16.7, +16.7] | 1.000 |
| schema_only | 0 | 4 | -4 | -22.2 | [-44.4, -5.6] | 0.125 |
| schema_true_joins | 1 | 3 | -2.5 | -13.9 | [-33.3, +2.8] | 0.625 |
| wren | 1 | 2 | -1 | -5.6 | [-19.4, +5.6] | 1.000 |
| wren_reviewed | 1 | 3 | -1 | -5.6 | [-22.2, +11.1] | 0.625 |
| wren_reviewed_unresolved | 0 | 3 | -1.66667 | -9.3 | [-22.2, +0.0] | 0.250 |

One question is worth 5.6 points on this database. An interval that includes 0, or p above 0.05, means the difference is not distinguishable from noise.

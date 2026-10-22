# dbeval analysis (question-level)

Source: `results/raw/suite_results_with_controls.csv`. Rows dropped for infrastructure errors: 0.


## appdb  (32 questions)

| system | questions passed | accuracy | flaky questions* |
|---|---|---|---|
| baseline | 5/32 | 15.6% | 1 |
| baseline_rules | 19/32 | 59.4% | 1 |
| datus | 5/32 | 15.6% | 0 |
| ktx | 4/32 | 12.5% | 0 |
| schema_only | 3/32 | 9.4% | 0 |
| schema_true_joins | 4/32 | 12.5% | 0 |
| wren | 4/32 | 12.5% | 0 |

*flaky = passed in some runs but not all.


Paired comparison against `baseline` (a question counts as passed if it passed in most runs):

| system | fixed (tool right, baseline wrong) | broke (baseline right, tool wrong) | net questions | diff (points) | 95% bootstrap interval | sign-test p |
|---|---|---|---|---|---|---|
| baseline_rules | 14 | 0 | +14 | +43.8 | [+28.1, +62.5] | 0.000 |
| datus | 0 | 0 | +0 | +0.0 | [+0.0, +0.0] | 1.000 |
| ktx | 0 | 1 | -1 | -3.1 | [-9.4, +0.0] | 1.000 |
| schema_only | 0 | 2 | -2 | -6.2 | [-15.6, +0.0] | 0.500 |
| schema_true_joins | 0 | 1 | -1 | -3.1 | [-9.4, +0.0] | 1.000 |
| wren | 0 | 1 | -1 | -3.1 | [-9.4, +0.0] | 1.000 |

One question is worth 3.1 points on this database. An interval that includes 0, or p above 0.05, means the difference is not distinguishable from noise.


## olist  (18 questions)

| system | questions passed | accuracy | flaky questions* |
|---|---|---|---|
| baseline | 13/18 | 72.2% | 2 |
| baseline_rules | 15/18 | 83.3% | 1 |
| datus | 14/18 | 77.8% | 1 |
| ktx | 14/18 | 77.8% | 0 |
| schema_only | 12/18 | 66.7% | 0 |
| schema_true_joins | 12/18 | 66.7% | 0 |
| wren | 14/18 | 77.8% | 0 |

*flaky = passed in some runs but not all.


Paired comparison against `baseline` (a question counts as passed if it passed in most runs):

| system | fixed (tool right, baseline wrong) | broke (baseline right, tool wrong) | net questions | diff (points) | 95% bootstrap interval | sign-test p |
|---|---|---|---|---|---|---|
| baseline_rules | 3 | 1 | +2 | +11.1 | [-11.1, +33.3] | 0.625 |
| datus | 2 | 1 | +1 | +5.6 | [-11.1, +22.2] | 1.000 |
| ktx | 2 | 1 | +1 | +5.6 | [-11.1, +22.2] | 1.000 |
| schema_only | 0 | 1 | -1 | -5.6 | [-16.7, +0.0] | 1.000 |
| schema_true_joins | 0 | 1 | -1 | -5.6 | [-16.7, +0.0] | 1.000 |
| wren | 2 | 1 | +1 | +5.6 | [-11.1, +22.2] | 1.000 |

One question is worth 5.6 points on this database. An interval that includes 0, or p above 0.05, means the difference is not distinguishable from noise.

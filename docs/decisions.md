# Engineering decisions

## 2026-11-03 — Initial architecture

- Use a `src/mlexp` package, Python 3.11+, scikit-learn, MLflow, PyYAML, Pydantic,
  and the standard-library argparse CLI. Keep the first implementation small.
- Use the MIT license for reuse and contribution to the open-source project.
- Limit M1 input to built-in Iris and Diabetes numerical datasets. External CSV
  and categorical preprocessing belong to M2.
- Use logistic regression and ridge as useful baselines, plus task-specific dummy
  models. Parameters are explicit configuration, with no search in M1.
- Reserve a seeded test partition first. Use stratified folds for classification
  and shuffled K-fold for regression, on the training partition only. Fit a fresh
  pipeline for each fold; refit on all training rows before final evaluation.
- Report accuracy and macro F1 for classification; RMSE, MAE, and R² for regression.
  Compare using CV accuracy (higher is better) or CV RMSE (lower is better).
- Use MLflow's existing tracking client, search, and artifact APIs. Store metadata
  in local SQLite and artifacts on local disk by default. Do not build a competing
  tracking database, model registry, or dashboard.
- Persist the fitted pipeline with MLflow's scikit-learn flavor. Serialized model
  artifacts must only be loaded when their provenance is trusted.
- Use explicit client instances rather than changing global tracking configuration.
  Log run failures and never present a partially completed run as successful.
- Compare only matching dataset content, task, seed/split, fold count, and scoring
  protocol. Reports may show final test scores; comparison ranks only by CV scores.
- Reproducibility means matching partitions and results within the same dependency
  environment; cross-platform and cross-version bitwise identity is not promised.
- Constrain threadpoolctl to 3.6 on Windows: 3.7's DLL discovery produced corrupted
  Unicode paths during actual experiment tests. Keep other platforms unconstrained
  beyond scikit-learn's requirements. Add a Windows CI job in a Unicode checkout;
  revisit this bound after verifying an upstream fix. No third-party files are patched.
- Set MLflow model serialization explicitly to cloudpickle for stable behavior across
  MLflow 3 releases; record its runtime dependencies. Loading requires trusted artifacts.

References: [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html)
and [MLflow tracking APIs](https://mlflow.org/docs/latest/ml/tracking/).

## 2026-11-03 — MVP continuation and CSV input

- Use the persistent `autonomous-dev` branch, created from the verified initial
  implementation. Preserve local history and existing artifacts. Do not publish.
- Complete the existing M2–M4 roadmap without adding unrelated capabilities.
- Require explicit numeric/categorical feature lists and a target for CSV input.
  Exact header/schema matching prevents accidental inclusion of an index or target.
  Reject malformed records, missing targets, nonnumeric numeric columns, and infinity.
- Read CSV bytes once for both parsing and fingerprinting. Resolve CSV paths relative
  to YAML, while tracking database paths remain relative to the working directory.
- Use a ColumnTransformer inside the pipeline for fold-local median imputation,
  scaling, categorical missing markers, and one-hot encoding with unknown categories
  ignored. Preserve all-missing columns; never drop rows or infer feature roles from
  held-out values. Validation of data types is deterministic schema checking.
- Advance the evaluation protocol to version 2 to record feature/target schemas.
  Older runs remain available to reports, but comparisons across protocols are rejected.

## 2026-11-03 — Bounded parameter selection

- Use scikit-learn GridSearchCV over the entire pipeline, with fixed, seeded
  training-only folds. Use the task's existing primary CV metric and one training
  refit; reserve the single held-out prediction for final evaluation.
- Bound grids to 8 values per parameter, 32 candidates, and 128 CV fits plus refit.
  Reject unknown, invalid, duplicate, empty, or oversized search spaces before work.
- Preserve requested parameters separately from resolved selected parameters. Track
  every candidate's fold scores, mean/std, rank, and the refit row count.
- Protocol version 3 includes this selection contract. Fixed and searched runs may
  be compared when data/folds/scoring/environment match. Selected CV scores can be
  optimistic after search; document their limits rather than use final test scores
  for ranking. Older protocol runs are preserved and reportable.

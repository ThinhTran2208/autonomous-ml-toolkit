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

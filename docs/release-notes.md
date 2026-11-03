# Release notes

## 0.2.0 — Local MVP candidate

- CPU-only classification/regression with strict safe YAML configuration.
- Built-in Iris and raw Diabetes datasets, plus explicitly typed CSV features.
- Fold-local imputation, scaling, categorical encoding, and seeded baselines.
- Bounded training-only grid search with one training refit and final evaluation.
- MLflow configuration, schema/fingerprint, exact split/fold, environment, model,
  selected parameters, candidate results, and final/CV metric tracking.
- `mlexp run`, `compare`, and `report`, with compatibility checks, CV-only ranking,
  failed-run exclusion, and report overwrite protection.
- Source regression tests, independent installed-wheel acceptance, and a shared
  local/CI verification command covering actual CLI smoke workflows.
- Windows threadpoolctl compatibility bound for Unicode dependency paths.

Known limitations: IID row splits only, small/dense tabular data, local SQLite
tracking only, trusted serialized model provenance required, and no production
deployment, GPU work, or package publication. Consult docs/progress.md for actual
executed validation and hosted CI limitations before any release.

## 0.1.0 — Initial local foundation

Built-in fixed-model experiments, local tracking, CLI commands, engineering
guidance, and initial tests. No package was published.

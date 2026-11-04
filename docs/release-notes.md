# Release notes

## Post-0.3.0 — F-01 fix (unpublished)

- Preserve the CLI console encoding and escape unrepresentable output characters.
  Writing a report to a Unicode path now returns success under redirected ASCII
  and cp1252 output; UTF-8 output continues to display the original path.
- Keep UTF-8 report content and exclusive creation/overwrite protection unchanged.
- The historical v0.3.0 independent audit remains CONDITIONAL PASS. This developer
  fix and its regression verification do not constitute a new independent audit.

## 0.3.0 — Verified dataset-agnostic CSV assurance (unpublished)

- YAML-configurable separate validation fraction and logged validation metrics;
  CV/search/preprocessing/final refit remain confined to training rows.
- Protocol 4 records train/validation/test rows and diagnostic validation roles;
  existing runs remain reportable, with cross-protocol ranking rejected.
- Independent installed-wheel CLI acceptance for full Iris, Breast Cancer Wisconsin,
  and California Housing CSVs, mixed features/missing values, and metric oracles.
- Targeted leakage and reproducibility tests for fixed and searched models on both tasks.
- California Housing acceptance downloads are cached locally and excluded from Git.

## 0.2.0 — Verified MVP (unpublished)

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

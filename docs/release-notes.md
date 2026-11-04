# Release notes

## 0.3.0 — Stable MVP with dataset-agnostic CSV assurance

- YAML-configurable separate validation fraction and logged validation metrics;
  CV/search/preprocessing/final refit remain confined to training rows.
- Protocol 4 records train/validation/test rows and diagnostic validation roles;
  existing runs remain reportable, with cross-protocol ranking rejected.
- Independent installed-wheel CLI acceptance for full Iris, Breast Cancer Wisconsin,
  and California Housing CSVs, mixed features/missing values, and metric oracles.
- Targeted leakage and reproducibility tests for fixed and searched models on both tasks.
- California Housing acceptance downloads are cached locally and excluded from Git.
- Include the F-01 correction in this initial v0.3.0 release; version 0.3.0 had
  not previously been officially published. Preserve the CLI console encoding
  and escape unrepresentable output characters. Writing a report to a Unicode
  path returns success under redirected ASCII and cp1252 output; UTF-8 output
  continues to display the original path. UTF-8 report content and exclusive
  creation/overwrite protection are unchanged.

Audit scope: the [historical independent audit](audits/mvp-v0.3.0-independent-audit.md)
returned **CONDITIONAL PASS**, with the Low severity F-01 finding. Its report is
preserved unchanged. The subsequent independent focused re-audit of implementation
commit `59c9a5fe1702b5b85c17ccf55871f1c977bcb1de` returned **PASS**, as confirmed
in the release authorization. This release preparation changes documentation only;
it is not a new independent code audit and does not expand the audited MVP scope.

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

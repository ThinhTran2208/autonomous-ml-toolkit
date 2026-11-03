# Engineering instructions

Work only in this repository. Build a small, reusable CPU-only Python toolkit for
tabular classification and regression. Prefer scikit-learn pipelines and MLflow
APIs to custom infrastructure. Do not introduce paid services or deployment code.

## Evaluation contract

- Split the held-out test set before fitting any learned transformation.
- Put imputation, scaling, and estimators inside a scikit-learn pipeline.
- Fit preprocessing separately inside every training-only cross-validation fold.
- Use cross-validation metrics for model comparison and future parameter selection.
- Use held-out data only for final evaluation. Never select models, parameters,
  thresholds, or features using test scores. Repeated inspection of test scores
  invalidates their interpretation as an untouched final estimate.
- Seed splits, cross-validation, and stochastic estimators explicitly. Log the
  resolved configuration, dataset/split identity, package versions, and metrics.

## Workflow

- Read docs/roadmap.md, docs/decisions.md, and docs/progress.md before changing scope.
- Keep configuration strict; reject unknown keys and incompatible task/model pairs.
- Keep generated MLflow stores, environments, and reports out of version control.
- Add meaningful tests for behavior, failure paths, reproducibility, and leakage.
- Run `.venv/Scripts/python -m pytest` (Windows) or `.venv/bin/python -m pytest`
  (POSIX), `ruff check .`, and `ruff format --check .` before committing.
- Use a task branch. Never push to main, rewrite remote history, or delete data.
- Record executed commands, actual results, limitations, and blockers in
  docs/progress.md. Do not describe unexecuted checks as passing.
- Keep changes focused. No credentials, local machine paths, or private preferences
  in commits. Do not load untrusted serialized model artifacts.

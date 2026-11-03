# Roadmap and acceptance criteria

The original MVP covers M0–M4 below and has verified completion evidence.
The user subsequently authorized M5: dataset-agnostic CSV assurance and explicit
validation partitions, within the same tabular MVP scope. The persistent
source-of-truth branch remains `autonomous-dev`. See docs/progress.md for status.
M0–M5 are now verified complete. Further feature work requires a new authorized
milestone; existing datasets, runs, and local completion tags are preserved.

## M0 — Engineering foundation

Acceptance:
- Repository instructions, this roadmap, decision records, and progress log exist.
- Installable `src/` package, strict YAML configuration, Ruff, pytest, and CI exist.
- A clean development install succeeds: `python -m pip install -e ".[dev]"`.
- `ruff check .` and `ruff format --check .` pass.

## M1 — Small functional experiment

Acceptance:
- `mlexp run examples/iris.yaml` and `mlexp run examples/diabetes.yaml` finish on
  built-in datasets without downloading data or using a GPU.
- Logistic regression / ridge and dummy baselines are configurable with explicit
  seeds. Numeric imputation and scaling are fitted only on training data.
- Training-only cross-validation precedes a single held-out prediction pass.
- MLflow records configuration, parameters, CV/final metrics, split identities,
  dependency versions, and a fitted pipeline artifact in a local store.
- `mlexp compare --experiment iris-baseline` shows completed runs ordered by
  training-only CV performance; final scores cannot be used as sort keys.
- `mlexp report RUN_ID` renders the tracked run without retraining.
- Tests cover both tasks, baseline models, CLI commands, invalid configuration,
  deterministic partitions/results, MLflow persistence, and preprocessing leakage.
- `python -m pytest`, `ruff check .`, and `ruff format --check .` pass locally.
- CI runs those commands on Linux Python 3.11, 3.12, and 3.13.
- A Windows Python 3.12 CI job exercises a Unicode checkout path.

## M2 — User-provided tabular datasets

Acceptance:
- CSV loading with explicit target, missing-value policy, numeric/categorical
  feature handling, and input schema validation.
- Content fingerprints and target/feature schema are tracked.
- Missing targets, duplicate columns, absent targets, and incompatible types fail
  with actionable errors; no silent row dropping.
- `python -m pytest tests/test_data.py tests/test_csv_experiment.py` passes with
  fixtures for mixed types, unseen categories, missing values, and target leakage.
- Full pytest and Ruff checks pass; CSV CLI examples are documented and executed.

## M3 — Training-only model selection

Acceptance:
- Bounded parameter search runs exclusively within the training partition and
  pipeline; selected model is evaluated on held-out data once.
- Search space, scorer, fold scores, selected parameters, and refit are tracked.
- Comparison rejects incompatible dataset/split/task/scoring protocols.
- `python -m pytest tests/test_selection.py` verifies disjoint selection/test rows
  using instrumented estimators and deliberately adversarial test targets.
- Full pytest and Ruff checks pass; selection example is executed.

## M4 — Reliability and release readiness

Acceptance:
- Public API and CLI behavior, metric interpretation, reproducibility limits,
  contribution workflow, and local MLflow UI usage are documented.
- Packaging builds and installs from a wheel in a clean environment.
- `python -m build`, `python -m pytest`, `ruff check .`, and
  `ruff format --check .` pass; wheel CLI smoke checks run in CI.
- Dependency update and compatibility policy, license choice, and release notes
  are recorded before any published release.

## M5 — Dataset-agnostic CSV and three-way evaluation

Acceptance:
- Arbitrary compatible classification/regression CSV input requires YAML changes
  only: configurable target, numeric/categorical predictors, and missing policy.
- Configurable `test_size` and optional `validation_size` reserve disjoint seeded
  partitions; their remaining rows train. Invalid sizes/class counts fail early.
- All preprocessing, CV, search, and final fitting exclude validation/test rows.
  Comparison uses CV only; validation diagnostics and final test metrics are tracked.
- `python -m pytest tests/test_validation.py tests/test_config.py` verifies exact
  fitting rows, deterministic splits, rejected input, and adversarial held-out data.
- Independent installed-wheel CLI run/compare/report acceptance passes on full
  Iris, Breast Cancer Wisconsin, and California Housing CSV exports, including
  mixed features and missing values. All CV/validation/test metrics are independently
  reconstructed; saved preprocessing statistics match training rows only.
- `python scripts/verify.py` passes lint, format, full source tests, build, fresh
  wheel install, independent acceptance, and both documented CSV CLI smoke tests.
- README documents YAML-only usage, split semantics, metric roles, and the cached
  California Housing acceptance download. No datasets or model artifacts are pushed.
- Verified code is committed and synchronized only to `origin/autonomous-dev`.

The progress log records actual verification evidence and remaining limitations.

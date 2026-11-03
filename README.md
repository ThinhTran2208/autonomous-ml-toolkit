# ML Experiment & Evaluation Toolkit

A small CPU-only Python toolkit for reproducible tabular classification and
regression, with YAML configuration and local MLflow tracking.

Supports built-in Iris and Diabetes datasets, explicitly typed CSV datasets,
logistic regression, ridge, and dummy baselines. See [the roadmap](docs/roadmap.md)
for milestone acceptance criteria.

## Quick start

Use Python 3.11–3.13 (3.12 recommended for development).

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell, instead:
# .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"

mlexp run examples/iris.yaml
mlexp run examples/iris-dummy.yaml
mlexp run examples/diabetes.yaml
mlexp run examples/diabetes-dummy.yaml
mlexp compare --experiment iris-baseline
mlexp compare --experiment diabetes-baseline
mlexp report RUN_ID
mlexp report RUN_ID --output reports/run.md
```

`run` prints JSON containing the run ID and metrics. Replace `RUN_ID` with that
ID. `compare` prints JSON ordered by training-only CV accuracy (descending) or CV
RMSE (ascending). `report` reads MLflow metadata and never retrains. Report files
are created exclusively; an existing file is never overwritten.

Run all commands from the repository root for the examples. Relative tracking
database paths are relative to the current working directory, including when a
config file lives elsewhere. The default backend is `sqlite:///mlflow.db`, with
artifacts in `mlartifacts/mlflow/`. Both are ignored by Git. To use another local
database, set `tracking_uri` in YAML and pass the same `--tracking-uri` to
`compare` and `report`. Remote stores and in-memory databases are outside M1.

When upgrading an existing workspace, preserve its tracking store. Version 0.3.0
uses evaluation protocol 4 and refuses to rank historic runs from another protocol
or dependency environment. Use a new experiment name or set `tracking_uri` to a
fresh SQLite database in the new configs and pass that URI to compare/report.
Existing runs remain available through `report` with their original database URI.

Use MLflow's existing interface for deeper inspection:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1
```

## Configuration

```yaml
experiment: iris-baseline
task: classification
dataset: iris
model: logistic_regression
seed: 42
test_size: 0.2
cv_folds: 5
parameters:
  C: 1.0
  max_iter: 1000
tracking_uri: sqlite:///mlflow.db
```

| Task | Dataset | Models | Supported parameters |
| --- | --- | --- | --- |
| Classification | `iris` or compatible CSV | `logistic_regression`, `dummy` | `C`, `max_iter` for logistic regression |
| Regression | `diabetes` or compatible CSV | `ridge`, `dummy` | `alpha` for ridge |

For a dummy baseline, set `model: dummy` and `parameters: {}`. Classification
predicts the most frequent training class; regression predicts the training mean.
Parameters must be positive finite numbers; `max_iter` must be integral. Other
model parameters use scikit-learn defaults and are recorded in MLflow. Unknown
keys, unsupported task/model combinations, bad split sizes, and invalid fold
counts fail explicitly. YAML is loaded with safe constructors.

## CSV input

Use `examples/csv-classification.yaml` or `examples/csv-regression.yaml` for
complete examples with small fabricated datasets checked into this repository:

```bash
mlexp run examples/csv-classification.yaml
mlexp run examples/csv-regression.yaml
```

To use any compatible tabular CSV, change only the YAML configuration; there is
no dataset registration or Python code to edit. Set `task` to `classification`
with `model: logistic_regression` (or `dummy`), or `regression` with `model: ridge`
(or `dummy`). Choose the target and feature columns in the dataset schema:

```yaml
experiment: custom-classification
task: classification
model: logistic_regression
seed: 42
test_size: 0.2
validation_size: 0.2
cv_folds: 5
dataset:
  type: csv
  path: data/custom.csv
  target: label
  numeric_features: [age, income]
  categorical_features: [region]
  missing_values: impute
tracking_uri: sqlite:///custom.db
```

Save this as `experiment.yaml`, put the CSV at `data/custom.csv` beside that YAML,
then run `mlexp run experiment.yaml`. Both task types use the same CSV loader and
pipeline architecture. All feature names and the target are configurable.

CSV paths resolve relative to the YAML file. CSV headers must match the listed
features and target exactly; duplicate, absent, unnamed, or unexpected columns
and malformed rows are errors. The target cannot appear among predictors.
Blank/whitespace fields are missing; strings such as `NA` remain literal values.
Targets are never imputed, and no rows are silently removed. Regression targets
and numeric features must contain finite numeric values (features may be missing).
Classification targets are string labels and must contain at least two classes.

With `missing_values: impute`, numerical columns use training medians and scaling;
a numerical column empty in a training fold is filled with zero. Categorical
missing values use `__mlexp_missing__`, with one-hot encoding learned inside each
fold. Unseen categories are ignored on transformation. Set `missing_values: error`
to reject missing feature values instead. Either feature list may be empty,
but at least one predictor is required. Dense one-hot encoding targets small
tabular datasets; very high-cardinality data is outside this MVP.

CSV bytes are read once and fingerprinted together with the explicit schema.
The target/feature schema is recorded in the MLflow split and protocol artifacts.

## Train, validation, and test splits

`test_size` (default `0.2`) and `validation_size` (default `0.0`) are fractions
of all rows. Both must be finite, test size must be positive, validation size
must be nonnegative, and their sum must be less than one. The remainder is the
training fraction: `0.2` test and `0.2` validation gives approximately 60/20/20.
Counts round up when reserving each partition; train receives the remaining rows.
The test partition is reserved first, then validation is split from the remainder
using `validation_size / (1 - test_size)`. Classification stratifies both splits;
all splits use `seed`. Insufficient rows or class counts fail explicitly.

Cross-validation and optional parameter search run inside the training partition
only. After a final fit on training rows, the pipeline predicts validation rows
once (if configured), then test rows once. Validation metrics are diagnostic;
they do not drive automatic selection or ranking. Neither validation nor test
rows enter any preprocessing fit or final refit. `validation_*` and `test_*`
metrics are logged separately, along with exact row identities and counts.
With `validation_size: 0.0`, the original train/test plus training-only CV workflow
remains available; no `validation_*` metrics are emitted.

## Training-only parameter search

Add an optional search grid using the same model parameter names:

```yaml
search:
  parameter_grid:
    C: [0.1, 1.0, 10.0]
```

```bash
mlexp run examples/iris-search.yaml
mlexp run examples/diabetes-search.yaml
```

The grid is limited to 8 distinct values per parameter, 32 combinations, and
128 CV fits plus one final refit. It uses the reserved training rows exclusively,
with a freshly fitted preprocessing pipeline in every fold. Selection maximizes
CV accuracy for classification and minimizes CV RMSE for regression. Ties retain
scikit-learn's deterministic candidate order. Grid values override corresponding
fixed `parameters`; dummy models have no searchable parameters.

The selected estimator is refitted once on all training rows and evaluated on
held-out rows once. `selection.json` records the grid, scorer, all candidate fold
scores, ranks, chosen parameters, and refit row count. `cv_*` values describe the
chosen candidate; searching can make these scores optimistic, so they are selection
statistics rather than an unbiased generalization estimate. Reports retain final
test scores for final assessment only. No search parameter can reference them.

## Evaluation and reproducibility

1. Load data without learned preprocessing. Diabetes uses `scaled=False` to avoid
   its loader's default full-dataset scaling.
2. Reserve seeded test and optional validation partitions; stratify classification.
3. Cross-validate only training rows with seeded shuffled folds. Each fold fits
   its own median imputer, standard scaler, and estimator inside a pipeline.
4. Refit on training rows, calculate optional validation diagnostics, then predict
   the held-out test rows once for final metrics. Never refit on validation rows.

Classification reports accuracy and macro F1. Regression reports RMSE, MAE, and
R². `cv_*` values are the unweighted mean of validation-fold scores; `*_std` is
the population standard deviation across folds. RMSE/MAE are positive losses;
lower is better. Each regression validation/test partition needs at least two
rows (including a configured separate validation partition). Every classification
training class needs at least `cv_folds` rows.

`compare` accepts only finished runs with identical dataset contents, partitions,
folds, scoring protocol, and recorded dependency versions. Use separate experiment
names for different protocols. Its ordering never uses test metrics. These small
toy datasets demonstrate the workflow; their scores are not evidence of broad
model quality.

**Test scores are final evaluation only.** Do not choose models, parameters,
features, or thresholds from them. If you iterate after viewing test results,
reserve a new independent final dataset for an unbiased estimate.

Every run stores the resolved configuration, dataset hash, exact split and fold
indices, package versions, per-fold scores, model defaults, and fitted pipeline.
Seeds reproduce partitions and results within the same dependency environment;
floating-point results may vary by platform/version. Only load serialized model
artifacts you trust. The toolkit never loads a model while comparing/reporting.

## Development

```bash
python -m pytest
ruff check .
ruff format --check .
python -m build
python scripts/verify.py
```

`scripts/verify.py` is the shared local/CI acceptance command. It runs source
checks, builds a wheel, installs it in a fresh environment, runs the independent
built-in-dataset acceptance suite outside the source tree, and smoke-tests the
CSV CLI workflows. Logs, environments, stores, and reports are preserved under
ignored `.cache/verification/` directories. A run succeeds only if every check
passes. It requires dependency downloads but uses no paid services.

Independent wheel acceptance exports the full Iris (150 rows), Breast Cancer
Wisconsin (569 rows), and California Housing (20,640 rows) datasets to temporary
CSVs, then runs the same CLI with different YAML schemas. It includes categorical
predictors and missing feature values, reconstructs every CV/validation/test
metric, and verifies training-only imputer/scaler statistics. California Housing
is [downloaded by scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html)
on the first acceptance run into ignored `.cache/datasets/`; subsequent runs use
the cache. A download failure fails acceptance rather than skipping the test.
Ordinary `mlexp run` never downloads datasets; users supply their CSV locally.

CI targets Linux Python 3.11, 3.12, and 3.13, plus Windows Python 3.12, in Unicode
checkout paths, using that same command. A Windows-only
threadpoolctl constraint avoids a verified 3.7 DLL discovery issue in such paths.
Local test fixtures use temporary tracking databases and never overwrite
the example store. See [decisions](docs/decisions.md), [progress](docs/progress.md),
and [engineering instructions](AGENTS.md) before contributing.

See [public API and CLI behavior](docs/api.md), [contribution workflow](CONTRIBUTING.md),
[compatibility policy](docs/compatibility.md), and [release notes](docs/release-notes.md).

Licensed under the [MIT license](LICENSE).

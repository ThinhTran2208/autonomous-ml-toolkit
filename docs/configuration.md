# Configuration reference

For installation and a first run, start with the [README](../README.md).
This reference retains the detailed v0.3.0 configuration, CSV schema, split,
and search rules.

Run the example commands below from the repository root. Built-in Diabetes
features are loaded with `scaled=False`, so the loader does not scale the full
dataset before splitting; the pipeline learns scaling from training rows only.

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
tabular datasets; very high-cardinality data is outside the supported scope.

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

## Metrics and tracking

Classification reports accuracy and macro F1; regression reports RMSE, MAE, and
R². `cv_*` values are the unweighted mean of validation-fold scores; `*_std` is
the population standard deviation across folds. RMSE/MAE are positive losses;
lower is better. Each regression CV validation fold needs at least two rows.
Every held-out test or configured validation partition needs at least two rows;
every classification training class needs at least `cv_folds` rows.

Run example commands from the repository root. Relative tracking database paths
resolve from the current working directory, even when the YAML lives elsewhere.
The default backend is `sqlite:///mlflow.db`, with artifacts in
`mlartifacts/mlflow/`. Remote stores and in-memory databases are unsupported.
To use another local database, set `tracking_uri` in YAML and pass the same
`--tracking-uri` to `compare` and `report`.

Version 0.3.0 uses evaluation protocol 4. Comparison rejects runs from another
protocol or recorded dependency environment. Preserve existing tracking stores:
use a new experiment name or a fresh SQLite database for incompatible new runs.
Existing runs remain reportable with their original database URI.

See the [API and CLI contract](api.md) for artifact names, metric roles, and
failure behavior, and the [compatibility policy](compatibility.md) for supported
platforms and dependency changes.

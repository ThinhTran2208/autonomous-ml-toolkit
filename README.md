# ML Experiment & Evaluation Toolkit

Run small tabular classification and regression experiments from YAML, compare
models using training-only cross-validation (CV), and keep configurations, metrics,
and fitted pipelines together in local MLflow tracking.

For students and practitioners building repeatable CPU baselines, the toolkit
provides:

- Built-in Iris and Diabetes datasets and explicitly typed local CSV input.
- scikit-learn pipelines for imputation, scaling, categorical encoding, and fitting.
- Dummy baselines, logistic regression, ridge, and bounded training-only grid search.
- CV-ranked comparisons and Markdown reports from tracked MLflow metadata.

It automates the experiment workflow; it is not AutoML. You choose a compatible
dataset, feature schema, model, and optional parameter grid. Version **0.3.0**
targets small tabular datasets with independent, identically distributed (IID)
rows. See [supported scope](#supported-scope) before using it for an evaluation.

## Quick start

Use Python 3.11–3.13; Python 3.12 is recommended for development. See the
[compatibility policy](docs/compatibility.md) for verified platform targets.
Install from this repository; no PyPI release is required.

Clone and enter the repository (GitHub access is required if it is private):

```bash
git clone https://github.com/ThinhTran2208/autonomous-ml-toolkit.git
cd autonomous-ml-toolkit
```

Create and activate an environment using your chosen Python version.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the toolkit and its runtime dependencies in the activated environment:

```bash
python -m pip install -e .
```

From the repository root, run a dummy classifier and logistic regression on the
same seeded Iris split, then compare them:

```bash
mlexp run examples/iris-dummy.yaml
mlexp run examples/iris.yaml
mlexp compare --experiment iris-baseline
```

Each `run` prints JSON with `run_id`, `experiment`, and `metrics`. Copy `run_id`
from the second run and replace `RUN_ID` below with that value:

```bash
mlexp report RUN_ID --output reports/iris.md
```

Open `reports/iris.md` for the configuration and tracked metrics. Omit `--output`
to print Markdown to the terminal. Reports never retrain and never overwrite an
existing output file; use a new filename for another report.

For regression, use [diabetes-dummy.yaml](examples/diabetes-dummy.yaml) and
[diabetes.yaml](examples/diabetes.yaml), then compare `diabetes-baseline`.
Both built-in datasets run without downloads.

## What you get

`run` returns JSON, `compare` returns CV-ranked JSON, and `report` produces
Markdown. This is a `compare` output **excerpt** from the Quick start workflow,
run on Windows/Python 3.12.10 on 2026-11-05 (dummy row omitted):

```json
[
  {
    "run_id": "4c491d660cc44d6c9c889ecc5bcf11ab",
    "model": "logistic_regression",
    "selection_metric": "cv_accuracy",
    "selection_score": 0.9583333333333334
  }
]
```

This toy-data score illustrates the output, not broad model quality. Your local
run IDs will differ; use your own ID for `report`. See the
[verification entry](docs/progress.md#2026-11-05--readme-usability-and-portfolio-refresh)
for provenance and retained evidence.

Each run stores the configuration, dataset fingerprint and schema, exact split
and fold indices, package versions, fold scores, selection details, and fitted
pipeline in MLflow. The default store is `mlflow.db`, with artifacts under
`mlartifacts/mlflow/`. Stores, environments, and generated reports are ignored by
Git. See the [artifact reference](docs/api.md#artifacts-and-metric-interpretation).
Inspect local runs with MLflow's UI:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1
```

Tracking paths resolve from the current working directory. With a custom
`tracking_uri` in YAML, pass the same `--tracking-uri` to `compare` and `report`.
Comparison rejects incompatible datasets, splits, protocols, or recorded package
versions. Preserve old stores when upgrading; use a new experiment or database
for incompatible runs. Old runs remain reportable. See [tracking details](docs/configuration.md#metrics-and-tracking).

## Use your own CSV

A compatible new dataset needs only YAML changes, with no Python edits or dataset
registration. Start with the checked-in [classification example](examples/csv-classification.yaml)
and its [small fabricated CSV](examples/data/classification.csv):

```yaml
experiment: csv-classification
task: classification
dataset:
  type: csv
  path: data/classification.csv
  target: label
  numeric_features: [number]
  categorical_features: [category]
  missing_values: impute
model: logistic_regression
seed: 42
test_size: 0.2
validation_size: 0.2
cv_folds: 3
tracking_uri: sqlite:///mlflow.db
```

Run `mlexp run examples/csv-classification.yaml`. CSV paths resolve relative to
the YAML file, so this path points to `examples/data/classification.csv`. For your
data, copy the YAML and update the path, target, and numeric/categorical feature
lists. Headers must match the declared target and features exactly; the target
cannot also be a predictor.

Blank fields are missing. Targets must be present; rows are never silently
dropped. With `impute`, numeric features use training medians and scaling;
categorical features use a missing marker and dense one-hot encoding. Each
training fold learns its own transformations. Use `missing_values: error` to
reject missing features. Unknown keys and incompatible task/model pairs fail
explicitly.

For regression, use [csv-regression.yaml](examples/csv-regression.yaml).
The [configuration reference](docs/configuration.md) covers schema rules,
all-missing features, unseen categories, split rounding, model parameters, and
bounded search, including [classification](examples/iris-search.yaml) and
[regression](examples/diabetes-search.yaml) search examples.

## Evaluation and reproducibility

1. Reserve test and optional validation rows before any learned transformation.
   Classification stratifies splits; regression uses random row splits.
2. Fit preprocessing and estimators inside a pipeline, separately in every
   training-only CV fold. Optional parameter search also uses training rows only.
3. Fit the final pipeline on training rows only, evaluate validation diagnostics
   if configured, then predict test rows once for final evaluation.

`test_size` and `validation_size` are fractions of all rows; the remainder trains.
Defaults are `0.2` test and `0.0` validation. Setting both to `0.2` gives
approximately 60/20/20, subject to rounding and class availability. Validation rows
never enter preprocessing, CV, search, or final fitting.

`compare` ranks by CV accuracy (higher is better) for classification or CV RMSE
(lower is better) for regression. Classification also reports macro F1;
regression also reports MAE and R². Validation metrics are diagnostic only.
CV scores after parameter search can be optimistic.

**Test scores are for final evaluation only.** Do not choose models, parameters,
features, or thresholds from test results. Each `run` emits test metrics, so
repeated inspection while iterating compromises their role as an untouched final
estimate; reserve new independent final data after such iteration.

Explicit seeds and recorded configurations, dataset/split identities, and versions
support reproducibility within the same environment. They do not guarantee
bitwise identity across platforms or dependency versions. The pipeline boundary
does not detect every form of leakage: duplicated entities, target-copy predictors,
and features unavailable at prediction time remain the user's responsibility.
Only load serialized model artifacts with trusted provenance; `compare` and
`report` do not deserialize models.

## Supported scope

| Task | Input | Models | Configurable model parameters |
| --- | --- | --- | --- |
| Classification | Iris or compatible CSV | `logistic_regression`, `dummy` | `C`, `max_iter` for logistic regression |
| Regression | Diabetes or compatible CSV | `ridge`, `dummy` | `alpha` for ridge |

Dummy classification predicts the most frequent training class; dummy regression
predicts the training mean. The toolkit is CPU-only, uses dense preprocessing,
and supports persistent local SQLite tracking. It does not support time-series or
group-aware evaluation, high-cardinality sparse workflows, multi-output targets,
GPU training, remote tracking backends, or production deployment.

## Development and verification

Install development dependencies separately in the activated environment:

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
ruff format --check .
```

For packaging and independent installed-wheel acceptance, use
`python scripts/verify.py`. It runs source checks, builds a wheel, installs it in
a fresh environment, and runs the CLI outside the source checkout. Acceptance
exports full Iris, Breast Cancer Wisconsin, and California Housing datasets to CSV, exercises mixed
features and missing values, reconstructs CV/validation/test metrics, and checks
training-only preprocessing statistics. It also smoke-tests both checked-in CSV
workflows. Logs and environments are retained under ignored `.cache/verification/`.

The first acceptance run downloads California Housing through scikit-learn into
ignored `.cache/datasets/`; later runs use the cache. Download failures fail
acceptance. Ordinary CSV experiments read local files and never download datasets.
The [CI workflow](.github/workflows/ci.yml) uses the same verifier; actual executed
results and platform limits are recorded in [progress](docs/progress.md).

AI agents assisted implementation, documentation, and verification work under the
[engineering instructions](AGENTS.md). Automated tests and installed-wheel
acceptance check behavior; the [independent audit](docs/audits/mvp-v0.3.0-independent-audit.md)
records separate probes and a historical conditional verdict. The
[release notes](docs/release-notes.md) record the subsequent fix and focused
re-audit outcome. These records describe verification scope, not a guarantee for
every dataset or environment.

See the [API and CLI contract](docs/api.md), [contribution workflow](CONTRIBUTING.md),
[roadmap](docs/roadmap.md), and [engineering decisions](docs/decisions.md).
Licensed under the [MIT license](LICENSE).

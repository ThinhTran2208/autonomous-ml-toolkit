# Public API and CLI contract

The supported Python entry points are:

```python
from mlexp import ExperimentConfig, load_config, run_experiment
from mlexp.tracking import compare_runs, render_report

config = load_config("examples/iris.yaml")
result = run_experiment(config)
rows = compare_runs(config.experiment, config.tracking_uri)
markdown = render_report(result["run_id"], config.tracking_uri)
```

`ExperimentConfig` is a Pydantic model. Construct it from keyword arguments or
`ExperimentConfig.model_validate(mapping)`. Configurations reject unknown fields;
do not use `model_copy(update=...)` to apply unvalidated user input. Treat nested
configuration containers as immutable. CSV and search schemas are available as
`CSVDataConfig` and `SearchConfig` in `mlexp.config`.

`load_config(path)` reads one safe YAML mapping, rejects duplicate keys, validates
it, and resolves a CSV path relative to the YAML file. It does not load the data.
Tracking URIs remain relative to the current working directory. Persistent local
SQLite URIs are supported; remote stores and in-memory backends are rejected.

`run_experiment(config)` validates/loads data, reserves test and optional validation
rows, performs training-only CV or bounded search, refits, evaluates, and saves MLflow
artifacts. It returns a dictionary with `run_id`, `experiment`, and numeric
`metrics`. `test_size` and optional `validation_size` are fractions of all rows;
the remainder trains the pipeline. The latter defaults to zero for train/test
compatibility. Validation never enters CV/search/refit and is evaluated only after
training, before the final test prediction. Invalid data raises `ValueError`; input
errors may raise `OSError` or YAML/Pydantic validation errors. MLflow failures
propagate its exceptions. Failures
after run creation mark the run FAILED; keyboard interruption marks it KILLED.

`compare_runs(experiment, tracking_uri="sqlite:///mlflow.db")` returns a list of
`run_id`, `model`, `selection_metric`, and `selection_score`. Only FINISHED runs
participate. Runs must share exact data/schema/partitions/folds/scoring/protocol
and recorded dependency versions. Sorting is CV accuracy descending or CV RMSE
ascending; ties use run ID. An existing empty experiment returns `[]`; unknown or
incompatible experiments raise `ValueError`. It never loads or retrains models.

`render_report(run_id, tracking_uri="sqlite:///mlflow.db")` returns Markdown with
status, configuration, tracked metrics, and artifact location. It reads metadata
only. Reports may display test scores; selecting by these scores invalidates the
interpretation of the data as an untouched final estimate.

## Commands

| Command | Output |
| --- | --- |
| `mlexp run CONFIG.yaml` | JSON with run ID, experiment, and metrics |
| `mlexp compare --experiment NAME [--tracking-uri URI]` | CV-ranked JSON rows |
| `mlexp report RUN_ID [--tracking-uri URI]` | Markdown on stdout |
| `mlexp report RUN_ID --output PATH` | A new Markdown file; refuses to overwrite |

Exit codes: 0 for success, 1 for handled config/data/tracking/file failures, and 2
for argparse usage errors. JSON goes to stdout; library diagnostics and errors
go to stderr. Relative report paths use the current working directory.

## Artifacts and metric interpretation

- `config.json`: validated requested configuration, including search settings.
- `split.json`: dataset fingerprint, schema, and exact train/validation/test/CV row identities.
- `protocol.json`: evaluation protocol, scoring functions, split, and package versions.
- `environment.json`: toolkit/Python and relevant runtime package versions.
- `fold_scores.json`: selected or fixed candidate scores per validation fold.
- `selection.json`: fixed settings or full bounded search results and refit details.
- `model/`: fitted MLflow scikit-learn pipeline, signature, and pinned requirements.

CV scores are unweighted fold means and population standard deviations. RMSE/MAE
are positive losses; lower is better. Classification accuracy/macro F1 and
regression R² are higher-is-better metrics. Selected CV scores can be optimistic
after search; test metrics are final evaluation only. Serialized pipeline loading
requires trusted artifacts; neither comparison nor reporting deserializes models.

Protocol 4 logs optional `validation_accuracy` / `validation_f1_macro` or
`validation_rmse` / `validation_mae` / `validation_r2`. These are diagnostic only;
comparison continues to rank training-only CV scores. Validation rows are excluded
from every fitted transformation and estimator, even the final refit. Runs using
different partitions or older protocols cannot be ranked together. Their reports
remain accessible. `validation_size: 0.0` records an empty `validation_indices`
list and zero validation rows, and produces no validation metrics.

This MVP assumes independent, identically distributed rows. Grouped subjects,
time series, high-cardinality sparse data, multi-output targets, GPU work, and
production deployment are outside the supported evaluation protocol.

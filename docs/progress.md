# Progress

## 2026-11-03 — M0/M1 implemented and locally verified

- Confirmed the specified remote repository is empty and cloned it into the
  dedicated workspace. No existing code or data was replaced.
- Created engineering instructions, milestone acceptance criteria, and architecture
  decisions before implementation.
- Planned M0/M1 delivery: strict YAML, two built-in tasks, seeded preprocessing and
  training, training-only CV, local MLflow tracking, run/compare/report CLI, tests,
  documentation, and CI.
- Implemented the installable `mlexp` package, strict safe YAML (including duplicate
  key rejection), Iris/Diabetes loading, training-only pipeline CV, final held-out
  evaluation, logistic/ridge/dummy baselines, and local SQLite-backed MLflow.
- Added `run`, `compare`, and `report` commands. Comparison ranks only CV results
  and rejects different dataset/split/fold/scoring/environment protocols. Reports
  never retrain and refuse to overwrite files.
- Runs record resolved model defaults, configuration, content fingerprint, exact
  split/fold indices, package versions, fold scores, and a fitted MLflow pipeline.
- Added MIT licensing, usage documentation, 49 automated tests, and CI for Linux
  Python 3.11/3.12/3.13 plus Windows Python 3.12. CI uses Unicode checkout paths
  and includes package builds and Linux clean-wheel CLI smoke checks.

### Executed validation

Local environment: Windows, Python 3.12.10, scikit-learn 1.9.1, MLflow 3.17.2,
NumPy 2.5.4, pytest 9.2.0, Ruff 0.17.3, threadpoolctl 3.6.0.

| Command | Actual result |
| --- | --- |
| `uv --no-cache pip install --python .venv/Scripts/python.exe -e '.[dev]'` | Installed successfully into the project environment |
| `python -m compileall -q src tests` | Passed |
| `.venv/Scripts/ruff.exe check .` | All checks passed |
| `.venv/Scripts/ruff.exe format --check .` | 17 files already formatted |
| `.venv/Scripts/python.exe -X utf8 -m pytest --tb=short -p no:cacheprovider` | **49 passed**, one upstream SQLAlchemy deprecation warning, 40.42 seconds |
| `.venv/Scripts/python.exe -X utf8 -m build` | Built source distribution and wheel successfully after the final code/dependency changes |
| `.venv/Scripts/mlexp.exe run examples/iris.yaml` | FINISHED; model and metadata persisted |
| `.venv/Scripts/mlexp.exe run examples/iris-dummy.yaml` | FINISHED |
| `.venv/Scripts/mlexp.exe run examples/diabetes.yaml` | FINISHED; model and metadata persisted |
| `.venv/Scripts/mlexp.exe run examples/diabetes-dummy.yaml` | FINISHED |
| `.venv/Scripts/mlexp.exe compare --experiment iris-baseline` | Ranked logistic regression (CV accuracy 0.958333) ahead of dummy (0.333333) |
| `.venv/Scripts/mlexp.exe compare --experiment diabetes-baseline` | Ranked ridge (CV RMSE 55.374175) ahead of dummy (78.133634) |
| `.venv/Scripts/mlexp.exe report cd15f0e9aa024792999f376dcb7c91d8 --output reports/iris.md` | Created Markdown report from tracked data |

Tests instrument actual preprocessing fits to verify every CV fold and final
refit use only their permitted rows, count the single held-out prediction, and
verify CV results stay unchanged when held-out features are perturbed. They also
check model reload, both tasks, seed reproducibility, rejected configuration,
failed-run status, comparison ordering, and all CLI commands.

### Resolved setup issues and limits

- Initial sandbox network restrictions blocked cloning/dependency downloads/build
  isolation. Approved network-enabled retries succeeded. An inaccessible uv cache
  was avoided using uv's supported `--no-cache` option.
- The initial pytest attempt reported 5 passed / 44 setup errors because the
  sandbox could not read the existing system pytest temporary directory. Retried
  with appropriate filesystem permissions; disabled the conflicting local cache
  provider for the final run. This did not skip any tests.
- Runtime testing then exposed threadpoolctl 3.7 corrupting Unicode DLL paths on
  Windows, plus a prediction spy that lost the wrapped method name. Constrained
  the dependency to 3.6 on Windows and preserved spy metadata, then ran all tests
  successfully. No installed third-party source was patched.
- MLflow emits an upstream SQLAlchemy 2.1 deprecation warning. The exercised
  tracking, searching, artifact, and report operations pass. The uv-created local
  environment also lacks pip metadata, so MLflow leaves pip unpinned in its
  optional Conda environment; model pip requirements are explicitly pinned.
- Serialized pipelines use cloudpickle and require trusted provenance when loaded.
- Local runs, reports, environments, and build outputs are ignored by Git. Failed
  diagnostic runs remain in MLflow with FAILED status; comparison excludes them.
- Work stays on `feat/initial-experiment-toolkit`; no remote refs were changed.
- GitHub Actions and its fresh-wheel smoke checks are configured but have **not**
  executed remotely. Only Windows Python 3.12 was verified locally.
- CSV/categorical data (M2), hyperparameter search (M3), and full release hardening
  (M4) remain planned. No current blockers prevent using the M1 workflow.

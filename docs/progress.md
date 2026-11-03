# Progress

Project status: DATASET_AGNOSTIC_IN_PROGRESS

## 2026-11-03 — Authorized M5 dataset-agnostic assurance

The user authorized YAML-only arbitrary compatible tabular CSV experiments,
explicit train/validation/test splits, and end-to-end verification on Iris,
Breast Cancer Wisconsin, and California Housing after original MVP completion.
Original M0–M4 completion evidence below is preserved.

- Existing strict CSV target/schema/missing policies remain the common loader.
- Added optional validation fractions with training-only CV/search/preprocessing
  and fit, diagnostic validation metrics, and a final test evaluation.
- Added independent installed-wheel CLI coverage for all three full datasets,
  checking each CV/validation/test metric against scikit-learn oracles.
- Targeted command `.venv/Scripts/python.exe -X utf8 -m pytest
  tests/test_validation.py tests/test_config.py --tb=short`: **43 passed** in
  19.41s, one visible upstream MLflow/SQLAlchemy deprecation warning.
- Shared verifier source stage: **113 passed** in 76.29s, one visible upstream
  warning. Ruff lint/format and sdist/wheel build passed. Version 0.3.0 development
  installation succeeded using the README command.
- Fresh-wheel installation succeeded. Independent acceptance: **9 passed** in
  234.11s, one visible upstream warning. This includes the full Iris (150 rows),
  Breast Cancer Wisconsin (569 rows), and California Housing (20,640 rows) CSV
  workflows, all CV/validation/test metric oracles, and training-only saved
  preprocessing statistics. No tests were skipped or weakened.
- `.venv/Scripts/python.exe -X utf8 scripts/verify.py`: **PASSED**, including
  both CSV examples' `run`, `report --output`, and `compare` commands from outside
  the source checkout, using the fresh wheel and three-way partitions.
  Full evidence: `.cache/verification/89f3e18692c24466bca17d82a1cfd551/result.json`,
  with per-step logs, isolated environment, and dependency freeze retained.
- Final `python -m ruff check .`, `python -m ruff format --check .`, and
  `git diff --check` passed. No new datasets, stores, serialized models, or local
  environment artifacts are included in the changes.
- Local M5 acceptance is complete. Remote synchronization and hosted results
  remain pending; no feature work remains and no current blocker was encountered.


## 2026-11-03 — MVP completion verified

All M0–M4 acceptance criteria have verification evidence. Feature work is stopped.
No subsequent development milestone is authorized.

Verified code commit: `464af58eda84ab45a906cf00adc2370fc7229bcc` on `autonomous-dev`.
[Successful hosted CI run](https://github.com/ThinhTran2208/autonomous-ml-toolkit/actions/runs/41674892421)
executed the shared `python scripts/verify.py` command on every target:

| Hosted target | Actual result |
| --- | --- |
| Linux Python 3.11 | Passed |
| Linux Python 3.12 | Passed |
| Linux Python 3.13 | Passed |
| Windows Python 3.12, Unicode checkout and environment | Passed |

### Final acceptance evidence

| Criterion | Executed verification |
| --- | --- |
| Classification/regression, YAML, baselines, seeded reproducibility | 99 source tests plus 6 independent installed-wheel acceptance tests |
| Leakage-free preprocessing and evaluation | Actual fold/refit row and target instrumentation; adversarial held-out target tests; saved-model training-statistic and final-metric reconstruction |
| Typed CSV input, missing values, categorical handling, invalid data rejection | CSV/data regression tests and both documented CSV CLI workflows |
| Bounded training-only parameter selection | 19 selection tests, both built-in search examples, and independent wheel search acceptance |
| MLflow configurations, metrics, artifacts, comparison and reporting | Real local SQLite tracking, model reload, run/compare/report CLI acceptance, protocol mismatch and overwrite checks |
| Installable package and documented usage | README development install, successful sdist/wheel build, fresh venv wheel installation, isolated import from site-packages |
| Tests, Ruff, CI, documented smoke checks | All four hosted jobs passed the entire shared verifier, including source pytest, lint, format check, clean wheel acceptance, and CSV run/report/compare |
| Engineering/release documentation | AGENTS.md, milestone acceptance criteria, decisions, API/CLI contract, contribution workflow, compatibility policy, MIT license, and release notes |

Final local source check:
`.venv/Scripts/python.exe -X utf8 -m pytest --tb=short` — **99 passed** in 57.33s,
one visible upstream MLflow/SQLAlchemy deprecation warning. Ruff lint and format
checks passed. Independent clean-wheel acceptance passed **6 tests** locally and
was rerun successfully by each hosted CI job. No tests or acceptance gates were
skipped or weakened.

Local full-verifier evidence is preserved in
`.cache/verification/b42a1d58a1e949b9a1dbfee27d4a6639/`; that earlier successful
run had 96 source tests before the three console-encoding regressions were added.
Hosted CI above verifies all 99 source tests, all 6 independent checks, package
installation/build, and all smoke checks after the console fix.

- Completion tag: `mvp-v0.2.0`, local only.
- `autonomous-dev` is synchronized with the supplied private origin. Main and
  repository visibility were preserved; no release or package was published.
  Existing MLflow runs were preserved. The completion-record commit changes documentation only; the
  application, tests, verifier, and workflow match the verified code commit above.
- Unresolved MVP blockers: none. Supported boundaries remain IID CPU-only small
  tabular data, dense categorical encoding, local SQLite tracking, and trusted
  serialized model provenance. Future features require a new authorized milestone.

## 2026-11-03 — Hosted CI exposed a verifier output regression

- Synchronized verified commit `cb68386` to the existing private
  `origin/autonomous-dev`. No main ref, visibility setting, or release was changed.
- [Hosted CI run](https://github.com/ThinhTran2208/autonomous-ml-toolkit/actions/runs/41672870995):
  Linux Python 3.11/3.12/3.13 jobs passed. Windows passed source tests, wheel build,
  isolated acceptance, and both CSV run/report/compare workflows, then failed while
  printing the final Unicode evidence path under its redirected cp1252 console.
- Fixed the verifier to escape otherwise unrepresentable console characters,
  retaining UTF-8 log files and all checks. Added real text-stream regression tests
  for ASCII, cp1252, and UTF-8. Hosted revalidation remains required before completion.
- `.venv/Scripts/python.exe -X utf8 -m pytest --tb=short`: **99 passed** in 57.33s
  after the fix, including all three console-encoding regressions. Ruff lint and
  formatting checks passed. No application checks were bypassed or disabled.

## 2026-11-03 — M4 local verification passed; hosted CI pending

- Prepared version 0.2.0 with API/CLI documentation, contribution instructions,
  dependency/compatibility policy, release notes, and a shared local/CI verifier.
- Installed the development package using the README command:
  `.venv/Scripts/python.exe -X utf8 -m pip install -e '.[dev]'` — succeeded.
- `.venv/Scripts/python.exe -X utf8 scripts/verify.py` completed successfully.
  Evidence: `.cache/verification/b42a1d58a1e949b9a1dbfee27d4a6639/result.json`, with
  per-step logs and a clean wheel environment preserved in that directory.
- Executed checks in that verifier:
  - `python -m ruff check .` and `python -m ruff format --check .`: passed.
  - `python -m pytest --tb=short`: **96 passed**, one upstream deprecation warning.
  - `python -m build`: source archive and 0.2.0 wheel built successfully.
  - Fresh standard-library venv + `pip install WHEEL 'pytest>=8.3,<10'`: succeeded;
    `pip freeze --all` retained as evidence. No system site-packages or editable
    source paths were used for wheel acceptance.
  - Independent `python -m pytest acceptance -c pyproject.toml --tb=short` in the
    fresh wheel environment: **6 passed** in 150.64s, one upstream warning.
  - Both CSV examples executed from copied configs outside the source working
    directory, with `run`, `report --output`, and `compare` all succeeding.
- The first independent run had 3 passing / 3 failing tests due to test harness
  database selection and Windows isolated-output encoding. Fixed both and reran
  the entire verification command, with all assertions retained.
- Added regression coverage for lexical class labels (`001` versus `1`, `TRUE`
  versus `True`) and textual booleans in numeric features. CSV parsing now preserves
  lexical identity until explicit schema-driven numeric conversion.
- actionlint 1.7.12 checked the final workflow successfully. The official release
  archive checksum was verified before execution. CI invokes the same verifier
  on Linux Python 3.11/3.12/3.13 and Windows Python 3.12, with 20-minute job limits.
- Confirmed the supplied origin repository is private and initially has no refs.
  Synchronizing only `autonomous-dev` will enable actual hosted matrix evidence;
  repository visibility, main, and release/package publication remain unchanged.
- Remaining completion gate: actual hosted CI results for the verified code.
  Keep MVP_IN_PROGRESS until that gate has evidence. No feature expansion remains.

## 2026-11-03 — M3 training-only model selection completed

- Added validated bounded GridSearchCV over the full preprocessing/model pipeline.
  Search sees only reserved training rows; the selected pipeline gets one training
  refit and one held-out prediction. Fixed-model behavior remains supported.
- Logged search grids, scorer, each candidate's fold scores/rank/mean/std, selected
  parameters, resolved estimator defaults, and refit row count in MLflow.
- Instrumented tests verify the exact permitted rows and targets in every fit,
  one held-out prediction per run, and identical selections after adversarial
  held-out target changes, for classification and regression. Invalid/oversized
  grids and actual protocol mismatches are rejected.
- `.venv/Scripts/python.exe -X utf8 -m pytest --tb=short`: **94 passed** in 65.55s,
  one upstream deprecation warning. No tests were skipped or weakened.
- Ruff lint passed; `ruff format --check .`: 21 files formatted.
- `.venv/Scripts/python.exe -X utf8 -m pytest tests/test_selection.py --tb=short`:
  **19 passed** (one upstream warning).
- `mlexp run examples/iris-search.yaml` and
  `mlexp run examples/diabetes-search.yaml`: both FINISHED with selection artifacts.
- Current milestone: M4 clean-wheel installation, independent acceptance, shared
  CI verification, and release/contribution documentation. No current blocker.

## 2026-11-03 — M2 CSV experiments completed

- Created `autonomous-dev` from the existing verified project state; preserved
  the original branch, generated data, and local history. No publication or remote
  synchronization was performed, as requested.
- Added explicit CSV schemas, strict row/header/target/type validation, numeric
  and categorical preprocessing inside each fold, and content/schema fingerprints.
- Added fabricated classification/regression CSV examples and tests for missing
  values, unseen categories, all-missing columns, target exclusion, and model reload.
- Initial runtime tests exposed a non-JSON dataset manifest and pandas inferring
  a float dtype for all-missing categorical columns. Fixed both and reran all tests.
- `.venv/Scripts/python.exe -X utf8 -m pytest --tb=short`: **75 passed** in 62.41s,
  one upstream MLflow/SQLAlchemy deprecation warning. Cache locations now use the
  writable ignored `.cache/` directory; no tests or assertions were bypassed.
- `.venv/Scripts/ruff.exe check .`: passed. `ruff format --check .`: 19 files formatted.
- `.venv/Scripts/python.exe -X utf8 -m pytest tests/test_data.py tests/test_csv_experiment.py --tb=short`:
  **26 passed** in 16.37s (one upstream warning).
- Both `mlexp run examples/csv-classification.yaml` and
  `mlexp run examples/csv-regression.yaml` completed with tracked model artifacts.
- Current milestone after M2: M3 bounded, training-only parameter selection.
- M4 clean-wheel installation, independent acceptance, and release documentation
  remain. No current blocker prevents continuing.

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

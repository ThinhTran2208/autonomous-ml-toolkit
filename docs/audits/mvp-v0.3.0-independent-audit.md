# Independent MVP Audit — v0.3.0

Audit date: 2026-11-04 (Asia/Saigon). Repository: `ThinhTran2208/autonomous-ml-toolkit`.

## 1. Executive summary

**Final verdict: CONDITIONAL PASS.** The core CPU-only, IID tabular experiment workflow
worked in independently executed tests. No blocking model-selection, preprocessing
leakage, numerical evaluation, or reproducibility defect was found within the
documented scope. One **Low** severity Windows CLI reporting defect was reproduced.
Finding counts: **Critical 0; High 0; Medium 0; Low 1**.

The installed wheel correctly handled previously unseen synthetic CSV datasets,
training-only search, missing values, unknown categories, local MLflow tracking,
comparison, and reporting. All 113 existing source tests passed, but this verdict
also rests on separately authored probes, explicit metric calculations, independent
reference models, real fit-row instrumentation, adversarial inputs, and fresh installs.
The main wheel harness recorded **18 passing probe groups and one failing group**;
the failure is F-01. Supplementary probes and the focused console reproduction are
reported separately rather than counted as additional project unit tests.

The CLI can write a report successfully and then return failure when printing its
Unicode output path to a redirected cp1252 stream. This does not invalidate model
results, but can mislead automation and leaves a file that the next retry refuses
to overwrite. Correct that behavior or explicitly document and accept the UTF-8
workaround before broader use. Promotion to `main` is recommended only after that
condition is addressed and verified; **do not promote the unchanged candidate
unconditionally**. No promotion, source fix, commit, or push was performed by this audit.

Duplicate entities and semantic copies of the target produced misleadingly perfect
scores in deliberately contaminated datasets. These are proven **dataset-level
risks**, not evidence that the implementation mixes held-out rows into training.
The toolkit assumes IID rows and cannot establish that predictors were available
at prediction time.

## 2. Audit scope and provenance

- Examined commit: **`67f9634450c55ba441c3195454cafd45546d6114`** (`67f9634`).
- At audit start, `HEAD`, `autonomous-dev`, and the local remote-tracking ref
  `origin/autonomous-dev` resolved to that commit. The annotated `mvp-v0.3.0` tag
  also dereferenced to it. Remote refs were not fetched or modified.
- `67f9634` changes documentation only. A Git comparison against implementation
  commit `1ae6f1df324ec50bb41b8cacbeb793a1bf2cbaf0` found no changes in `src`,
  `tests`, `acceptance`, `scripts`, `.github`, or `pyproject.toml`.
- Inspected all eight package modules, all source tests and fixtures, the existing
  installed-package acceptance suite, verifier, packaging, CI workflow, README,
  AGENTS.md, roadmap, decisions, progress, API, compatibility, contribution, and
  release documentation.
- Audit branch: `codex/independent-mvp-audit`. Deliverables are this report and an
  appended progress entry. Production source, project tests, dependencies, acceptance
  criteria, and `MVP_COMPLETE` status remain unchanged.
- The built wheel's eight Python source files were compared byte-for-byte with
  the inspected source. All matched. Wheel SHA-256:
  `e1d0555f4ae47f56b35bad8cef197ef8b646d54c88c5ea335a3ad641588c3bf1`.

### Environment

Executed locally on Windows 10, build 19042, x64 Python **3.12.10**, in a Unicode
checkout path. Fresh venvs used standard-library `venv`, without system site packages.
The original environment and fresh environments differ in MLflow resolution:

| Component | Source-test environment | Fresh editable / wheel environments |
| --- | --- | --- |
| Toolkit | 0.3.0 | 0.3.0 |
| Python | 3.12.10 | 3.12.10 |
| MLflow | 3.17.2 | 3.18.0 |
| scikit-learn | 1.9.1 | 1.9.1 |
| NumPy | 2.5.4 | 2.5.4 |
| pandas | 3.1.0 | 3.1.0 |
| SciPy | 1.18.1 | 1.18.1 |
| Pydantic | 2.14.2 | 2.14.2 |
| PyYAML | 6.0.3 | 6.0.3 |
| cloudpickle | 3.1.2 | 3.1.2 |
| joblib | 1.6.0 | 1.6.0 |
| threadpoolctl | 3.6.0 | 3.6.0 |

Source checks used pytest 9.2.0 and Ruff 0.17.3. Fresh dependency resolution was
accepted as declared; no requirement was changed to obtain passing results.
Both fresh environments passed `pip check`; complete freezes are preserved locally.

### Verification boundaries

Personally executed results apply to Windows/Python 3.12.10 and the versions above.
Linux, Python 3.11/3.13, macOS, Python 3.14+, older allowed dependency combinations,
and cross-platform numerical identity are **NOT VERIFIED** by this audit.
The CI YAML defines Linux 3.11/3.12/3.13 and Windows 3.12 jobs with Unicode paths.
The progress log claims successful hosted CI for `1ae6f1d`; that is historical
repository evidence, not an independently fetched or rerun hosted result here.
The metadata permits Python `>=3.11`; this does not establish compatibility with
every future Python minor version.

No new external dataset was needed. The original California Housing acceptance
download and the full `scripts/verify.py` chain were not rerun. Its source, existing
tests, and CI configuration were inspected; this audit instead executed a fresh
build/install and its own new-dataset acceptance probes. No remote tracking service,
deployment, package publication, or paid resource was configured. Local experiment
stores were isolated from all pre-existing project runs. Only model artifacts
generated during this audit were deserialized.

### Actual architecture

| Stage | Implementation | Independent assessment |
| --- | --- | --- |
| Configuration | `config.py`: safe YAML loader, duplicate-key rejection, Pydantic schemas, bounded grids | Explicit task/schema/model/seed/fraction checks; CSV paths relative to YAML |
| Data | `data.py`: CSV byte read, header/row validation, typed conversion, content/schema fingerprint | No learned transformation; target excluded by explicit schema |
| Partitions | `data.py:118–141`: seeded test split, optional validation from remainder, classification stratification | Row identities disjoint; exact sequential rounding verified |
| Preprocessing | `models.py`: imputer/scaler and categorical imputer/one-hot encoder inside pipeline | Learned independently inside each training CV fold; unseen categories ignored |
| Fixed CV | `experiment.py`: seeded shuffled KFold/StratifiedKFold, `cross_validate`, `n_jobs=1` | Training-only; all published CV metrics reconstructed |
| Search/refit | `selection.py`: bounded GridSearchCV, primary CV metric, one training refit | Candidate fold scores/means/stds and selected index independently verified |
| Final evaluation | `experiment.py`: optional validation prediction, then one test prediction | Validation diagnostics do not select/refit; explicit metric formulas match |
| Tracking | `experiment.py`, `tracking.py`: explicit MLflow client, SQLite, local artifacts, failure status | Successful, failed, and incomplete runs exercised |
| Compare/report | `tracking.py`, `cli.py`: CV ranking, protocol key, metadata-only Markdown | Correct ranking and persistence; Unicode output-path defect described below |

There is no feature-selection stage, calibration, threshold tuning, group splitting,
time-series handling, or hidden train-plus-validation refit. Their absence matches
the small documented scope. The main architecture discrepancy is the CLI's
successful-file-write/failure-exit behavior under a legacy output encoding.

## 3. Verification matrix

Evidence names below refer to files under the ignored repository-local directory
`.cache/independent-audit-20261104/`. `P` means `probe-results.json`, `E` means
`edge-results.json`, `F` means `followup-results.json`, and `S` means
`supplement-results.json`. These are raw audit evidence, not previously existing
project assertions. Their retained scripts permit local reinspection. Use a fresh
output directory for a complete rerun, since the probes deliberately retain runs
and refuse to overwrite report outputs.

| Requirement | Procedure | Expected | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Target commit | Inspect refs/history and implementation diff | Exact supplied MVP | Exact SHA; implementation matches `1ae6f1d` | PASS | Git commands in §7 |
| Existing source tests | Run documented venv pytest | No failures | 113 passed, one upstream warning, 116.84 s | PASS | `source-tests.log` |
| Lint / formatting | Execute both Ruff checks | Clean | Source: 29 formatted files; final audit documents included: 30 | PASS | Console output; final check logs |
| Distribution build | Build sdist and wheel | Both build | Both built; all 8 wheel modules match source | PASS | `build.log`, `wheel-source-integrity.log` |
| Fresh editable install | README `pip install -e ".[dev]"` in new venv | Installs; entry point works | Install, help, run/compare/report succeed | PASS | `editable-install.log`, F |
| Fresh wheel install | Install built wheel in second new venv | Isolated installed package | Imports from site-packages; run/compare/report succeed | PASS | `wheel-install.log`, P paths check |
| Dependency consistency | `pip check` in both fresh environments | No broken requirements | No broken requirements | PASS | `*-pip-check.log` |
| Split isolation | Independently reconstruct seeded partitions and CV folds | Complete, disjoint row identities | Exact match for all four main CSVs | PASS | P dataset checks |
| Fold-local learned transforms | Instrument actual ColumnTransformer fits and targets | 12 search-fold fits + one training refit | Exact permitted rows/targets in all 13 fits | PASS | P `instrument-real-fold-and-refit-rows` |
| Imputation/scaling | Compare fitted medians, means, variances to training arrays | Training-only statistics | Match; all-missing numeric feature retained as zero | PASS | P dataset checks |
| Categorical isolation | Assign a category only to validation/test | It never enters learned vocabulary | Absent from vocabulary; prediction succeeds | PASS | P dataset checks |
| Held-out feature intervention | Set held-out numeric features to 1e8 and change categories | CV/search unchanged | Unchanged for both tasks, fixed and searched; final metrics change | PASS | P four `heldout-extremes` checks |
| Held-out target intervention | Flip classification targets after fixing partitions; set regression targets to -1e9 | No effect on CV or selection | CV and selection unchanged; final scores change | PASS | P target-flip and regression-extreme checks |
| One final evaluation pass | Spy on pipeline predictions | One validation and one test call | Exactly one each in instrumented searched run | PASS | P fit-row instrumentation |
| Memorization adversary | Unique categorical IDs + random labels | Training can memorize; unseen rows near chance | 100% training; 52.5% CV/validation/test | PASS | S random-label check |
| Search correctness | Independently fit all 3 candidates × 4 folds | Correct scores, ordering and chosen candidate | All candidate fold/mean/std values and chosen index match | PASS | P binary/regression search |
| Numerical metrics | Explicit accuracy/F1 and RMSE/MAE/R² formulas | Agreement within 1e-10 | All four datasets agree; exact differences in §5 | PASS | P dataset checks |
| Degenerate regression | Constant target, perfectly fitted predictor | Zero losses, finite sklearn R² convention | RMSE/MAE 0; R² 1 for CV/validation/test | PASS | S constant-regression check |
| Repeated seeded runs | Repeat binary and regression searches | Identical split/selection/metrics | Zero metric differences; six JSON artifacts equal | PASS | P repeat checks |
| Saved config sufficiency | Run stored resolved config in a new CLI process | Same metrics with same data/environment | Exact match | PASS | S saved-config replay |
| Traceability | Inspect config, seed, versions, fingerprint, manifests | Accurate metadata | Schema/content SHA-256 and all exact row/fold identities match | PASS | P dataset/repeat checks |
| YAML-only new datasets | Execute four synthetic schemas/tasks | No application edits needed | All four complete | PASS | P dataset checks |
| Single feature-type / missing data | Numeric-only, categorical-only, all-missing features | Valid inputs complete | All complete with finite metrics | PASS | E three feature-type checks |
| Invalid CSV/config | 17 main cases + 8 supplementary cases | Predictable actionable rejection | All rejected; selected cases also checked through CLI | PASS | P invalid matrix; E additional-invalid |
| NUL-byte integrity | Invalid numeric value, categorical/target lexical values | Reject numeric corruption or preserve lexical text | Numeric rejected; category/target text preserved | PASS | P NUL check; F corrected and lexical checks |
| Missing policy | `missing_values: error` with missing feature | Reject | Actionable ValueError | PASS | E additional-invalid |
| Duplicate records | Repeated entity rows across IID splits | Expose dataset risk without row-ID overlap | 24 repeated entities overlap; no row-ID overlap; perfect scores | PASS | E duplicate-risk; limitation, not automatic protection |
| Target copies | Predictor semantically equals target | Expose user-supplied leakage risk | Perfect scores despite target-column exclusion | PASS | E target-proxy; limitation, not automatic protection |
| MLflow persistence | New-process retrieval of run, params and artifacts | Stored values match returned values | Exact metric equality; model and all metadata retrieved | PASS | P dataset/tracking checks |
| Tracking failure | Inject failure in model artifact saving | FAILED even with previously logged metrics | FAILED; excluded from compare; report shows FAILED | PASS | E artifact-failure-lifecycle |
| Incomplete runs | Add RUNNING and FAILED runs | Not ranked | Both excluded | PASS | P tracking check |
| CV-only ranking | Create deliberately contrary CV/test scores | Classification descending CV; regression ascending CV loss | Correct; no final metrics returned in comparison | PASS | P compare checks |
| Protocol mismatch | Add incompatible completed run | Refuse ranking | Actionable incompatibility error | PASS | P compare checks |
| Report accuracy | Read report in separate CLI process | Stored values with documented formatting | Every displayed metric equals stored value at 6 significant digits | PASS | P tracking check |
| Report overwrite protection | Reuse an existing output path | Reject without changing bytes | Exit 1; contents preserved | PASS | P tracking check |
| Path handling | Absolute config; relative CSV; relative SQLite; separate cwd | Resolve according to README | Correct; no dependency on repo-root cwd | PASS | P paths check; F editable smoke |
| Unicode output on cp1252 | Redirect CLI report with a Unicode output path | File written and success exit | File written, then exit 1 encoding error | FAIL | P legacy-console; F-01 |
| Hosted/platform matrix | Review YAML/history; no hosted execution | Personally verify each platform | Only Windows 3.12 executed here | NOT VERIFIED | Scope limitations |
| Cross-version/BLAS determinism | No cross-platform equivalence experiment | Bound claims to tested runtime | No bitwise cross-environment guarantee asserted | NOT VERIFIED | Scope limitations |

The NUL numeric probe in the first edge harness initially labeled a correct input
rejection as FAIL because its wrapper expected execution to reach a subsequent
assertion. The expectation was corrected and rerun in `followup_probe.py`; the main
wheel probe independently confirms rejection. The original diagnostic log is retained.
That harness error is not counted as a toolkit finding. No project test was changed.

## 4. Detailed findings

### F-01 — Unicode report output path yields failure after a successful write

**Severity: Low. Proven defect.** Affects `src/mlexp/cli.py:42–47`, especially
`print(str(args.output))` at line 45.

**Reproduction:** use a trusted completed run in an isolated local store and a
new output filename containing Unicode. Capture stdout/stderr, as a CI job or
calling program would, with a cp1252 output encoding:

```python
import os
import subprocess

completed = subprocess.run(
    [
        "mlexp",
        "report",
        RUN_ID,
        "--tracking-uri",
        TRACKING_URI,
        "--output",
        "reports/report-試験.md",
    ],
    env=os.environ | {"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"},
    capture_output=True,
)
print(completed.returncode)  # observed: 1
```

**Expected:** create the UTF-8 Markdown report once, return 0, and emit a readable
or safely escaped output path. **Actual:** the complete report exists, but printing
its path raises `UnicodeEncodeError`; the CLI catches it as `ValueError`, emits
`mlexp: 'charmap' codec can't encode ...`, and returns 1. Retrying the same command
then encounters overwrite protection. The test used the actual installed wheel
with MLflow 3.18.0, a Unicode checkout/output path, and an explicitly redirected
cp1252 stream. It does not prove failure in every interactive Windows terminal.

A focused follow-up used relative output paths to isolate the filename itself:
an ASCII filename under cp1252 returned **0**, a Unicode filename under cp1252
returned **1**, and a Unicode filename under UTF-8 returned **0**. All three files
were created and their report bytes were identical. Evidence:
`console-repro-results.json` and `console_repro.py` in the audit directory.

**Root cause:** output encoding is handled in `scripts/verify.py` but not in the
application CLI. Filesystem success and console formatting share one exception
handler, so a post-write presentation error is reported as operation failure.

**Recommended correction:** configure safe stream error handling (for example,
preserve the selected encoding and escape unrepresentable characters), or emit
an ASCII-safe representation of the path. Cover redirected ASCII/cp1252/UTF-8
streams and confirm both exit code and file bytes. Keep exclusive file creation.
Do not weaken overwrite protection or silently discard output-path characters.

**Available workaround:** launch the CLI with UTF-8 output, such as
`PYTHONUTF8=1` or `PYTHONIOENCODING=utf-8`. UTF-8 report creation and retrieval passed
the independent checks. This workaround was used explicitly in the normal probe
environment and disabled in the adversarial legacy-console test. No fix was made.

### Risks and limitations that are not proven implementation defects

- **Duplicated/grouped entities:** IID row indices can be disjoint while the same
  entity appears in both sets. Twenty-four entities repeated ten times yielded
  100% CV and test accuracy. Users must deduplicate or prepare an appropriate
  group-aware evaluation outside this MVP. Automatic group-aware splitting is
  explicitly out of scope; the audit does not recommend silent deduplication.
- **Semantic target leakage:** an explicitly declared predictor copied from the
  target also yields 100%. Schema checks prevent including the named target column,
  not an alias, future measurement, post-outcome field, or revealing identifier.
  Users must review feature provenance and prediction-time availability.
- **Selection optimism and repeated final inspection:** search winners' CV scores
  can be optimistic. Repeatedly viewing test scores and manually changing configs
  invalidates an untouched final estimate. The README correctly explains both;
  the toolkit enforces CV-only automatic ranking, not a human experiment policy.
- **Input retention:** logged configuration, hash, schema, and indices identify the
  data but do not archive its CSV bytes. Reproduction requires retaining the same
  dataset and dependency environment. The saved-config replay did so successfully.
- **Determinism boundaries:** seeded splits and supported estimators reproduced
  locally. `n_jobs=1` does not promise identical BLAS reductions, CPU instructions,
  solver behavior, or library defaults across environments. There is no GPU or
  distributed training in the inspected implementation.
- **Serialization:** cloudpickle artifacts require trusted provenance, as already
  documented. Reports/comparisons read metadata and do not deserialize models.
- **Coverage limits:** comparison pagination is implemented, but a >1,000-run
  experiment, concurrent experiment creation, low-disk conditions, and process
  termination mid-write were not stress-tested. The injected save failure verifies
  one concrete partial-run failure path, not every storage fault.

## 5. Reproducibility and independent numerical results

The numerical oracle did not call `mlexp.evaluation_metrics`, `build_pipeline`,
`fit_search`, or the project's tests. It constructed separate scikit-learn models,
independently regenerated seeded splits/folds, explicitly iterated candidate grids,
and calculated metrics from predictions. Accuracy was the fraction correct;
macro F1 was the unweighted mean of per-class `2TP/(2TP+FP+FN)` over the label union;
RMSE was `sqrt(mean((y-pred)^2))`; MAE was `mean(abs(y-pred))`; R² was
`1-SSE/SST`, with the documented finite sklearn convention tested separately for
a constant target. Fold means were unweighted and standard deviations used `ddof=0`.
All comparison tolerances were `rtol=atol=1e-10`; repetition tolerance was `1e-12`.

| Dataset | Train / validation / test rows | Selected parameters | CV primary | Validation primary | Test primary | Maximum absolute oracle difference |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| binary-search | 126 / 36 / 49 | `{"C": 1.0}` | 0.904989919355 | 0.916666666667 | 0.857142857143 | 0 |
| multiclass-fixed | 126 / 53 / 32 | `{}` | 0.682711693548 | 0.754716981132 | 0.59375 | 0 |
| regression-search | 125 / 22 / 64 | `{"alpha": 0.03}` | 0.690388237962 | 0.920529491227 | 0.531470351339 | 0 |
| regression-two-way | 158 / 0 / 53 | `{}` | 0.735951710724 | — | 0.556088570682 | 0 |

Classification primary is accuracy; regression primary is RMSE. The oracle checked
**every** emitted metric, including macro F1, MAE, R² and CV standard deviations,
not just the primary scores displayed above. It also checked every search candidate's
fold scores, mean/std, the chosen index, and the chosen parameters.

| Repeated experiment | Maximum metric difference | Metadata/artifact equality |
| --- | ---: | --- |
| binary-search-repeat | 0 | Exact equality of split, selection, resolved config, environment, fold scores, and protocol JSON |
| regression-search-repeat | 0 | Exact equality of split, selection, resolved config, environment, fold scores, and protocol JSON |

Run IDs and timestamps intentionally differed. A third reproducibility check
replayed the saved `config.json` in a new installed-CLI process and matched all
metrics exactly. The CSV had not moved or changed. Model defaults and selected
parameters are additionally logged in MLflow, including estimator random state.

The fit spy observed 12 candidate/fold fits and one final refit, all on exactly
the independently expected training rows and targets. Validation and test were
predicted once each. Extreme held-out feature values changed final evaluation
without changing any CV result or selected candidate, for both fixed and searched
models in both tasks. Regression target values were also changed to -1e9 outside
training. Classification targets were flipped using a fixed-partition intervention
so that altered labels could not change stratified partition allocation.

The classification intervention changed test accuracy from **0.857142857143** to **0.142857142857**, while CV scores and selection remained identical. This artificial run was confined to the audit store and is not a real model-quality estimate.

## 6. Dataset generalization results

All datasets were authored independently in ignored audit directories. No application
source or registry change was necessary. The four main datasets each contain 211
rows, seeded synthetic numeric predictors, a three-level categorical predictor,
periodically missing numeric/category values, and an entirely missing numeric
column. Every validation/test row receives a category absent from training.

| Dataset or case | Construction / purpose | Observed outcome |
| --- | --- | --- |
| Binary mixed classification | Two balanced quantile-derived classes; C grid `[0.03, 1, 30]`; test 0.23, validation 0.17 | End-to-end success, oracle match, repeated search identical |
| Multiclass mixed classification | Four classes; fixed logistic regression; test 0.15, validation 0.25 | End-to-end success and all metrics match |
| Mixed regression | Noisy linear/category effect; alpha grid `[0.03, 1, 30]`; test 0.30, validation 0.10 | End-to-end success, oracle match, repeated search identical |
| Two-way regression | Same compatible schema; fixed ridge; test 0.25, validation 0 | No validation metrics; correct CV/final metrics |
| Categorical-only | 120 rows; category missing periodically; dummy classifier; 20% validation | Success with finite metrics |
| Numeric-only | 120 rows; numeric regression target; dummy regressor; 20% validation | Success with finite metrics |
| All predictors missing | 120 rows; both numeric and categorical columns empty | Success; classifier accuracy 0.5, macro F1 1/3 |
| Random-label identity trap | 400 rows; unique categorical token; logistic C=1000 | Train accuracy 1.0; CV/validation/test 0.525 |
| Constant regression | 90 rows; target always 7.5; ridge | All losses zero; R² 1.0 under finite convention |
| Duplicate-record risk | 24 entity/category records repeated 10 times | No row-ID overlap, but all 24 entities cross partitions; scores 1.0 |
| Target-copy risk | 120 rows; declared categorical feature copies target | Scores 1.0; user-supplied semantic leakage |
| Held-out extremes | Four main datasets, held-out x/z set to 1e8; unseen category changed; regression targets -1e9 | Training CV and search unchanged; final scores change |
| Absent/missing target | Missing header target or blank target field | Explicit rejection; targets never imputed |
| Empty / header-only | Zero bytes or header with no observations | Explicit rejection |
| Malformed CSV | Too many/few fields or unclosed quoted field | Explicit rejection; CLI cases return 1 without traceback |
| Invalid schema | Duplicate header or unexpected extra column | Explicit rejection |
| Unsuitable numeric types | Text predictor, infinity, textual regression target | Explicit rejection with column named |
| NUL bytes | `1` followed by NUL and nonnumeric suffix; NUL-bearing category and target strings | Numeric rejected; lexical strings preserved distinctly |
| Missing-value error policy | Missing feature with `missing_values: error` | Explicit rejection |
| Invalid config | Unknown key, incompatible model, invalid fractions, bool seed, one CV fold, invalid search value | Pydantic/value validation errors |
| Unsafe/ambiguous YAML | Python object tag, duplicate key, nonmapping document | Rejected without execution |
| Insufficient partitions | Tiny test/validation or insufficient per-class training counts | Early split/count errors |

The sequential split implementation rounds up the test count first, then rounds
up the validation fraction of the remaining rows. Counts were independently
verified using the documented formula rather than assuming exact decimal fractions
of the original row count. No blank/invalid records were silently dropped in the
tested cases. Arbitrary text features used as declared categories are supported;
unstructured text modeling, high-cardinality dense encodings at large scale, grouped
subjects, time series, and multi-output targets are outside the documented scope.

## 7. MLflow, installation, commands, and evidence

### Executed commands

Paths here are repository-relative to avoid embedding machine-specific directories.
For readability, `A` denotes `.cache/independent-audit-20261104`, `E` denotes
`A/editable-env/Scripts`, and `W` denotes `A/wheel-env/Scripts`. Expand these
abbreviations when rerunning; they are labels, not required environment variables.

| Executed command / operation | Actual outcome |
| --- | --- |
| `git status --short --branch`, `git log -8 --oneline`, `git rev-parse HEAD`, `git show --stat 67f9634`, `git remote -v` | Clean target checkout; correct repository, commit and history |
| `git switch -c codex/independent-mvp-audit` | Created audit branch from supplied commit |
| `git rev-parse autonomous-dev origin/autonomous-dev`, `git rev-parse 'mvp-v0.3.0^{commit}'` | Exact target commit verified |
| `git diff --name-only 1ae6f1d 67f9634 -- src tests acceptance scripts .github pyproject.toml` | Empty: no implementation differences |
| `.venv/Scripts/python.exe -X utf8 -m pytest --tb=short` | 113 passed; 1 SQLAlchemy deprecation warning; 116.84 s |
| `.venv/Scripts/ruff.exe check .` | All checks passed |
| `.venv/Scripts/ruff.exe format --check .` | 29 files already formatted |
| Final Ruff lint/format checks after report edits | All checks passed; 30 files already formatted. An initially unformatted report code block was corrected before this final check |
| `.venv/Scripts/python.exe -X utf8 -m build --outdir A/dist` | Built sdist and wheel successfully |
| `.venv/Scripts/python.exe -X utf8 -m venv A/editable-env` | Fresh editable-test environment created |
| `E/python.exe -X utf8 -m pip install -e '.[dev]'` | Documented development install succeeded |
| `.venv/Scripts/python.exe -X utf8 -m venv A/wheel-env` | Separate fresh environment created |
| `W/python.exe -X utf8 -m pip install A/dist/ml_experiment_evaluation_toolkit-0.3.0-py3-none-any.whl` | Standard wheel install succeeded |
| `E/python.exe -X utf8 -m pip check`; `W/python.exe -X utf8 -m pip check` | Both report no broken requirements |
| `E/python.exe -X utf8 -m pip freeze --all`; `W/python.exe -X utf8 -m pip freeze --all` | Complete dependency evidence retained |
| `E/mlexp.exe --help` | Supported commands/options displayed |
| `.venv/Scripts/python.exe -X utf8 A/edge_probe.py` | Feature/dataset/failure probes executed; initial harness NUL expectation corrected separately |
| `E/python.exe -X utf8 A/followup_probe.py` | NUL correction/preservation checks and editable CLI workflow passed |
| `W/python.exe -X utf8 A/audit_probe.py` | Installed-wheel dataset, oracle, leakage, repeat, tracking, error and CLI probes executed; one CLI defect |
| `W/python.exe -X utf8 A/supplement_probe.py` | Memorization trap, constant regression and saved-config replay passed |
| `W/python.exe -X utf8 A/console_repro.py` | ASCII/cp1252 control and Unicode/UTF-8 workaround succeed; Unicode/cp1252 returns 1 after writing identical report bytes |
| Python zipfile/source byte comparison | All 8 wheel modules identical to audited source; SHA recorded in §2 |

The probe scripts invoke the actual installed executables with these supported forms:

```text
mlexp run CONFIG.yaml
mlexp compare --experiment NAME --tracking-uri sqlite:///DATABASE
mlexp report RUN_ID --tracking-uri sqlite:///DATABASE
mlexp report RUN_ID --tracking-uri sqlite:///DATABASE --output REPORT.md
```

They execute from their own isolated data directories, not the repository root.
`cli-transcript.jsonl` contains the main probe's actual argv, return codes, stdout
and stderr. Separate editable CLI transcripts preserve its run/compare/report calls.
All data paths and SQLite stores resolve according to the documented config-versus-cwd
rules. Source-test temp data, new audit stores, build outputs and environments remain
ignored; no existing experiment store was used or deleted.

### Tracking observations

Fresh experiments and runs were associated correctly. The returned metric dictionary
exactly matched MLflow's stored metrics. Artifacts included config, split/fold manifest,
environment, protocol, fold scores, selection details and the fitted pipeline. Artifact
retrieval occurred after CLI training exited, using `MlflowClient`; the freshly generated
pipeline produced the same predictions as the independently fitted reference.

Comparison excluded both RUNNING and FAILED runs. An injected failure at model saving
left six already logged metrics but correctly marked the run FAILED and excluded it.
Its report remained readable and explicitly showed FAILED. Deliberately opposing
CV and test rankings confirmed CV-only ordering for both tasks; incompatible completed
runs triggered refusal instead of being silently mixed. Reports matched all stored
metric values at their intended six-significant-digit display precision and did not
retrain. Existing report files were unchanged after rejected overwrite attempts.

The original source tests emitted a visible upstream SQLAlchemy `noload` deprecation
warning. Probe model saving emitted MLflow's serialization caution. Neither was hidden
or converted into a claim of failure; observed tracking and artifact operations passed.
The newly resolved MLflow 3.18.0 environment was tested directly rather than assumed
equivalent to the original 3.17.2 environment.

### Retained evidence index

- `source-tests.log`, `build.log`, `editable-install.log`, `wheel-install.log`.
- `editable-freeze.txt`, `wheel-freeze.txt`, both `*-pip-check.log` files.
- `audit_probe.py`, `probe-results.json`, `audit-probe.log`, `cli-transcript.jsonl`.
- `edge_probe.py`, `edge-results.json`, `edge-probe.log` (includes the initial harness diagnostic).
- `followup_probe.py`, `followup-results.json`, `editable-cli-transcript.json`.
- `supplement_probe.py`, `supplement-results.json`, `supplement-probe.log`.
- `console_repro.py`, `console-repro-results.json`, `console-repro.log`.
- `wheel-source-integrity.log`, distributions, isolated environments, generated CSVs,
  MLflow stores, retrieved artifacts and reports under the same audit directory.

These generated artifacts are retained locally and intentionally excluded from version
control. This Markdown report records the portable conclusions and reproduction steps.

## 8. Final verdict

**CONDITIONAL PASS** — the documented MVP works in the audited Windows environment
and on independently authored compatible CSVs, with no blocking correctness,
reproducibility, model-selection, or preprocessing-leakage defect found. The single
Low severity Unicode CLI reporting issue should be corrected or explicitly documented
with its UTF-8 workaround before broader use or unconditional promotion to `main`.

This verdict does not certify arbitrary datasets, grouped/time-dependent evaluation,
all dependency combinations, or unexecuted platforms. The independent audit is complete;
implementation of improvements, changes to completion status, and promotion are outside
this deliverable and were not performed.

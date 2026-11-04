# Progress

Project status: MVP_COMPLETE

## 2026-11-04 — Cross-drive environment diagnosis and release verification

- Reproduced the known failure using the isolated worktree's own Python 3.12.10
  interpreter and pip 25.0.1. `direct_url.json` and the editable `.pth` correctly
  referenced that worktree; there were no pip configuration overrides or inherited
  Python/pip/virtual-environment settings causing source-path contamination.
- Inspected installed pip's `Git.get_subdirectory`: it uses the parent of
  `git rev-parse --git-dir` as a root, then calls `os.path.relpath`. The source
  worktree and shared Git metadata are on different drives, causing the observed
  `ValueError`. The direct pip subprocess returned **2**; the initial diagnostic
  helper expected 1 and was corrected to record the actual nonzero exit and exact
  exception. This diagnostic correction changed no project verification criterion.
- Preserved every prior checkout, virtual environment, uncommitted document, audit
  report, and incomplete verification log. Created a separate isolated checkout
  of the same repository at approved implementation
  `59c9a5fe1702b5b85c17ccf55871f1c977bcb1de`, with its own Git metadata and new
  `.venv` colocated on one drive. Copied the corrected release documentation;
  no production, test, dependency, package-version, or historical-audit file changed.
- Documented setup `python -m venv .venv` followed by
  `.venv/Scripts/python.exe -X utf8 -m pip install -e '.[dev]'` succeeded (exit 0).
  The fresh environment retains pip **25.0.1**; no pip upgrade or patch was needed.
- `.venv/Scripts/python.exe -X utf8 -m pip check` and `pip freeze --all` both
  returned **0**. Metadata and import assertions returned **0**, confirming the
  editable URL, `.pth` import, and Python prefix refer to the new release checkout,
  version remains **0.3.0**, and pip detects no project subdirectory.
- Diagnostic metadata, known-failure stdout/stderr, preservation hashes, source
  installation logs, full freeze, and exact commands/exit codes are retained in
  `.cache/release-preparation/` in the new checkout. Environment checks are recorded
  as PASSED in `environment-check.json`.
- `.venv/Scripts/python.exe -X utf8 scripts/verify.py` completed with **exit 0**.
  All **13 steps passed**: Ruff lint/format, **119 source tests** (86.11 seconds),
  sdist and wheel builds, fresh wheel installation, wheel `pip freeze --all`,
  **10 installed-wheel acceptance tests** (363.74 seconds), and classification
  and regression CSV `run`, `report --output`, and `compare` smoke commands.
  All six smoke commands returned **0**. The existing upstream SQLAlchemy
  deprecation warning remains visible; no test or verification criterion changed.
- Full command arrays, per-step exit codes, durations, stdout/stderr, package
  freeze, and fresh wheel environment are preserved under
  `.cache/verification/6c94329712384cd4ae96d75a379de187/`; `result.json` is **PASSED**.
  The additional wheel environment `python -X utf8 -m pip check` returned **0**.
  `.cache/release-preparation/local-summary.json` records completion of every
  required verifier step and confirms preserved original document hashes.
- Release identity checks passed: only `docs/release-notes.md` and this progress
  log differ from the approved implementation; all eight wheel Python modules
  match the checkout byte-for-byte, and their Git blob identities match the
  approved commit. Package version remains **0.3.0**. The wheel SHA-256 is
  `6d81e6d8ccf62ff1fa5a21fab3c948bb9aa1906ca5d849f6b47e71cecdd8a112`, identical
  to the wheel recorded by the focused re-audit. The historical audit is unchanged.
- This documentation-only release preparation records the initial v0.3.0 release
  decision and existing audit scope; it is not a new independent code audit.
  Hosted CI must succeed for the exact documentation commit before promotion
  to `main` and the annotated `v0.3.0` tag. No package or GitHub Release publication
  is authorized.

## 2026-11-04 — Initial v0.3.0 documentation preparation (environment blocker)

- Reconfirmed with `git ls-remote --symref origin HEAD refs/heads/autonomous-dev
  refs/heads/main refs/tags/v0.3.0 'refs/tags/v0.3.0^{}'` that the development
  tip is approved implementation `59c9a5fe1702b5b85c17ccf55871f1c977bcb1de`;
  remote `main` and release tag `v0.3.0` are absent. GitHub metadata confirmed
  default `autonomous-dev`, private visibility, and no GitHub Releases.
- Created an isolated clean worktree and local `codex/prepare-v0.3.0` task branch
  from that SHA. Preserved the original checkout's uncommitted progress entry,
  prior verification branch, and the separate focused re-audit's untracked report
  and ignored evidence. No stash, reset, deletion, or audit modification occurred.
- Updated only release documentation: merged F-01 into the initial 0.3.0 notes
  and recorded the historical CONDITIONAL PASS and subsequent focused PASS.
  The historical audit's SHA-256 remains
  `ed910a1bc8140a276fd04e565a5048b0b218af20b566378bdbe8718aa56bd096`.
  The documentation preparation is not a new independent code audit.
- `python -m venv .venv` and `.venv/Scripts/python.exe -X utf8 -m pip install
  -e '.[dev]'` succeeded. `pip check` passed; an isolated editable import resolved
  to this worktree's source and confirmed version 0.3.0. A setup interpreter-path
  print initially hit the primary checkout's legacy console encoding; its explicit
  `-X utf8` rerun succeeded without changing any project file.
- `.venv/Scripts/python.exe -X utf8 scripts/verify.py` passed Ruff lint and format
  checks. Source pytest was still running when the separate environment snapshot
  command `.venv/Scripts/python.exe -X utf8 -m pip freeze --all` failed: pip 25.0.1
  raised `ValueError: path is on mount 'c:', start on mount 'D:'` while resolving
  the editable package in the cross-drive Git worktree. This is an environment
  verification blocker; no workaround or verification bypass was applied.
- Stopped the owned verifier process tree per the user's stop-on-failure rule.
  Its incomplete logs remain under
  `.cache/verification/7d9d32c34d334734979991a0c4085859/`; the retained RUNNING
  result is not a PASS. Full source pytest, packaging, fresh-wheel acceptance,
  CLI smoke tests, and candidate CI are not claimed complete.
- `git diff --check` passed. The worktree changes remain uncommitted and limited
  to `docs/release-notes.md` and this log. No release candidate commit, push,
  stable branch, release tag, default-branch change, or publication was performed.

## 2026-11-04 — F-01 Unicode CLI output-path fix

Addressed the Low severity finding from the retained v0.3.0 independent audit on
`autonomous-dev`. Existing history, audit text, generated data, and tracking stores
are preserved. The historical verdict remains **CONDITIONAL PASS**; this developer
fix is not a new independent audit, release, or milestone. No main update is part
of this work.

Root cause: after exclusive UTF-8 report creation succeeded, printing its Unicode
path to strict cp1252 stdout raised `UnicodeEncodeError`. The CLI's `ValueError`
handler then returned 1 for a successful write. At CLI entry, preserve stdout and
stderr encodings and configure `backslashreplace` for streams supporting
`reconfigure`. Unsupported console characters remain visible as escapes; UTF-8
output remains intact. Report content, filesystem paths, and exclusive `open("x")`
creation are unchanged. Other I/O errors still return failure.

Regression evidence:

- Added six real-text-stream cases: ASCII/Unicode filenames crossed with ASCII,
  cp1252, and UTF-8 encodings. Before the fix, the Unicode ASCII/cp1252 cases
  failed (2 failed, 4 passed); after the fix all six passed. They verify exit 0,
  exact displayed paths, original Unicode content, retained encoding, and exit 1
  with unchanged bytes on retry.
- Added installed-wheel subprocess acceptance for the same six combinations with
  `PYTHONUTF8=0`, explicit `PYTHONIOENCODING`, byte-identical UTF-8 reports, and
  overwrite protection. The first run caught a test expectation using forward
  slashes instead of Windows-native separators. Corrected it to `str(Path(output))`;
  an immediate lint run caught a 101-character line, which was wrapped before
  restarting complete verification. No acceptance condition was removed.
- `.venv/Scripts/python.exe scripts/verify.py` initially passed Ruff, all **119**
  source tests (138.28 seconds, one existing upstream SQLAlchemy warning), the
  sdist/wheel build, fresh wheel installation, and dependency freeze before the
  test expectation failure above. Initial evidence is retained under
  `.cache/verification/18594dfc04ed4bcf9a96792de915dd6d/`; the lint-only diagnostic
  is retained under `.cache/verification/e65ba83d6aaf406ba69e39a71b1b3d4f/`.
- The corrected full verifier rerun passed lint/format, **119 source tests**
  (167.91 seconds, one existing upstream warning), build, fresh wheel install,
  dependency freeze, and `pip check`. Its process was interrupted during
  acceptance after eight passing cases, leaving an incomplete RUNNING log under
  `.cache/verification/e916f60506494cfcab400d7ec8e513d2/`. This is not claimed as
  a completed successful verifier run.
- Executed `.venv/Scripts/python.exe .cache/f01-20261104/finish_verification.py`
  to rerun the entire installed-wheel acceptance suite in that fresh environment
  from a new directory outside the checkout: **10 passed**, one existing upstream
  warning, **527.01 seconds**. All assertions and datasets were retained.
  Evidence is recorded separately under
  `.cache/f01-20261104/completion-0c1699be62014b49a13216c829b4c364/`.
- That completion helper also passed both documented CSV examples' installed-wheel
  `run`, `report --output`, and `compare` commands from outside the checkout:
  **all six smoke commands returned 0**. Its final `result.json` is **PASSED**.
  Final `.venv/Scripts/ruff.exe check .`, `ruff format --check .` (30 files),
  and `git diff --check` passed. Source, regression, packaging, dependency,
  acceptance, and CLI checks are complete; the interrupted original verifier
  log remains preserved rather than relabeled as passing.
- The fresh wheel environment's `python -m pip check` passed. All eight Python
  modules in the exact `ml_experiment_evaluation_toolkit-0.3.0-py3-none-any.whl`
  match source bytes. An initial wildcard integrity check selected an older
  retained wheel; selecting the exact versioned artifact corrected that probe.
- Ran `.cache/f01-20261104/reproduce.py` with the fresh wheel interpreter and CLI
  against the independent audit's retained `binary-search` run and SQLite store.
  All six ASCII/Unicode filename and ASCII/cp1252/UTF-8 cases returned **0**;
  all retries returned **1** without changing bytes. All six files exactly match
  the original audit's report, SHA-256
  `d1c06a9a664055a8cc7be0cd5fd4158240aadb09b3db36dcfa869e98a7a9f6cc`.
  New filenames preserve the original evidence. Results and commands are retained
  in `.cache/f01-20261104/results-62512be4f4984b2c847678b6ea116c69.json`
  and `reproduce.py`; the historical reproduction script/results are unchanged.

Limitations remain the existing CPU-only IID tabular/local-tracking scope and
dependency/platform reproducibility boundaries. Legacy consoles display escapes
for characters they cannot encode; report files retain their original Unicode.
Local evidence applies to Windows/Python 3.12.10. Hosted verification is performed
by the unchanged [CI workflow on autonomous-dev](https://github.com/ThinhTran2208/autonomous-ml-toolkit/actions?query=branch%3Aautonomous-dev);
its result must be checked for the pushed commit separately from local evidence.
The existing upstream MLflow/SQLAlchemy deprecation warning is not suppressed.

## 2026-11-04 — Independent audit of the v0.3.0 MVP

Completed the separately requested audit of commit
`67f9634450c55ba441c3195454cafd45546d6114`. The report is
[docs/audits/mvp-v0.3.0-independent-audit.md](audits/mvp-v0.3.0-independent-audit.md).
Its verdict is **CONDITIONAL PASS**, with **one Low severity finding**: redirected
cp1252 output can make `mlexp report` return failure after successfully writing a
report whose output path contains Unicode. No blocking correctness, preprocessing
leakage, selection, or reproducibility defect was found in the exercised scope.
The report recommends fixing or documenting the UTF-8 workaround before broader
use or unconditional promotion. No implementation changes or promotion were made;
the existing project completion status above is unchanged.

Executed evidence, separate from the original development verification:

- `.venv/Scripts/python.exe -X utf8 -m pytest --tb=short`: **113 passed**, one
  visible upstream SQLAlchemy deprecation warning, **116.84 seconds**.
- `.venv/Scripts/ruff.exe check .`: **passed**;
  `.venv/Scripts/ruff.exe format --check .`: **29 files already formatted**.
  After the audit document was added, its Python reproduction block initially
  needed formatting. Corrected that block and reran both checks: **lint passed;
  30 files already formatted**. `git diff --check` also passed.
- `.venv/Scripts/python.exe -X utf8 -m build --outdir
  .cache/independent-audit-20261104/dist`: **sdist and wheel built**. All eight
  wheel Python modules match the inspected source byte-for-byte.
- Standard-library `venv` created separate editable and wheel environments under
  the ignored audit directory. The README `python -m pip install -e '.[dev]'`
  installation and `python -m pip install` of the built wheel both **succeeded**.
  Both environments passed `python -m pip check`; complete freezes are retained.
- Fresh installations resolved **MLflow 3.18.0**, compared with **3.17.2** in the
  source-test environment. No dependency requirement was changed. All environments
  used Windows/Python **3.12.10** and the declared Windows threadpoolctl bound.
- Independently authored `audit_probe.py`, run using the fresh wheel interpreter:
  **18 probe groups passed; 1 failed**, exposing the Unicode CLI finding above.
  Four new synthetic CSV datasets passed explicit metric oracles, split/fold
  reconstruction, training-statistic checks, unseen-category handling, fixed/search
  workflows and held-out perturbations. All reconstructed metric differences were
  **0.0**. Repeated binary/regression searches matched all metrics and six metadata
  artifacts exactly. Instrumentation observed 12 training-fold fits, one training
  refit, and one prediction each for validation and test.
- Additional isolated probes exercised single-type/all-missing features, malformed
  CSV/configuration, an injected model-artifact failure, incomplete-run exclusion,
  CV-only ranking, report contents/overwrite protection, and relative/absolute
  paths. Fresh editable and wheel `mlexp run`, `compare`, and `report` workflows
  succeeded from separate working directories.
- A focused console reproduction confirmed: ASCII path/cp1252 returns **0**;
  Unicode path/cp1252 returns **1** after writing; Unicode path/UTF-8 returns **0**.
  All three created report files have identical bytes.
- A random-label/unique-ID dataset achieved training accuracy **1.0** but only
  **0.525** CV/validation/test accuracy. Deliberately duplicated entities and a
  target-copy predictor produced perfect scores, confirming documented dataset
  risks rather than row-index leakage. Constant-target regression and a saved
  configuration replay passed; replayed metrics differed by **0.0**.
- The initial edge harness mislabeled a correct NUL-bearing numeric-field rejection
  as a failure. Its expectation was corrected and independently rerun; invalid
  numeric input is rejected and categorical/target lexical identities are preserved.
  The original diagnostic evidence remains retained. Project tests were not changed.

Raw commands, transcripts, new CSVs, isolated stores, artifacts, environments and
audit scripts are preserved under ignored `.cache/independent-audit-20261104/`.
Only this progress entry and the audit report are deliverable repository changes.
No existing data was deleted, no production code or acceptance criterion was changed,
and no commit, push, merge, or main update was performed.

Limitations: this audit personally executed Windows/Python 3.12 only. Hosted CI,
Linux/Python 3.11/3.13, other dependency combinations, and cross-platform numerical
identity are **NOT VERIFIED** here. Existing CI claims were treated as historical
evidence. The original California Housing download and full verifier were not rerun;
the independent synthetic-data and fresh-install probes supplied new evidence.

## 2026-11-04 — M5 completed and verified

All M5 acceptance criteria in docs/roadmap.md passed. Arbitrary compatible tabular
CSVs use the same YAML-configured loader and pipeline for either task. Separate
validation and test partitions never enter preprocessing, CV, search, or refit.

[Successful M5 CI run](https://github.com/ThinhTran2208/autonomous-ml-toolkit/actions/runs/41679957431)
verified code commit `1ae6f1df324ec50bb41b8cacbeb793a1bf2cbaf0` on every target:

| Hosted target | Actual result |
| --- | --- |
| Linux Python 3.11 | Passed |
| Linux Python 3.12 | Passed |
| Linux Python 3.13 | Passed |
| Windows Python 3.12, Unicode checkout and environment | Passed |

Each job passed the shared `python scripts/verify.py`: Ruff lint/format, all
113 source tests, distribution build, clean-wheel install, all 9 independent
acceptance tests, and both CSV run/report/compare smoke workflows. The complete
local Windows command and timing evidence are recorded below. No assertions,
checks, or datasets were replaced to obtain passing results.

- Verified implementation is synchronized to `origin/autonomous-dev`.
- This completion update changes documentation only; application/tests/verifier/CI
  match the verified implementation commit. Local completion tag: `mvp-v0.3.0`.
- No unresolved blockers. California Housing acceptance needs network access on
  its first run, then uses the ignored cache; normal CSV experiments stay local.
  The upstream MLflow/SQLAlchemy deprecation warning remains visible and nonblocking.
- No datasets, credentials, model artifacts, remote tags, main changes, or package
  releases were pushed. Existing stores, history, and the original local tag remain.
- M0–M5 are complete. Feature work is stopped until another milestone is authorized.

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
- Local M5 acceptance is complete. Verified implementation commit
  `1ae6f1df324ec50bb41b8cacbeb793a1bf2cbaf0` was synchronized successfully using
  `git push origin autonomous-dev` on 2026-11-04. The remote branch matches the local
  commit. No main branch, remote tag, dataset, or model artifact was pushed.
- [Hosted M5 CI run](https://github.com/ThinhTran2208/autonomous-ml-toolkit/actions/runs/41679957431)
  passed the shared verifier on Linux Python 3.11/3.12/3.13 and Windows 3.12.
  No feature work remains and no blocker was encountered.


## 2026-11-03 — MVP completion verified

All M0–M4 acceptance criteria have verification evidence. Feature work is stopped.
No subsequent milestone was authorized at that point; M5 was authorized later,
as recorded above.

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

# Contributing

Read AGENTS.md, docs/roadmap.md, docs/decisions.md, and docs/progress.md before
working. The persistent integration branch is `autonomous-dev`; never push or
merge to main as part of autonomous work. Preserve existing work and generated
tracking data. Publication and releases require separate authorization.

Use Python 3.11–3.13; development is locally verified on Windows Python 3.12.
Create a virtual environment and install the development extras as in README.md:

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
ruff format --check .
python scripts/verify.py
```

The final command runs exactly the verification entry point used in CI: lint,
format checking, all source tests, package build, clean wheel installation,
independent acceptance tests, and CSV CLI smoke/report/compare checks. It needs
network access to install ordinary public Python dependencies, with no cloud
accounts or paid services. Each invocation creates a fresh environment and stores
logs plus `result.json` in an ignored `.cache/verification/` subdirectory. Previous
runs and application data are preserved.

The independent suite in `acceptance/` does not import toolkit implementation
helpers. It invokes the wheel's CLI from a separate working directory, checks
MLflow metadata and generated model artifacts, reconstructs final metrics using
scikit-learn, and validates reproducible seeds and CV-only comparison. Run it
through the verifier so an editable source checkout cannot satisfy wheel checks.

Changes must include relevant behavior/failure/leakage tests, an updated decision
record where appropriate, and actual verification evidence in docs/progress.md.
Do not select models or parameters from held-out scores. After MVP_COMPLETE,
feature work needs a subsequent authorized milestone.

See [dependency compatibility policy](docs/compatibility.md) and
[release notes](docs/release-notes.md).

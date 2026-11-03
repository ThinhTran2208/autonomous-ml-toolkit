# Dependency and compatibility policy

- Supported Python targets: 3.11, 3.12, and 3.13 on Linux; Python 3.12 on Windows.
  CI defines these jobs in Unicode checkout paths. Actual executed evidence,
  including any unexecuted matrix jobs, is recorded in docs/progress.md.
- Runtime requirements use explicit lower bounds and exclude unreviewed major
  upgrades. pandas is an explicit dependency for named CSV features. Development
  tools use bounded requirements in the `dev` extra.
- Windows threadpoolctl remains constrained to 3.6 because 3.7 failed DLL discovery
  in a verified Unicode workspace. Remove the bound only after the regression
  checks pass with an upstream fix. Do not patch installed dependencies.
- The package intentionally permits compatible dependency resolution across
  Python/platform targets instead of shipping a Windows-only freeze file. Seeds
  guarantee repeatable partitions and results within the same runtime environment;
  they do not promise cross-version/platform bitwise identity. Each MLflow run
  records versions, and the wheel verifier retains `pip freeze --all` evidence.
- For dependency updates, install into a fresh environment, run
  `python scripts/verify.py`, and inspect CI for every supported target before
  publishing a release. Never silence a new warning or relax a test to make an
  upgrade pass. Known upstream MLflow/SQLAlchemy deprecations remain visible.
- Changes to splitting, scoring, preprocessing semantics, or the selection
  contract require reviewing/incrementing the evaluation protocol version. Use a
  new MLflow experiment when protocols or recorded environments differ; historic
  runs remain reportable and are never deleted by an upgrade.
- Keep the Python public API and CLI stable within a minor release. Additions
  use a minor version; incompatible behavior requires a documented version change.
  The project uses MIT licensing. Local verification and local tags do not publish
  packages, release artifacts, or websites.

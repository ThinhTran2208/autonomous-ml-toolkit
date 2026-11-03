import importlib.util
import io
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("encoding", ["ascii", "cp1252", "utf-8"])
def test_verifier_reports_unicode_paths_on_redirected_consoles(monkeypatch, encoding):
    path = Path(__file__).resolve().parents[1] / "scripts" / "verify.py"
    spec = importlib.util.spec_from_file_location("mlexp_verification", path)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    output, errors = io.BytesIO(), io.BytesIO()
    stdout = io.TextIOWrapper(output, encoding=encoding)
    stderr = io.TextIOWrapper(errors, encoding=encoding)
    with monkeypatch.context() as context:
        context.setattr(sys, "stdout", stdout)
        context.setattr(sys, "stderr", stderr)
        verifier._configure_console()
        print("Verification evidence: checkout-試験/result.json", flush=True)
        print("Error in checkout-試験", file=sys.stderr, flush=True)
    for value in (output.getvalue(), errors.getvalue()):
        expected = "試験".encode() if encoding == "utf-8" else b"\\u8a66\\u9a13"
        assert expected in value

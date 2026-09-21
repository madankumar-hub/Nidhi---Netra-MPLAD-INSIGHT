"""Run every dependency-free test module in one command.

    python -m tests.run_all

`pytest tests/` works too once pytest is installed.
"""
from __future__ import annotations

import sys

from tests import (
    test_access_control,
    test_accessibility,
    test_anomaly_model,
    test_deployment_safety,
    test_geography,
    test_pdf_export,
    test_rate_limit,
    test_risk_engine,
    test_sample_csv,
    test_schema_contracts,
    test_security,
    test_vocabulary_coverage,
)

MODULES = [
    ("Risk engine", test_risk_engine),
    ("Machine learning", test_anomaly_model),
    ("Schema contracts", test_schema_contracts),
    ("Security", test_security),
    ("Access control", test_access_control),
    ("Rate limiting", test_rate_limit),
    ("PDF export", test_pdf_export),
    ("Geography", test_geography),
    ("Vocabulary coverage", test_vocabulary_coverage),
    ("Sample CSV", test_sample_csv),
    ("Accessibility", test_accessibility),
    ("Deployment safety", test_deployment_safety),
]


def main() -> int:
    failures = 0
    for title, module in MODULES:
        print(f"\n=== {title} " + "=" * (56 - len(title)))
        failures += module._run_all()
    print("\n" + ("All test modules passed." if not failures else f"{failures} module(s) failed."))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

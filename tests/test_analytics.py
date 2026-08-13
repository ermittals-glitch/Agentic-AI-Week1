from __future__ import annotations

import pandas as pd

from src.analytics.kpis import build_claim_kpis


def test_build_claim_kpis_basic() -> None:
    df = pd.DataFrame(
        {
            "claim_id": ["A", "A", "B"],
            "provider_charge": [100, 200, 300],
            "allowed_amount": [80, 150, 200],
            "insurance_paid": [70, 120, 150],
            "patient_responsibility": [10, 30, 50],
        }
    )

    kpis = build_claim_kpis(df)
    assert kpis["claim_count"] == 2
    assert kpis["service_lines"] == 3
    assert kpis["total_provider_charge"] == 600

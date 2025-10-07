"""Mini README: Tests covering the finance ledger duplication helpers.

Structure:
    * test_duplicate_transaction_applies_overrides - ensures copies inherit fields and accept overrides.
    * test_duplicate_transaction_rejects_bad_metadata - invalid metadata payloads raise clear errors.
"""

from __future__ import annotations

from datetime import date

import pytest

from nerfdrone.finance import FinanceLedger, Transaction, TransactionType


def test_duplicate_transaction_applies_overrides() -> None:
    """Duplicating should copy the base record and apply overrides for edits."""

    ledger = FinanceLedger(
        transactions=[
            Transaction(
                transaction_id="txn_0001",
                transaction_type=TransactionType.EXPENSE,
                description="Pilot salary",
                category="Payroll",
                amount=4000.0,
                occurred_on=date(2024, 5, 1),
                metadata={"role": "Pilot"},
            )
        ]
    )

    duplicated = ledger.duplicate_transaction(
        "txn_0001",
        overrides={
            "amount": 4050.0,
            "occurred_on": date(2024, 6, 1),
            "metadata": {"role": "Pilot", "note": "June uplift"},
        },
    )

    assert duplicated.transaction_id != "txn_0001"
    assert duplicated.amount == pytest.approx(4050.0)
    assert duplicated.occurred_on == date(2024, 6, 1)
    assert duplicated.metadata["note"] == "June uplift"
    snapshot = ledger.export_snapshot()
    assert any(entry["transaction_id"] == duplicated.transaction_id for entry in snapshot["expenses"])


def test_duplicate_transaction_rejects_bad_metadata() -> None:
    """Duplication should reject metadata overrides that are not dictionaries."""

    ledger = FinanceLedger()

    with pytest.raises(ValueError):
        ledger.duplicate_transaction("txn_0001", overrides={"metadata": "not-a-dict"})

"""Mini README: In-memory finance ledger supporting income and expenses.

Structure:
    * TransactionType - enum representing income versus expense entries.
    * Transaction - dataclass storing transaction metadata and helpers.
    * FinanceLedger - orchestrates CRUD-like behaviour for transactions.

The ledger is intentionally simple and dependency-free so the interface can
simulate budgeting workflows without external services. It validates inputs,
logs actions for debugging, and exposes duplication helpers that copy an
existing entry while letting callers override selected fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional

from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


class TransactionType(str, Enum):
    """Enumerate the supported transaction categories."""

    INCOME = "income"
    EXPENSE = "expense"

    @classmethod
    def from_str(cls, value: str) -> "TransactionType":
        """Coerce arbitrary casing into a valid transaction type."""

        try:
            normalised = value.strip().lower()
            return cls(normalised)
        except (ValueError, AttributeError) as error:
            raise ValueError(f"Unsupported transaction type: {value}") from error


@dataclass(slots=True)
class Transaction:
    """Represent a ledger entry with optional metadata."""

    transaction_id: str
    transaction_type: TransactionType
    description: str
    category: str
    amount: float
    occurred_on: date
    metadata: Dict[str, str] = field(default_factory=dict)

    def duplicate(
        self,
        *,
        transaction_id: str,
        overrides: Optional[Dict[str, object]] = None,
    ) -> "Transaction":
        """Return a copy applying optional overrides for editable fields."""

        overrides = overrides or {}
        coerced_overrides = _coerce_overrides(overrides)
        duplicated = replace(self, transaction_id=transaction_id, **coerced_overrides)
        return duplicated

    def as_dict(self) -> Dict[str, object]:
        """Export the transaction with serialisable values."""

        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type.value,
            "description": self.description,
            "category": self.category,
            "amount": self.amount,
            "occurred_on": self.occurred_on.isoformat(),
            "metadata": dict(self.metadata),
        }


def _coerce_overrides(overrides: Dict[str, object]) -> Dict[str, object]:
    """Validate and coerce override payloads used when duplicating."""

    coerced: Dict[str, object] = {}
    for key, value in overrides.items():
        if key == "transaction_type" and value is not None:
            coerced[key] = TransactionType.from_str(str(value))
        elif key == "occurred_on" and value is not None:
            coerced[key] = _parse_date(value)
        elif key in {"description", "category"} and value is not None:
            coerced[key] = str(value)
        elif key == "amount" and value is not None:
            coerced[key] = float(value)
        elif key == "metadata" and value is not None:
            if isinstance(value, dict):
                coerced[key] = {str(k): str(v) for k, v in value.items()}
            else:
                raise ValueError(
                    "Metadata overrides must be provided as a dictionary of string pairs."
                )
        elif value is not None:
            raise ValueError(f"Override of field '{key}' is not supported.")
    return coerced


def _parse_date(value: object) -> date:
    """Parse ISO formatted strings or date objects safely."""

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError("Dates must be provided as ISO strings or date/datetime instances.")


class FinanceLedger:
    """Manage a collection of transactions with duplication helpers."""

    def __init__(self, transactions: Optional[Iterable[Transaction]] = None) -> None:
        self._transactions: Dict[str, Transaction] = {}
        self._sequence = 0
        if transactions:
            for transaction in transactions:
                self._register(transaction)
        else:
            self._seed_demo_transactions()
        LOGGER.debug("Finance ledger initialised with %s transactions", len(self._transactions))

    def _seed_demo_transactions(self) -> None:
        """Populate the ledger with deterministic demo data."""

        demo_transactions = [
            Transaction(
                transaction_id=self._next_id(),
                transaction_type=TransactionType.INCOME,
                description="Recurring mapping contract",
                category="Commercial",
                amount=12500.0,
                occurred_on=date(2024, 5, 28),
                metadata={"client": "City Council"},
            ),
            Transaction(
                transaction_id=self._next_id(),
                transaction_type=TransactionType.INCOME,
                description="Survey retainer",
                category="Commercial",
                amount=5800.0,
                occurred_on=date(2024, 5, 1),
                metadata={"client": "Greenbuild"},
            ),
            Transaction(
                transaction_id=self._next_id(),
                transaction_type=TransactionType.EXPENSE,
                description="Pilot salary",
                category="Payroll",
                amount=4200.0,
                occurred_on=date(2024, 5, 31),
                metadata={"role": "Senior pilot"},
            ),
            Transaction(
                transaction_id=self._next_id(),
                transaction_type=TransactionType.EXPENSE,
                description="Insurance premium",
                category="Operations",
                amount=950.0,
                occurred_on=date(2024, 5, 20),
                metadata={"provider": "AeroShield"},
            ),
        ]
        for transaction in demo_transactions:
            self._register(transaction)

    def _next_id(self) -> str:
        """Generate a deterministic transaction identifier."""

        self._sequence += 1
        return f"txn_{self._sequence:04d}"

    def _register(self, transaction: Transaction) -> None:
        """Store a transaction ensuring identifiers remain unique."""

        if transaction.transaction_id in self._transactions:
            raise ValueError(f"Transaction {transaction.transaction_id} already exists.")
        self._transactions[transaction.transaction_id] = transaction
        self._sequence = max(self._sequence, int(transaction.transaction_id.split("_")[-1]))

    def list_transactions(self) -> List[Transaction]:
        """Return transactions ordered by most recent date first."""

        return sorted(
            self._transactions.values(),
            key=lambda transaction: (transaction.occurred_on, transaction.transaction_id),
            reverse=True,
        )

    def get_transaction(self, transaction_id: str) -> Transaction:
        """Retrieve a transaction, raising informative errors when missing."""

        if transaction_id not in self._transactions:
            raise KeyError(f"Transaction {transaction_id} not found")
        return self._transactions[transaction_id]

    def duplicate_transaction(
        self, transaction_id: str, overrides: Optional[Dict[str, object]] = None
    ) -> Transaction:
        """Create a new transaction based on an existing one with overrides."""

        original = self.get_transaction(transaction_id)
        new_id = self._next_id()
        duplicated = original.duplicate(transaction_id=new_id, overrides=overrides)
        self._register(duplicated)
        LOGGER.info("Duplicated transaction %s -> %s", transaction_id, new_id)
        return duplicated

    def export_snapshot(self) -> Dict[str, List[Dict[str, object]]]:
        """Export transactions grouped by type for JSON responses."""

        income: List[Dict[str, object]] = []
        expenses: List[Dict[str, object]] = []
        for transaction in self.list_transactions():
            if transaction.transaction_type is TransactionType.INCOME:
                income.append(transaction.as_dict())
            else:
                expenses.append(transaction.as_dict())
        return {"income": income, "expenses": expenses}

"""Mini README: Finance utilities for budgeting within Nerfdrone.

This package groups helpers that simulate basic income and expense
tracking so operators can reason about mission budgets inside the control
centre. Modules expose lightweight, in-memory ledgers that are easy to
extend or replace with persistent storage later. The goal is to provide a
clear API for recording transactions, duplicating them, and exporting
structured snapshots for the web interface.
"""

from .ledger import FinanceLedger, Transaction, TransactionType

__all__ = ["FinanceLedger", "Transaction", "TransactionType"]

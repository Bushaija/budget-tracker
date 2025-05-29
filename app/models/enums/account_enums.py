"""Account-related enumerations."""

from enum import Enum as PyEnum


class AccountCategory(str, PyEnum):
    """Categories for chart of accounts classification."""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class TransactionType(str, PyEnum):
    """Types of financial transactions."""
    DEBIT = "debit"
    CREDIT = "credit"
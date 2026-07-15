"""
Database package.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from .connection import get_db, init_database, engine, SessionLocal
from .models import (
    Base,
    Transaction,
    Mapping,
    PivotConfig,
    AmortizationType,
    AmortizationResult,
    LoanPayment,
    LoanConfig,
    CompteResultatMapping,
    CompteResultatMappingCategory,
    CompteResultatConfig
)

__all__ = [
    "get_db",
    "init_database",
    "engine",
    "SessionLocal",
    "Base",
    "Transaction",
    "Mapping",
    "PivotConfig",
    "AmortizationType",
    "AmortizationResult",
    "LoanPayment",
    "LoanConfig",
    "CompteResultatMapping",
    "CompteResultatMappingCategory",
    "CompteResultatConfig",
]



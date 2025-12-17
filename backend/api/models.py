"""
Pydantic models for API requests and responses.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
Always check with the user before modifying this file.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# Transaction models

class TransactionBase(BaseModel):
    """Base model for transaction."""
    date: date
    quantite: float = Field(..., description="Montant de la transaction")
    nom: str = Field(..., max_length=500, description="Description/nom de la transaction")
    solde: float = Field(..., description="Solde après transaction")
    source_file: Optional[str] = Field(None, max_length=255, description="Fichier source d'origine")


class TransactionCreate(TransactionBase):
    """Model for creating a transaction."""
    pass


class TransactionUpdate(BaseModel):
    """Model for updating a transaction."""
    date: Optional[date] = None
    quantite: Optional[float] = None
    nom: Optional[str] = Field(None, max_length=500)
    solde: Optional[float] = None
    source_file: Optional[str] = Field(None, max_length=255)


class TransactionResponse(TransactionBase):
    """Model for transaction response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Model for list of transactions response."""
    transactions: List[TransactionResponse]
    total: int
    page: int = 1
    page_size: int = 100


# Health check models

class HealthResponse(BaseModel):
    """Model for health check response."""
    status: str
    message: Optional[str] = None
    database: Optional[str] = None

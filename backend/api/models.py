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
    date: Optional[str] = None  # Accept string, will be converted to date in route
    quantite: Optional[float] = None
    nom: Optional[str] = Field(None, max_length=500)
    solde: Optional[float] = None
    source_file: Optional[str] = Field(None, max_length=255)
    
    class Config:
        from_attributes = True


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


# File upload models

class ColumnMapping(BaseModel):
    """Model for column mapping (file column → database column)."""
    file_column: str = Field(..., description="Nom de la colonne dans le fichier")
    db_column: str = Field(..., description="Nom de la colonne en BDD (date, quantite, nom)")


class FilePreviewResponse(BaseModel):
    """Model for file preview response."""
    filename: str
    encoding: str
    separator: str
    total_rows: int
    column_mapping: List[ColumnMapping] = Field(..., description="Mapping proposé des colonnes")
    preview: List[dict] = Field(..., description="Premières lignes pour aperçu")
    validation_errors: List[str] = Field(default_factory=list, description="Erreurs de validation")
    stats: dict = Field(..., description="Statistiques (dates min/max, etc.)")


class FileImportRequest(BaseModel):
    """Model for file import request."""
    filename: str
    column_mapping: List[ColumnMapping] = Field(..., description="Mapping confirmé par l'utilisateur")


class DuplicateTransaction(BaseModel):
    """Model for duplicate transaction."""
    date: str
    quantite: float
    nom: str
    existing_id: int = Field(..., description="ID de la transaction existante en BDD")


class FileImportResponse(BaseModel):
    """Model for file import response."""
    filename: str
    imported_count: int
    duplicates_count: int
    errors_count: int
    duplicates: List[DuplicateTransaction] = Field(default_factory=list)
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    message: str


class FileImportHistory(BaseModel):
    """Model for file import history."""
    id: int
    filename: str
    imported_at: datetime
    imported_count: int
    duplicates_count: int
    errors_count: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    class Config:
        from_attributes = True

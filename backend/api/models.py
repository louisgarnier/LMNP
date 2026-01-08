"""
Pydantic models for API requests and responses.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
Always check with the user before modifying this file.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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
    level_1: Optional[str] = None
    level_2: Optional[str] = None
    level_3: Optional[str] = None

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


class TransactionError(BaseModel):
    """Model for transaction error details."""
    line_number: int = Field(..., description="Numéro de ligne dans le fichier (1-based)")
    date: Optional[str] = None
    quantite: Optional[float] = None
    nom: Optional[str] = None
    error_message: str = Field(..., description="Message d'erreur détaillé")


class FileImportResponse(BaseModel):
    """Model for file import response."""
    filename: str
    imported_count: int
    duplicates_count: int
    errors_count: int
    duplicates: List[DuplicateTransaction] = Field(default_factory=list)
    errors: List[TransactionError] = Field(default_factory=list, description="Liste détaillée des erreurs")
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


# Mapping models

class MappingBase(BaseModel):
    """Base model for mapping."""
    nom: str = Field(..., max_length=500, description="Nom/pattern de transaction")
    level_1: str = Field(..., max_length=100, description="Catégorie principale")
    level_2: str = Field(..., max_length=100, description="Sous-catégorie")
    level_3: Optional[str] = Field(None, max_length=100, description="Détail spécifique")
    is_prefix_match: bool = Field(True, description="Si True, match par préfixe")
    priority: int = Field(0, description="Priorité pour résolution de conflits")


class MappingCreate(MappingBase):
    """Model for creating a mapping."""
    pass


# Allowed mapping models

class AllowedMappingBase(BaseModel):
    """Base model for allowed mapping."""
    level_1: str = Field(..., max_length=100, description="Catégorie principale")
    level_2: str = Field(..., max_length=100, description="Sous-catégorie")
    level_3: Optional[str] = Field(None, max_length=100, description="Détail spécifique")
    is_hardcoded: bool = Field(False, description="True si hard codé (protégé)")


class AllowedMappingCreate(AllowedMappingBase):
    """Model for creating an allowed mapping."""
    pass


class AllowedMappingResponse(AllowedMappingBase):
    """Model for allowed mapping response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AllowedMappingListResponse(BaseModel):
    """Model for list of allowed mappings."""
    mappings: List[AllowedMappingResponse]
    total: int


class MappingUpdate(BaseModel):
    """Model for updating a mapping."""
    nom: Optional[str] = Field(None, max_length=500)
    level_1: Optional[str] = Field(None, max_length=100)
    level_2: Optional[str] = Field(None, max_length=100)
    level_3: Optional[str] = Field(None, max_length=100)
    is_prefix_match: Optional[bool] = None
    priority: Optional[int] = None


class MappingResponse(MappingBase):
    """Model for mapping response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MappingListResponse(BaseModel):
    """Model for list of mappings response."""
    mappings: List[MappingResponse]
    total: int


class MappingPreviewResponse(BaseModel):
    """Model for mapping file preview response."""
    filename: str
    total_rows: int
    column_mapping: List[ColumnMapping] = Field(..., description="Mapping proposé des colonnes (nom, level_1, level_2, level_3)")
    preview: List[dict] = Field(..., description="Premières lignes pour aperçu (max 10)")
    validation_errors: List[str] = Field(default_factory=list, description="Erreurs de validation")
    stats: dict = Field(..., description="Statistiques (nombre de mappings valides, etc.)")


class MappingError(BaseModel):
    """Model for mapping error details."""
    line_number: int = Field(..., description="Numéro de ligne dans le fichier (1-based)")
    nom: Optional[str] = None
    level_1: Optional[str] = None
    level_2: Optional[str] = None
    level_3: Optional[str] = None
    error_message: str = Field(..., description="Message d'erreur détaillé")


class DuplicateMapping(BaseModel):
    """Model for duplicate mapping."""
    nom: str
    existing_id: int = Field(..., description="ID du mapping existant en BDD")


class MappingImportResponse(BaseModel):
    """Model for mapping import response."""
    filename: str
    imported_count: int
    duplicates_count: int
    errors_count: int
    duplicates: List[DuplicateMapping] = Field(default_factory=list)
    errors: List[MappingError] = Field(default_factory=list, description="Liste détaillée des erreurs")
    message: str


class MappingImportHistory(BaseModel):
    """Model for mapping import history."""
    id: int
    filename: str
    imported_at: datetime
    imported_count: int
    duplicates_count: int
    errors_count: int

    class Config:
        from_attributes = True


# Pivot Config models

class PivotConfigBase(BaseModel):
    """Base model for pivot config."""
    name: str = Field(..., max_length=255, description="Nom du tableau croisé")
    config: Dict[str, Any] = Field(..., description="Configuration JSON (rows, columns, data, filters)")


class PivotConfigCreate(PivotConfigBase):
    """Model for creating a pivot config."""
    pass


class PivotConfigUpdate(BaseModel):
    """Model for updating a pivot config."""
    name: Optional[str] = Field(None, max_length=255, description="Nom du tableau croisé")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration JSON (rows, columns, data, filters)")


class PivotConfigResponse(PivotConfigBase):
    """Model for pivot config response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PivotConfigListResponse(BaseModel):
    """Model for list of pivot configs."""
    items: List[PivotConfigResponse]
    total: int


# Amortization models

class AmortizationResultsResponse(BaseModel):
    """Model for amortization results response (aggregated by year and category)."""
    results: Dict[int, Dict[str, float]] = Field(..., description="Results by year: {year: {category: amount, ...}}")
    totals_by_year: Dict[int, float] = Field(..., description="Total by year")
    totals_by_category: Dict[str, float] = Field(..., description="Total by category")
    grand_total: float = Field(..., description="Grand total")


class AmortizationAggregatedResponse(BaseModel):
    """Model for aggregated amortization results (ready for pivot table display)."""
    categories: List[str] = Field(..., description="List of categories")
    years: List[int] = Field(..., description="List of years")
    data: List[List[float]] = Field(..., description="Matrix data: data[row][col] = amount for category[row] and year[years[col]]")
    totals_by_category: Dict[str, float] = Field(..., description="Total by category")
    totals_by_year: Dict[int, float] = Field(..., description="Total by year")
    grand_total: float = Field(..., description="Grand total")


class AmortizationResultDetail(BaseModel):
    """Model for a single amortization result detail."""
    transaction_id: int
    transaction_date: date
    transaction_nom: str
    transaction_quantite: float
    year: int
    category: str
    amount: float

    class Config:
        from_attributes = True


class AmortizationDetailsResponse(BaseModel):
    """Model for amortization details response (drill-down)."""
    items: List[AmortizationResultDetail]
    total: int
    page: int = 1
    page_size: int = 100


class AmortizationRecalculateResponse(BaseModel):
    """Model for recalculate response."""
    message: str
    results_created: int


# AmortizationType models

class AmortizationTypeBase(BaseModel):
    """Base model for amortization type."""
    name: str = Field(..., max_length=255, description="Nom du type d'amortissement")
    level_2_value: str = Field(..., max_length=100, description="Valeur level_2 à considérer")
    level_1_values: List[str] = Field(default_factory=list, description="Liste des valeurs level_1 mappées")
    start_date: Optional[date] = Field(None, description="Date de début d'amortissement (override, nullable)")
    duration: float = Field(..., ge=0, description="Durée d'amortissement en années (0 = non amortissable)")
    annual_amount: Optional[float] = Field(None, description="Annuité d'amortissement (override, nullable)")


class AmortizationTypeCreate(AmortizationTypeBase):
    """Model for creating an amortization type."""
    pass


class AmortizationTypeUpdate(BaseModel):
    """Model for updating an amortization type."""
    name: Optional[str] = Field(None, max_length=255)
    level_2_value: Optional[str] = Field(None, max_length=100)
    level_1_values: Optional[List[str]] = None
    start_date: Optional[date] = None
    duration: Optional[float] = Field(None, ge=0)
    annual_amount: Optional[float] = None
    
    class Config:
        from_attributes = True


class AmortizationTypeResponse(AmortizationTypeBase):
    """Model for amortization type response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AmortizationTypeListResponse(BaseModel):
    """Model for list of amortization types."""
    items: List[AmortizationTypeResponse]
    total: int


class AmortizationTypeAmountResponse(BaseModel):
    """Model for amortization type amount calculation."""
    type_id: int
    type_name: str
    amount: float = Field(..., description="Montant total d'immobilisation (somme des transactions)")


class AmortizationTypeCumulatedResponse(BaseModel):
    """Model for amortization type cumulated amount calculation."""
    type_id: int
    type_name: str
    cumulated_amount: float = Field(..., description="Montant cumulé d'amortissement (somme des AmortizationResult)")


class AmortizationTypeTransactionCountResponse(BaseModel):
    """Model for amortization type transaction count."""
    type_id: int
    type_name: str
    transaction_count: int = Field(..., description="Nombre de transactions correspondant au type")

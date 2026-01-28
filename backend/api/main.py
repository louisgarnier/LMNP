"""
FastAPI main application.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
Always check with the user before modifying this file.
"""

import sys
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.connection import init_database

# Import routes
from backend.api.routes import transactions, mappings, enrichment, analytics, pivot_configs, amortization, amortization_types, loan_payments, loan_configs, compte_resultat, bilan, properties

# Create FastAPI app
app = FastAPI(
    title="LMNP API",
    description="API pour la gestion comptable LMNP (Location Meublée Non Professionnelle)",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL (e.g., "http://localhost:3000")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(properties.router, prefix="/api", tags=["properties"])
app.include_router(transactions.router, prefix="/api", tags=["transactions"])
app.include_router(mappings.router, prefix="/api", tags=["mappings"])
app.include_router(enrichment.router, prefix="/api", tags=["enrichment"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(pivot_configs.router, prefix="/api", tags=["pivot-configs"])
app.include_router(amortization.router, prefix="/api", tags=["amortization"])
app.include_router(amortization_types.router, prefix="/api", tags=["amortization-types"])
app.include_router(loan_payments.router, prefix="/api", tags=["loan-payments"])
app.include_router(loan_configs.router, prefix="/api", tags=["loan-configs"])
app.include_router(compte_resultat.router, prefix="/api", tags=["compte-resultat"])
app.include_router(bilan.router, prefix="/api", tags=["bilan"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_database()


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {"message": "API is running", "status": "ok"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}



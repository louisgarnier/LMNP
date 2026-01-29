"""
FastAPI main application.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
Always check with the user before modifying this file.
"""

import sys
import logging
import traceback
from pathlib import Path

# Add project root to path for shared imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging avec fichiers séparés
from backend.api.utils.logger_config import (
    setup_api_logger, 
    setup_backend_logger, 
    setup_database_logger,
    setup_root_logging,
    redirect_stdout_stderr_to_log
)
from datetime import datetime

# IMPORTANT: Configurer le logging root EN PREMIER pour capturer TOUTES les erreurs
setup_root_logging()

# Rediriger stdout/stderr vers le fichier de log backend
log_file = redirect_stdout_stderr_to_log()

# Configurer les loggers spécifiques
setup_backend_logger()
setup_api_logger()
setup_database_logger()

# Logger de démarrage
logger = logging.getLogger("backend")
logger.info("="*80)
logger.info("🚀 DÉMARRAGE DU SERVEUR BACKEND")
logger.info("="*80)
logger.info(f"📁 Logs backend: logs/backend_{datetime.now().strftime('%Y-%m-%d')}.log")
logger.info(f"📁 Logs API: logs/api_{datetime.now().strftime('%Y-%m-%d')}.log")
logger.info(f"📁 Logs database: logs/database_{datetime.now().strftime('%Y-%m-%d')}.log")
logger.info(f"📁 Logs frontend: logs/frontend_{datetime.now().strftime('%Y-%m-%d')}.log")
logger.info("="*80)
logger.info("✅ Logging root configuré - Toutes les erreurs seront capturées")
logger.info("="*80)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.database.connection import init_database
import traceback
import time

# Import routes
from backend.api.routes import transactions, mappings, enrichment, analytics, pivot_configs, amortization, amortization_types, loan_payments, loan_configs, compte_resultat, bilan, properties, logs

# Import middleware de logging
from backend.api.middleware.logging_middleware import LoggingMiddleware

# Create FastAPI app
app = FastAPI(
    title="LMNP API",
    description="API pour la gestion comptable LMNP (Location Meublée Non Professionnelle)",
    version="1.0.0"
)

# Ajouter le middleware de logging EN PREMIER pour capturer toutes les requêtes
app.add_middleware(LoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL (e.g., "http://localhost:3000")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestionnaire d'exceptions global pour capturer toutes les erreurs
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Capture toutes les exceptions non gérées et les log."""
    from backend.api.utils.logger_config import get_logger
    
    # Logger dans le logger root (backend) pour qu'il apparaisse dans backend_*.log
    root_logger = logging.getLogger()
    root_logger.error(
        f"❌ EXCEPTION NON GÉRÉE dans {request.method} {request.url.path}: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    
    # Logger aussi dans le logger API
    logger = get_logger("backend.api.exceptions")
    logger.error(
        f"EXCEPTION NON GÉRÉE: {type(exc).__name__}: {str(exc)}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        },
        exc_info=True
    )
    
    # Afficher aussi dans le terminal (via print pour être sûr)
    print(f"\n{'='*80}")
    print(f"❌ ERREUR CRITIQUE: {type(exc).__name__}: {str(exc)}")
    print(f"   Méthode: {request.method}")
    print(f"   Path: {request.url.path}")
    print(f"   Traceback:")
    traceback.print_exc()
    print(f"{'='*80}\n")
    
    # Retourner une réponse d'erreur
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Erreur interne du serveur: {str(exc)}",
            "error_type": type(exc).__name__,
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Capture les exceptions HTTP et les log."""
    from backend.api.utils.logger_config import get_logger
    
    # Logger dans le logger root (backend) pour qu'il apparaisse dans backend_*.log
    root_logger = logging.getLogger()
    
    # Logger seulement les erreurs 5xx et 4xx importantes
    if exc.status_code >= 500:
        root_logger.error(
            f"❌ HTTP EXCEPTION {exc.status_code} dans {request.method} {request.url.path}: {exc.detail}",
            exc_info=True
        )
        logger = get_logger("backend.api.exceptions")
        logger.error(
            f"HTTP EXCEPTION {exc.status_code}: {exc.detail}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
            exc_info=True
        )
    elif exc.status_code >= 400:
        root_logger.warning(
            f"⚠️ HTTP EXCEPTION {exc.status_code} dans {request.method} {request.url.path}: {exc.detail}"
        )
        logger = get_logger("backend.api.exceptions")
        logger.warning(
            f"HTTP EXCEPTION {exc.status_code}: {exc.detail}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": exc.status_code,
                "detail": exc.detail,
            }
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Capture les erreurs de validation et les log."""
    from backend.api.utils.logger_config import get_logger
    logger = get_logger("backend.api.exceptions")
    
    logger.warning(
        f"VALIDATION ERROR: {exc.errors()}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "errors": exc.errors(),
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
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
app.include_router(logs.router, prefix="/api", tags=["logs"])


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



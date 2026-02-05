"""
Middleware de logging pour capturer toutes les requêtes et erreurs.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import traceback

from backend.api.utils.logger_config import get_logger

logger = get_logger("backend.api.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logger toutes les requêtes et réponses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Logger la requête entrante
        logger.info(
            f"[{request.method}] {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None,
            }
        )
        
        try:
            # Exécuter la requête
            response = await call_next(request)
            
            # Calculer le temps de traitement
            process_time = time.time() - start_time
            
            # Logger la réponse
            logger.info(
                f"[{request.method}] {request.url.path} - {response.status_code}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                }
            )
            
            return response
            
        except Exception as e:
            # Calculer le temps de traitement
            process_time = time.time() - start_time
            
            # Logger dans le logger root (backend) pour qu'il apparaisse dans backend_*.log
            root_logger = logging.getLogger()
            root_logger.error(
                f"❌ ERREUR dans middleware [{request.method}] {request.url.path}: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            
            # Logger aussi dans le logger API
            logger.error(
                f"[{request.method}] {request.url.path} - ERREUR: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time": f"{process_time:.3f}s",
                    "traceback": traceback.format_exc(),
                },
                exc_info=True
            )
            
            # Afficher aussi dans le terminal (via print pour être sûr)
            print(f"\n{'='*80}")
            print(f"❌ ERREUR MIDDLEWARE: {type(e).__name__}: {str(e)}")
            print(f"   Méthode: {request.method}")
            print(f"   Path: {request.url.path}")
            print(f"   Traceback:")
            traceback.print_exc()
            print(f"{'='*80}\n")
            
            # Retourner une réponse d'erreur
            return JSONResponse(
                status_code=500,
                content={
                    "detail": f"Erreur interne du serveur: {str(e)}",
                    "error_type": type(e).__name__,
                }
            )

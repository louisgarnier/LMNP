"""
API routes for logging (frontend logs).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import json
from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from backend.api.utils.logger_config import get_logger

router = APIRouter()

# Chemin vers le dossier logs
project_root = Path(__file__).parent.parent.parent.parent
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)


@router.post("/logs/frontend")
async def receive_frontend_log(log_entry: Dict[str, Any]):
    """
    Recevoir un log du frontend et l'écrire dans le fichier de logs frontend.
    
    Format attendu:
    {
        "timestamp": "2026-01-29T12:00:00.000Z",
        "level": "info|warn|error|debug",
        "category": "API|Component|etc",
        "message": "Message du log",
        "data": {...}  # Optionnel
    }
    """
    logger = get_logger("backend.api.routes.logs")
    
    try:
        # Créer le nom du fichier de log frontend avec la date
        date_str = datetime.now().strftime("%Y-%m-%d")
        frontend_log_file = logs_dir / f"frontend_{date_str}.log"
        
        # Formater le log
        timestamp = log_entry.get("timestamp", datetime.now().isoformat())
        level = log_entry.get("level", "info").upper()
        category = log_entry.get("category", "UNKNOWN")
        message = log_entry.get("message", "")
        data = log_entry.get("data", {})
        
        # Formater la ligne de log
        data_str = f" | Data: {json.dumps(data, ensure_ascii=False)}" if data else ""
        log_line = f"{timestamp} - [FRONTEND] - {level} - [{category}] - {message}{data_str}\n"
        
        # Écrire dans le fichier
        try:
            with open(frontend_log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
            logger.debug(f"Log frontend écrit dans {frontend_log_file}")
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture du log frontend dans le fichier: {e}", exc_info=True)
            raise
        
        # Logger aussi dans le backend pour traçabilité (seulement pour les erreurs et warnings)
        if level == "ERROR":
            logger.error(f"[Frontend] {category}: {message}", extra={"data": data})
        elif level == "WARN":
            logger.warning(f"[Frontend] {category}: {message}", extra={"data": data})
        # Les logs INFO sont seulement dans le fichier frontend pour éviter la surcharge
        
        return {"status": "ok", "logged": True, "file": str(frontend_log_file)}
        
    except Exception as e:
        logger.error(f"Erreur lors de l'écriture du log frontend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'écriture du log: {str(e)}")


@router.get("/logs/frontend")
async def get_frontend_logs(limit: int = 100):
    """
    Récupérer les logs frontend récents.
    """
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        frontend_log_file = logs_dir / f"frontend_{date_str}.log"
        
        if not frontend_log_file.exists():
            return {"logs": [], "total": 0}
        
        # Lire les dernières lignes
        with open(frontend_log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Prendre les N dernières lignes
        recent_logs = lines[-limit:] if len(lines) > limit else lines
        
        return {
            "logs": [line.strip() for line in recent_logs],
            "total": len(lines),
            "returned": len(recent_logs)
        }
        
    except Exception as e:
        logger = get_logger("backend.api.routes.logs")
        logger.error(f"Erreur lors de la lecture des logs frontend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture des logs: {str(e)}")

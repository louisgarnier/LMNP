"""
Configuration centralisée du logging pour le backend.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import os
import traceback

# Chemin vers le dossier logs (à la racine du projet)
project_root = Path(__file__).parent.parent.parent.parent
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

# Format de date pour les noms de fichiers
date_str = datetime.now().strftime("%Y-%m-%d")

# Configuration des fichiers de logs
LOG_FILES = {
    "backend": logs_dir / f"backend_{date_str}.log",
    "api": logs_dir / f"api_{date_str}.log",
    "database": logs_dir / f"database_{date_str}.log",
    "tests": logs_dir / f"tests_{date_str}.log",
}

# Format des logs
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_backend_logger():
    """Configure le logger pour le backend général."""
    logger = logging.getLogger("backend")
    logger.setLevel(logging.INFO)
    
    # Éviter les doublons
    if logger.handlers:
        return logger
    
    # Handler pour fichier
    file_handler = logging.FileHandler(LOG_FILES["backend"], encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_api_logger():
    """Configure le logger pour les routes API."""
    logger = logging.getLogger("backend.api")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Désactiver la propagation pour éviter les doublons
    
    # Éviter les doublons
    if logger.handlers:
        return logger
    
    # Handler pour fichier API
    file_handler = logging.FileHandler(LOG_FILES["api"], encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_database_logger():
    """Configure le logger pour les opérations de base de données."""
    logger = logging.getLogger("backend.database")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Désactiver la propagation pour éviter les doublons
    
    # Éviter les doublons
    if logger.handlers:
        return logger
    
    # Handler pour fichier database
    file_handler = logging.FileHandler(LOG_FILES["database"], encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_test_logger():
    """Configure le logger pour les tests."""
    logger = logging.getLogger("backend.tests")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Désactiver la propagation pour éviter les doublons
    
    # Éviter les doublons
    if logger.handlers:
        return logger
    
    # Handler pour fichier tests
    file_handler = logging.FileHandler(LOG_FILES["tests"], encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str):
    """
    Récupère un logger configuré selon le nom.
    
    Args:
        name: Nom du logger (ex: "backend.api.routes.properties")
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    
    # Si le logger commence par "backend.api", configurer le logger parent et utiliser la propagation
    if name.startswith("backend.api"):
        # Configurer le logger parent "backend.api"
        parent_logger = setup_api_logger()
        # Les loggers enfants hériteront automatiquement des handlers du parent
        logger.setLevel(logging.INFO)
        logger.propagate = True  # Activer la propagation vers le parent
    # Si le logger commence par "backend.database", utiliser le logger database
    elif name.startswith("backend.database"):
        parent_logger = setup_database_logger()
        logger.setLevel(logging.INFO)
        logger.propagate = True
    # Si le logger commence par "backend.tests", utiliser le logger tests
    elif name.startswith("backend.tests"):
        parent_logger = setup_test_logger()
        logger.setLevel(logging.INFO)
        logger.propagate = True
    # Sinon, utiliser le logger backend général
    else:
        parent_logger = setup_backend_logger()
        logger.setLevel(logging.INFO)
        logger.propagate = True
    
    return logger


def setup_root_logging():
    """
    Configure le logging root pour capturer TOUTES les erreurs et exceptions non gérées.
    Cette fonction doit être appelée au démarrage de l'application.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    backend_log_file = LOG_FILES["backend"]
    
    # Configurer le logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capturer tous les niveaux
    
    # Éviter les doublons
    if any(isinstance(h, logging.FileHandler) and h.baseFilename == str(backend_log_file) for h in root_logger.handlers):
        return root_logger
    
    # Handler pour fichier backend (capture TOUT)
    file_handler = logging.FileHandler(backend_log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Capturer tous les niveaux
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Handler pour console (garder pour le terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Capturer toutes les exceptions non gérées
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handler pour toutes les exceptions non gérées."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        root_logger.error(
            f"EXCEPTION NON GÉRÉE: {exc_type.__name__}: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception
    
    # Configurer les loggers de bibliothèques tierces pour qu'ils loggent aussi
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Logger les erreurs SQL
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    return root_logger


class TeeOutput:
    """
    Classe pour rediriger stdout/stderr vers à la fois le terminal ET le fichier de log.
    """
    def __init__(self, *files):
        self.files = files
    
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()


def redirect_stdout_stderr_to_log():
    """
    Redirige stdout et stderr vers le fichier de log backend en plus du terminal.
    Retourne le fichier ouvert pour qu'il reste ouvert.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    backend_log_file = LOG_FILES["backend"]
    
    # Ouvrir le fichier en mode append
    log_file = open(backend_log_file, 'a', encoding='utf-8')
    
    # Créer un TeeOutput qui écrit à la fois dans le terminal et le fichier
    tee_stdout = TeeOutput(sys.stdout, log_file)
    tee_stderr = TeeOutput(sys.stderr, log_file)
    
    # Rediriger stdout et stderr
    sys.stdout = tee_stdout
    sys.stderr = tee_stderr
    
    return log_file

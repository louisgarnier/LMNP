"""Crée la table classification_rules sur la base de prod (idempotent)."""
from backend.database.connection import engine
from backend.database.models import Base, ClassificationRule

def main() -> None:
    ClassificationRule.__table__.create(bind=engine, checkfirst=True)
    print("[migration] classification_rules créée (ou déjà présente).")

if __name__ == "__main__":
    main()

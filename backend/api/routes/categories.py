from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Category, CategoryGroup

router = APIRouter()

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    rows = (db.query(Category, CategoryGroup)
            .join(CategoryGroup, Category.group_id == CategoryGroup.id)
            .order_by(CategoryGroup.label, Category.label).all())
    return {"items": [{"id": c.id, "label": c.label,
                       "group_label": g.label, "nature": g.nature}
                      for c, g in rows]}

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.models import FiscalSettings


def test_fiscal_settings_defauts():
    s = FiscalSettings()
    # défauts métier : déficit 10 ans, amortissements illimités (NULL)
    assert FiscalSettings.__tablename__ == "fiscal_settings"
    cols = {c.name for c in FiscalSettings.__table__.columns}
    assert {"id", "deficit_report_years", "amort_report_years",
            "created_at", "updated_at"} <= cols

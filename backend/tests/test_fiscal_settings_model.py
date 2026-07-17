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

    cols_by_name = FiscalSettings.__table__.columns
    assert cols_by_name["deficit_report_years"].nullable is False
    assert cols_by_name["deficit_report_years"].default.arg == 10
    assert cols_by_name["amort_report_years"].nullable is True

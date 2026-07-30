"""Preview CONTPL rows without passwords."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.business_session import business_engine

with business_engine.connect() as conn:
    rows = conn.execute(
        text(
            """
            SELECT L_uid, l_id, LEN(P_w) AS pw_len, full_name, r_str, dt_create, dt_exp
            FROM dbo.CONTPL
            ORDER BY L_uid
            """
        )
    ).fetchall()
    for r in rows:
        print(r)

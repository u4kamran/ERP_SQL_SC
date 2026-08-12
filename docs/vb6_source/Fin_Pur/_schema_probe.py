from sqlalchemy import text

from app.database.business_session import BusinessSessionLocal

TABLES = [
    "Fin_Pur_M",
    "Fin_Pur_D",
    "fin_c001",
    "fin_c003",
    "fin_ldgr",
    "fin_supp_items",
    "gl0006",
    "City",
    "co",
    "gsetup",
]


def main():
    db = BusinessSessionLocal()
    try:
        for t in TABLES:
            try:
                rows = db.execute(
                    text(
                        """
                        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = :t
                        ORDER BY ORDINAL_POSITION
                        """
                    ),
                    {"t": t},
                ).fetchall()
                print("===", t, "cols", len(rows))
                for r in rows:
                    print(" ", r[0], r[1], r[2], r[3])
            except Exception as e:
                print("===", t, "ERR", e)
        # sample gsetup keys
        try:
            row = db.execute(text("SELECT TOP 1 * FROM gsetup")).mappings().first()
            if row:
                print("=== gsetup keys", list(row.keys())[:40])
                for k in ("stax_type", "STaxType", "cSTaxType", "fiscal_start", "fiscal_end"):
                    for rk in row.keys():
                        if rk.lower() == k.lower():
                            print(" ", rk, "=", row[rk])
        except Exception as e:
            print("gsetup err", e)
        # fin_c001 doc 2
        try:
            row = db.execute(text("SELECT TOP 1 * FROM fin_c001 WHERE doc_id = 2")).mappings().first()
            print("=== fin_c001 doc2", dict(row) if row else None)
        except Exception as e:
            print("fin_c001 err", e)
        try:
            row = db.execute(text("SELECT TOP 1 * FROM fin_c003 WHERE doc_id = 2")).mappings().first()
            print("=== fin_c003 doc2 keys", list(row.keys()) if row else None)
            if row:
                print(dict(row))
        except Exception as e:
            print("fin_c003 err", e)
    finally:
        db.close()


if __name__ == "__main__":
    main()

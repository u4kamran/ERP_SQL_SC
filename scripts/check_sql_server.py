"""Check SQL Server connection and list databases (reads .env)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config.settings import settings

import pyodbc

conn_str = (
    f"DRIVER={{{settings.db_driver}}};"
    f"SERVER={settings.db_server};"
    f"DATABASE=master;"
    f"UID={settings.db_user};"
    f"PWD={settings.db_password};"
    f"TrustServerCertificate={settings.db_trust_server_certificate};"
    f"Encrypt={settings.db_encrypt};"
)

print(f"Server: {settings.db_server}")
print(f"User:   {settings.db_user}")
print()

try:
    conn = pyodbc.connect(conn_str, timeout=10)
except Exception as exc:
    print(f"CONNECTION FAILED: {exc}")
    raise SystemExit(1)

cur = conn.cursor()
cur.execute("SELECT @@VERSION")
print("SQL Server version:")
print(cur.fetchone()[0][:200])
print()

cur.execute(
    "SELECT name FROM sys.databases "
    "WHERE name LIKE '%2626%' OR name LIKE '%2627%' OR name LIKE '%nahsl%' OR name LIKE '%NSDS%' "
    "ORDER BY name"
)
rows = [r[0] for r in cur.fetchall()]
print("Matching databases:")
for name in rows:
    print(f"  - {name}")

if not rows:
    print("  (none found)")

conn.close()
print()
print("Connection OK")

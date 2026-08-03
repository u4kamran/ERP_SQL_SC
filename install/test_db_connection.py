"""Try common SQL Server connection strings from the app machine."""

import re
import sys

try:
    import pyodbc
except ImportError:
    print("pyodbc not installed. Run: pip install pyodbc")
    raise SystemExit(1)


def clean_server(value: str) -> str:
  """Remove bad leading slashes from batch/cmd input."""
  value = (value or "").strip().strip('"')
  value = re.sub(r"^\\+", "", value)
  return value


host = clean_server(sys.argv[1] if len(sys.argv) > 1 else "shaheenhp")
user = sys.argv[2] if len(sys.argv) > 2 else "sa"
password = sys.argv[3] if len(sys.argv) > 3 else ""
biz_db = sys.argv[4] if len(sys.argv) > 4 else "nsds2626"
auth_db = sys.argv[5] if len(sys.argv) > 5 else "NSDS2626_AUTH"

servers = [
    host,
    f"{host}\\SQLEXPRESS",
    "shaheenhp",
    "shaheenhp\\SQLEXPRESS",
]

seen = set()
servers = [s for s in servers if s and not (s in seen or seen.add(s))]

driver = "ODBC Driver 18 for SQL Server"
ok_server = None

print(f"Driver: {driver}")
print()

for server in servers:
    for db in (biz_db, auth_db):
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={db};"
            f"UID={user};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=no;"
        )
        label = f"{server} / {db}"
        try:
            conn = pyodbc.connect(conn_str, timeout=8)
            conn.close()
            print(f"OK   {label}")
            ok_server = ok_server or server
        except Exception as exc:
            msg = str(exc).replace("\n", " ")
            if len(msg) > 120:
                msg = msg[:120] + "..."
            print(f"FAIL {label}")
            print(f"     {msg}")

print()
if ok_server:
    print("SUCCESS. Use this in .env:")
    print(f"  DB_SERVER={ok_server}")
    print(f"  BUSINESS_DB_SERVER={ok_server}")
else:
    print("No connection worked.")
    print("Ask on database PC: is SQL default instance or SQLEXPRESS?")
    print("Try database PC IP in .env if name does not resolve.")
    raise SystemExit(1)

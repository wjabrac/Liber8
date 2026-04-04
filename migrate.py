import os
import psycopg
from pathlib import Path

def run_migrations(dsn: str, migrations_dir: str):
    print(f"Connecting to {dsn} to apply migrations from {migrations_dir}")
    directory = Path(migrations_dir)
    
    with psycopg.connect(dsn, autocommit=True) as conn:
        for sql_file in sorted(directory.glob("*.sql")):
            print(f"Applying {sql_file.name}...")
            with open(sql_file, "r") as f:
                sql = f.read()
            with conn.cursor() as cur:
                cur.execute(sql)
            print(f"Applied {sql_file.name}")

if __name__ == "__main__":
    dsn = "postgres://postgres:mysecretpassword@127.0.0.1:5432/libr8_test"
    run_migrations(dsn, "sql/postgres")

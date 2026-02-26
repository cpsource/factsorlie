#!/usr/bin/env python3
"""Check for duplicate question_gz in querys and keep only the latest row per question."""

import os
import sys

from dotenv import load_dotenv
import psycopg2

load_dotenv(os.path.expanduser("~/.env"))

url = os.environ.get("NEON_DATABASE_URL")
if not url:
    print("Error: NEON_DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

conn = psycopg2.connect(url, sslmode="require")
with conn:
    with conn.cursor() as cur:
        # Find duplicates
        cur.execute(
            "SELECT question_gz, COUNT(*) as cnt FROM querys "
            "GROUP BY question_gz HAVING COUNT(*) > 1"
        )
        dupes = cur.fetchall()
        if not dupes:
            print("No duplicates found. Safe to add UNIQUE constraint.")
            conn.close()
            sys.exit(0)

        print(f"Found {len(dupes)} duplicate question(s)")

        # For each duplicate, keep the row with the highest idx, delete the rest
        total_deleted = 0
        for question_gz, cnt in dupes:
            cur.execute(
                "DELETE FROM querys WHERE question_gz = %s AND idx NOT IN ("
                "  SELECT MAX(idx) FROM querys WHERE question_gz = %s"
                ")",
                (question_gz, question_gz),
            )
            deleted = cur.rowcount
            total_deleted += deleted
            print(f"  removed {deleted} duplicate(s) (kept latest)")

        print(f"Deleted {total_deleted} total duplicate rows")
        print("Safe to add UNIQUE constraint now.")
conn.close()

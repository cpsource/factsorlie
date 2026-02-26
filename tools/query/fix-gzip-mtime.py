#!/usr/bin/env python3
"""One-time fix: recompress question_gz in querys with mtime=0 for deterministic matching."""

import gzip
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
        cur.execute("SELECT idx, question_gz, response_gz FROM querys")
        rows = cur.fetchall()
        print(f"Found {len(rows)} rows")
        for idx, question_gz, response_gz in rows:
            question = gzip.decompress(bytes(question_gz)).decode("utf-8")
            response = gzip.decompress(bytes(response_gz)).decode("utf-8")
            new_q = gzip.compress(question.encode("utf-8"), mtime=0)
            new_r = gzip.compress(response.encode("utf-8"), mtime=0)
            cur.execute(
                "UPDATE querys SET question_gz = %s, response_gz = %s WHERE idx = %s",
                (new_q, new_r, idx),
            )
            print(f"  updated idx={idx}")
conn.close()
print("Done")

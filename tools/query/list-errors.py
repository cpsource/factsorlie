#!/usr/bin/env python3
"""List recent rows from the errors table."""

import argparse
import gzip
import json
import os
import sys

from dotenv import load_dotenv
import psycopg2


def main():
    load_dotenv(os.path.expanduser("~/.env"))

    parser = argparse.ArgumentParser(description="List recent rows from the errors table")
    parser.add_argument("--limit", type=int, default=10, help="Number of rows to show (default: 10)")
    args = parser.parse_args()

    url = os.environ.get("NEON_DATABASE_URL")
    if not url:
        print("Error: NEON_DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(url, sslmode="require")
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT idx, row_src, question_gz, error, created_at FROM errors ORDER BY idx DESC LIMIT %s",
                (args.limit,),
            )
            rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No rows found.")
        return

    print(f"{'idx':<6} {'src':<8} {'created_at':<28} {'error':<40} {'question'}")
    print("-" * 120)
    for idx, row_src, question_gz, error, created_at in rows:
        question = gzip.decompress(bytes(question_gz)).decode("utf-8")
        if len(question) > 40:
            question = question[:37] + "..."
        if isinstance(error, str):
            try:
                error = json.loads(error)
            except json.JSONDecodeError:
                pass
        error_str = error.get("error", str(error)) if isinstance(error, dict) else str(error)
        if len(error_str) > 38:
            error_str = error_str[:35] + "..."
        print(f"{idx:<6} {row_src:<8} {str(created_at):<28} {error_str:<40} {question}")


if __name__ == "__main__":
    main()

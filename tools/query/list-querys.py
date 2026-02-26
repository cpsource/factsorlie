#!/usr/bin/env python3
"""List recent rows from the querys table."""

import argparse
import gzip
import os
import sys

from dotenv import load_dotenv
import psycopg2


def main():
    load_dotenv(os.path.expanduser("~/.env"))

    parser = argparse.ArgumentParser(description="List recent rows from the querys table")
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
                "SELECT idx, row_src, question_gz, hit_count, created_at FROM querys ORDER BY idx DESC LIMIT %s",
                (args.limit,),
            )
            rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No rows found.")
        return

    print(f"{'idx':<6} {'src':<8} {'hits':<6} {'created_at':<28} {'question'}")
    print("-" * 86)
    for idx, row_src, question_gz, hit_count, created_at in rows:
        question = gzip.decompress(bytes(question_gz)).decode("utf-8")
        # Truncate long questions for display
        if len(question) > 60:
            question = question[:57] + "..."
        print(f"{idx:<6} {row_src:<8} {hit_count:<6} {str(created_at):<28} {question}")


if __name__ == "__main__":
    main()

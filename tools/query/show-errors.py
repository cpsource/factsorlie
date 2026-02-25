#!/usr/bin/env python3
"""Fetch and display a row from the errors table by idx."""

import argparse
import gzip
import json
import os
import sys

from dotenv import load_dotenv
import psycopg2


def main():
    load_dotenv(os.path.expanduser("~/.env"))

    parser = argparse.ArgumentParser(description="Display a row from the errors table")
    parser.add_argument("--idx", type=int, required=True, help="Row index to fetch")
    args = parser.parse_args()

    url = os.environ.get("NEON_DATABASE_URL")
    if not url:
        print("Error: NEON_DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(url, sslmode="require")
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT idx, row_src, question_gz, error, created_at FROM errors WHERE idx = %s",
                (args.idx,),
            )
            row = cur.fetchone()
    conn.close()

    if not row:
        print(f"No row found with idx={args.idx}")
        sys.exit(1)

    idx, row_src, question_gz, error, created_at = row
    question = gzip.decompress(bytes(question_gz)).decode("utf-8")

    print(f"idx:        {idx}")
    print(f"row_src:    {row_src}")
    print(f"created_at: {created_at}")
    print(f"question:   {question}")
    print()
    if isinstance(error, str):
        try:
            error = json.loads(error)
        except json.JSONDecodeError:
            pass
    print("error:")
    print(json.dumps(error, indent=2))


if __name__ == "__main__":
    main()

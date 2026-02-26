#!/usr/bin/env python3
"""Fetch and display a row from the querys table by idx."""

import argparse
import gzip
import json
import os
import sys

from dotenv import load_dotenv
import psycopg2


def main():
    load_dotenv(os.path.expanduser("~/.env"))

    parser = argparse.ArgumentParser(description="Display a row from the querys table")
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
                "SELECT idx, row_src, question_gz, response_gz, hit_count, source_url, created_at FROM querys WHERE idx = %s",
                (args.idx,),
            )
            row = cur.fetchone()
    conn.close()

    if not row:
        print(f"No row found with idx={args.idx}")
        sys.exit(1)

    idx, row_src, question_gz, response_gz, hit_count, source_url, created_at = row
    question = gzip.decompress(bytes(question_gz)).decode("utf-8")
    response = gzip.decompress(bytes(response_gz)).decode("utf-8")

    print(f"idx:        {idx}")
    print(f"row_src:    {row_src}")
    print(f"hit_count:  {hit_count}")
    print(f"source_url: {source_url or '(none)'}")
    print(f"created_at: {created_at}")
    print(f"question:   {question}")
    print()
    try:
        parsed = json.loads(response)
        print("response:")
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(f"response:   {response}")


if __name__ == "__main__":
    main()

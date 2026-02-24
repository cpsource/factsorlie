import gzip
import os

import psycopg2


def get_conn():
    """Return a psycopg2 connection using NEON_DATABASE_URL, or None if not configured."""
    url = os.environ.get("NEON_DATABASE_URL")
    if not url:
        return None
    return psycopg2.connect(url, sslmode="require")


def log_query(row_src, question, response):
    """Gzip-compress question and response, then insert into the querys table.

    Silently catches all errors so logging never breaks the main flow.
    """
    try:
        conn = get_conn()
        if conn is None:
            return
        question_gz = gzip.compress(question.encode("utf-8"))
        response_gz = gzip.compress(response.encode("utf-8"))
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO querys (row_src, question_gz, response_gz) VALUES (%s, %s, %s)",
                    (row_src, question_gz, response_gz),
                )
        conn.close()
    except Exception:
        pass

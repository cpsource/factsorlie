import gzip
import json
import os

import psycopg2


def get_conn():
    """Return a psycopg2 connection using NEON_DATABASE_URL, or None if not configured."""
    url = os.environ.get("NEON_DATABASE_URL")
    if not url:
        return None
    return psycopg2.connect(url, sslmode="require")


def lookup_query(question, source_url=None):
    """Look up a cached response by gzip-compressed question.

    Returns the decompressed response string if found, or None.
    Increments hit_count on a match and updates source_url if provided.
    Silently returns None on any error.
    """
    try:
        conn = get_conn()
        if conn is None:
            return None
        question_gz = gzip.compress(question.encode("utf-8"), mtime=0)
        with conn:
            with conn.cursor() as cur:
                if source_url:
                    cur.execute(
                        "UPDATE querys SET hit_count = hit_count + 1, "
                        "source_url = COALESCE(source_url, %s) "
                        "WHERE question_gz = %s "
                        "RETURNING response_gz",
                        (source_url, question_gz),
                    )
                else:
                    cur.execute(
                        "UPDATE querys SET hit_count = hit_count + 1 "
                        "WHERE question_gz = %s "
                        "RETURNING response_gz",
                        (question_gz,),
                    )
                row = cur.fetchone()
        conn.close()
        if row:
            return gzip.decompress(bytes(row[0])).decode("utf-8")
        return None
    except Exception:
        return None


def log_query(row_src, question, response, source_url=None, expanded_prompt=None):
    """Gzip-compress question and response, then insert into the querys table.

    Silently catches all errors so logging never breaks the main flow.
    """
    try:
        conn = get_conn()
        if conn is None:
            return
        question_gz = gzip.compress(question.encode("utf-8"), mtime=0)
        response_gz = gzip.compress(response.encode("utf-8"), mtime=0)
        expanded_prompt_gz = None
        if expanded_prompt:
            expanded_prompt_gz = gzip.compress(expanded_prompt.encode("utf-8"), mtime=0)
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO querys (row_src, question_gz, response_gz, source_url, expanded_prompt_gz) VALUES (%s, %s, %s, %s, %s)",
                    (row_src, question_gz, response_gz, source_url, expanded_prompt_gz),
                )
        conn.close()
    except Exception:
        pass


def log_error(row_src, question, error_msg):
    """Log an API error to the errors table.

    Silently catches all errors so logging never breaks the main flow.
    """
    try:
        conn = get_conn()
        if conn is None:
            return
        question_gz = gzip.compress(question.encode("utf-8"), mtime=0)
        error_json = json.dumps({"error": error_msg})
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO errors (row_src, question_gz, error) VALUES (%s, %s, %s)",
                    (row_src, question_gz, error_json),
                )
        conn.close()
    except Exception:
        pass

import gzip
import json
from unittest import mock

import pytest

from db import get_conn, log_query


class TestGetConn:
    def test_returns_none_when_env_not_set(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            assert get_conn() is None

    @mock.patch("db.psycopg2.connect")
    def test_returns_connection_when_env_set(self, mock_connect):
        mock_connect.return_value = mock.MagicMock()
        with mock.patch.dict("os.environ", {"NEON_DATABASE_URL": "postgres://localhost/test"}):
            conn = get_conn()
            assert conn is not None
            mock_connect.assert_called_once_with("postgres://localhost/test", sslmode="require")


class TestLogQuery:
    @mock.patch("db.get_conn")
    def test_inserts_gzipped_data(self, mock_get_conn):
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_conn.cursor.return_value.__enter__ = mock.Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)
        mock_conn.__enter__ = mock.Mock(return_value=mock_conn)
        mock_conn.__exit__ = mock.Mock(return_value=False)
        mock_get_conn.return_value = mock_conn

        log_query("submit", "Is the earth flat?", json.dumps({"verdict": "FALSE"}))

        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args
        sql = args[0][0]
        params = args[0][1]

        assert "INSERT INTO querys" in sql
        assert params[0] == "submit"
        # Verify the data is gzip-compressed
        assert gzip.decompress(params[1]) == b"Is the earth flat?"
        assert json.loads(gzip.decompress(params[2])) == {"verdict": "FALSE"}

    @mock.patch("db.get_conn")
    def test_silent_on_db_not_configured(self, mock_get_conn):
        mock_get_conn.return_value = None
        # Should not raise
        log_query("query", "test question", "test response")

    @mock.patch("db.get_conn")
    def test_silent_on_db_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("connection refused")
        # Should not raise
        log_query("submit", "test", "test")

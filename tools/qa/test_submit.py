import pytest
from unittest.mock import patch, MagicMock
import requests
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


MOCK_ANTHROPIC_RESPONSE = {
    "content": [
        {
            "type": "text",
            "text": '{"verdict":"FALSE","confidence":"high","summary":"The Earth is not flat.","red_flags":["pseudoscience"]}',
        }
    ]
}


def test_submit_get(client):
    response = client.get("/submit")
    assert response.status_code == 200
    assert b"Your statement" in response.data


def test_submit_empty_statement(client):
    response = client.post("/submit", data={"statement": ""})
    assert response.status_code == 200
    assert b"Please enter a statement" in response.data


@patch("app.http_requests.post")
@patch("app.r")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_submit_analyzes_statement(mock_redis, mock_post, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = MOCK_ANTHROPIC_RESPONSE
    mock_post.return_value = mock_resp

    response = client.post("/submit", data={"statement": "The earth is flat"})
    assert response.status_code == 200
    assert b"FALSE" in response.data
    assert b"high confidence" in response.data
    assert b"The Earth is not flat." in response.data
    assert b"pseudoscience" in response.data

    # Verify statement was stored in Redis
    mock_redis.lpush.assert_called_once()
    args = mock_redis.lpush.call_args[0]
    assert args[0] == "submissions"
    assert "The earth is flat" in args[1]

    # Verify Anthropic was called with the statement
    call_kwargs = mock_post.call_args
    body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
    user_msg = body["messages"][0]["content"]
    assert "The earth is flat" in user_msg


@patch("app.http_requests.post")
@patch("app.r")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_submit_shows_error_on_api_failure(mock_redis, mock_post, client):
    mock_post.side_effect = requests.RequestException("Connection refused")

    response = client.post("/submit", data={"statement": "The earth is flat"})
    assert response.status_code == 200
    assert b"Analysis error" in response.data

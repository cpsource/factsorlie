import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_query_missing_title(client):
    response = client.post("/query", json={})
    assert response.status_code == 400
    assert "title" in response.get_json()["error"]


def test_query_no_body(client):
    response = client.post("/query", content_type="application/json", data="")
    assert response.status_code == 400


MOCK_ANTHROPIC_RESPONSE = {
    "content": [
        {
            "type": "text",
            "text": '{"verdict":"CLICKBAIT","confidence":"high","summary":"Exaggerated headline.","red_flags":["sensationalism"]}',
        }
    ]
}


@patch("app.http_requests.post")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_query_returns_verdict_without_meta(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = MOCK_ANTHROPIC_RESPONSE
    mock_post.return_value = mock_resp

    response = client.post("/query", json={"title": "SHOCKING: Scientists DESTROY Everything We Know!"})
    assert response.status_code == 200

    data = response.get_json()
    assert data["verdict"] == "CLICKBAIT"
    assert data["confidence"] == "high"
    assert "summary" in data
    assert "red_flags" in data

    # Verify the request to Anthropic does NOT include metadata context
    call_kwargs = mock_post.call_args
    body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
    user_msg = body["messages"][0]["content"]
    assert "Additional context" not in user_msg
    assert "SHOCKING: Scientists DESTROY Everything We Know!" in user_msg


@patch("app.http_requests.post")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_query_with_video_meta(mock_post, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = MOCK_ANTHROPIC_RESPONSE
    mock_post.return_value = mock_resp

    response = client.post("/query", json={
        "title": "Water Found on Mars",
        "videoMeta": {
            "uploadDate": "2025-01-01",
            "viewCount": "1000000",
            "description": "NASA confirms water on Mars"
        }
    })
    assert response.status_code == 200

    # Verify the user content sent to Anthropic includes metadata
    call_kwargs = mock_post.call_args
    body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
    user_msg = body["messages"][0]["content"]
    assert "Additional context" in user_msg
    assert "NASA confirms water on Mars" in user_msg


@patch.dict("os.environ", {}, clear=False)
def test_query_no_api_key(client):
    # Remove ANTHROPIC_API_KEY if present
    import os
    os.environ.pop("ANTHROPIC_API_KEY", None)

    response = client.post("/query", json={"title": "Some title here for testing"})
    assert response.status_code == 500
    assert "not configured" in response.get_json()["error"]

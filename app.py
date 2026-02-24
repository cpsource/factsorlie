import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
import redis
import requests as http_requests
import markdown
from turnstile import verify_turnstile
from db import log_query

app = Flask(__name__)

r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
)


@app.route("/")
def index():
    r.incr("hits")
    count = r.get("hits").decode("utf-8")
    readme_html = ""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    try:
        with open(readme_path, "r") as f:
            readme_html = markdown.markdown(f.read(), extensions=["tables", "fenced_code"])
    except FileNotFoundError:
        pass
    return render_template("index.html", count=count, readme_html=readme_html)


def is_rate_limited(ip, endpoint="default", limit=3, window=60):
    """Check if IP has exceeded limit requests within window seconds."""
    key = f"ratelimit:{endpoint}:{ip}"
    count = r.get(key)
    if count and int(count) >= limit:
        return True
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    pipe.execute()
    return False


@app.route("/submit", methods=["GET", "POST"])
def submit():
    message = None
    analysis = None
    turnstile_site_key = os.environ.get("CLOUDFLARE_TURNSTYLE_SITE_KEY")
    if request.method == "POST":
        turnstile_token = request.form.get("cf-turnstile-response")
        if not verify_turnstile(turnstile_token, request.remote_addr):
            message = "Bot verification failed. Please try again."
            return render_template("submit.html", message=message, analysis=analysis, turnstile_site_key=turnstile_site_key)
        if is_rate_limited(request.remote_addr, endpoint="submit", limit=3):
            message = "Rate limit exceeded. Please wait a minute before trying again."
            return render_template("submit.html", message=message, analysis=analysis, turnstile_site_key=turnstile_site_key)
        statement = request.form.get("statement", "").strip()
        if statement:
            r.lpush("submissions", json.dumps({"statement": statement}))
            result, error = analyze_statement(statement)
            if error:
                analysis = {"error": error}
            else:
                analysis = result
                log_query("submit", statement, json.dumps(analysis))
        else:
            message = "Please enter a statement."
    return render_template("submit.html", message=message, analysis=analysis, turnstile_site_key=turnstile_site_key)


@app.route("/health")
def health():
    return {"status": "ok"}


SYSTEM_PROMPT = """You are a headline truth-checker. Given a YouTube video title, assess whether the claim in the headline is likely TRUE, FALSE, MISLEADING, CLICKBAIT, or OPINION.

Respond in this exact JSON format and nothing else:
{
  "verdict": "TRUE" | "FALSE" | "MISLEADING" | "CLICKBAIT" | "OPINION" | "UNVERIFIABLE",
  "confidence": "high" | "medium" | "low",
  "summary": "1-2 sentence explanation of your assessment",
  "red_flags": ["list", "of", "red", "flags", "if any"]
}

Guidelines:
- CLICKBAIT: headline uses exaggerated language ("DESTROYS", "EXPLOSIVE", "ALL-OUT WAR") to dramatize mundane events
- MISLEADING: contains a kernel of truth but frames it deceptively
- FALSE: the core claim is factually wrong
- TRUE: the core claim is factually accurate
- OPINION: the headline is expressing a subjective view, not a factual claim
- UNVERIFIABLE: cannot determine truth from the headline alone

Focus on the literal claim. Flag emotional manipulation language. Be concise."""


def analyze_statement(title, video_meta=None):
    """Call Anthropic API to analyze a statement/title. Returns (result_dict, error_string)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "Server API key not configured"

    if video_meta:
        user_content = (
            f'Analyze this YouTube video title:\n\n"{title}"\n\n'
            f"Additional context:\n"
            f"Upload date: {video_meta.get('uploadDate', '')}\n"
            f"Views: {video_meta.get('viewCount', '')}\n"
            f"Description: {video_meta.get('description', '')}"
        )
    else:
        user_content = f'Analyze this YouTube video title:\n\n"{title}"'

    try:
        resp = http_requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 500,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_content}],
            },
            timeout=30,
        )
        resp.raise_for_status()
    except http_requests.RequestException as e:
        return None, f"Anthropic API error: {e}"

    api_data = resp.json()
    text = "".join(
        b["text"] for b in api_data.get("content", []) if b.get("type") == "text"
    )

    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        return None, "Failed to parse API response"

    return result, None


@app.route("/query", methods=["POST"])
def query():
    if is_rate_limited(request.remote_addr, endpoint="query", limit=12):
        return jsonify({"error": "Rate limit exceeded. Please wait a minute."}), 429

    data = request.get_json(silent=True)
    if not data or not data.get("title"):
        return jsonify({"error": "Missing required field: title"}), 400

    result, error = analyze_statement(data["title"], data.get("videoMeta"))
    if error:
        status = 500 if "not configured" in error else 502
        return jsonify({"error": error}), status

    log_query("query", data["title"], json.dumps(result))
    return jsonify(result)

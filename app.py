import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
import redis
import requests as http_requests

app = Flask(__name__)

r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
)


@app.route("/")
def index():
    r.incr("hits")
    count = r.get("hits").decode("utf-8")
    return render_template("index.html", count=count)


@app.route("/submit", methods=["GET", "POST"])
def submit():
    message = None
    if request.method == "POST":
        statement = request.form.get("statement", "").strip()
        category = request.form.get("category", "").strip()
        if statement and category in ("fact", "lie"):
            entry = json.dumps({"statement": statement, "category": category})
            r.lpush("submissions", entry)
            message = "Your submission has been recorded!"
        else:
            message = "Please fill in all fields."
    return render_template("submit.html", message=message)


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


@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(silent=True)
    if not data or not data.get("title"):
        return jsonify({"error": "Missing required field: title"}), 400

    title = data["title"]
    video_meta = data.get("videoMeta")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "Server API key not configured"}), 500

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
        return jsonify({"error": f"Anthropic API error: {e}"}), 502

    api_data = resp.json()
    text = "".join(
        b["text"] for b in api_data.get("content", []) if b.get("type") == "text"
    )

    # Strip markdown fences if present
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse API response"}), 502

    return jsonify(result)

import os
import json
from flask import Flask, render_template, request, redirect, url_for
import redis

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

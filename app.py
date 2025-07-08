from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

app = Flask(__name__)

# I use config for DB path, because I override it in tests
app.config["DB_NAME"] = "reviews.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(app.config["DB_NAME"])
    return conn


def init_db() -> None:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# Keywords for basic sentiment analysis
POSITIVE_WORDS: List[str] = ["хорош", "люблю", "отлично", "нрави", "прекрасно"]
NEGATIVE_WORDS: List[str] = ["плохо", "ненавиж", "ужасно", "отстой", "не работает"]


def get_sentiment(text: str) -> str:
    lower_text: str = text.lower()
    if any(word in lower_text for word in POSITIVE_WORDS):
        return "positive"
    elif any(word in lower_text for word in NEGATIVE_WORDS):
        return "negative"
    else:
        return "neutral"


@app.route("/reviews", methods=["POST"])
def create_review() -> Any:
    data: Dict[str, Any] = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    text: str = data.get("text", "")
    sentiment: str = get_sentiment(text)
    created_at: str = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
        (text, sentiment, created_at),
    )
    conn.commit()
    review_id: int = c.lastrowid
    conn.close()

    return jsonify(
        {
            "id": review_id,
            "text": text,
            "sentiment": sentiment,
            "created_at": created_at,
        }
    ), 201


@app.route("/reviews", methods=["GET"])
def get_reviews() -> Any:
    sentiment_filter: Optional[str] = request.args.get("sentiment")

    conn = get_db_connection()
    c = conn.cursor()

    if sentiment_filter:
        c.execute(
            "SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?",
            (sentiment_filter,),
        )
    else:
        c.execute("SELECT id, text, sentiment, created_at FROM reviews")

    rows = c.fetchall()
    conn.close()

    reviews: List[Dict[str, Any]] = [
        {"id": row[0], "text": row[1], "sentiment": row[2], "created_at": row[3]}
        for row in rows
    ]
    return jsonify(reviews)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

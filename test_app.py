import pytest
import tempfile
import os
import json
from app import app, init_db


@pytest.fixture
def client():
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()

    # Override the app config to use the temp DB
    app.config["DB_NAME"] = db_path
    app.config["TESTING"] = True

    # Initialize fresh DB schema
    init_db()

    with app.test_client() as client:
        yield client

    # Cleanup: close and remove temp DB file
    os.close(db_fd)
    os.unlink(db_path)


def test_create_review(client):
    # Test POST /reviews with a positive review
    response = client.post(
        "/reviews",
        data=json.dumps({"text": "Я люблю этот продукт"}),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["text"] == "Я люблю этот продукт"
    assert data["sentiment"] == "positive"
    assert "created_at" in data
    assert isinstance(data["id"], int)


def test_get_reviews_no_filter(client):
    # Insert two reviews (one positive, one negative)
    client.post("/reviews", json={"text": "Это хорошо"})
    client.post("/reviews", json={"text": "Это плохо"})

    # Test GET /reviews without sentiment filter returns both
    response = client.get("/reviews")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    sentiments = {review["sentiment"] for review in data}
    assert sentiments == {"positive", "negative"}


def test_get_reviews_with_filter(client):
    # Insert three reviews with different sentiments
    client.post("/reviews", json={"text": "Это отлично"})
    client.post("/reviews", json={"text": "Это ужасно"})
    client.post("/reviews", json={"text": "Это нормально"})

    # Test GET /reviews with sentiment filter = "positive"
    response = client.get("/reviews?sentiment=positive")
    assert response.status_code == 200
    data = response.get_json()
    assert all(review["sentiment"] == "positive" for review in data)

    # Test GET /reviews with sentiment filter = "neutral"
    response = client.get("/reviews?sentiment=neutral")
    assert response.status_code == 200
    data = response.get_json()
    assert all(review["sentiment"] == "neutral" for review in data)


def test_create_review_missing_text(client):
    # POST /reviews with empty body or missing 'text' should return 400
    response = client.post("/reviews", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

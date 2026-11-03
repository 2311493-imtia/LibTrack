"""
Automated tests for the LibTrack Book Management API.

These tests use an in-memory SQLite database (TESTING=1), which is allowed
for automated testing only. They never touch real Supabase data.
"""

import os

# Must be set BEFORE importing main so the app uses the in-memory test DB.
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from main import app, Base, engine

# A valid book payload used by many tests.
VALID_BOOK = {
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "isbn": "9780743273563",
    "category": "Fiction",
    "publisher": "Scribner",
    "published_year": 1925,
    "total_copies": 5,
    "available_copies": 5,
    "description": "A classic novel about the American Dream",
}


@pytest.fixture()
def client():
    """Fresh database + test client for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health and Hello (existing endpoints must keep working)
# ---------------------------------------------------------------------------
def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_hello(client):
    res = client.get("/api/hello", params={"name": "Nisha"})
    assert res.status_code == 200
    assert res.json() == {"message": "Hello, Nisha!"}


# ---------------------------------------------------------------------------
# Create Book
# ---------------------------------------------------------------------------
def test_create_book(client):
    res = client.post("/api/books", json=VALID_BOOK)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] == 1
    assert data["title"] == VALID_BOOK["title"]
    assert data["available_copies"] == VALID_BOOK["available_copies"]
    assert data["created_at"]


def test_create_book_available_defaults_to_total(client):
    payload = {k: v for k, v in VALID_BOOK.items() if k != "available_copies"}
    res = client.post("/api/books", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["available_copies"] == data["total_copies"] == 5


def test_create_book_duplicate_isbn_conflict(client):
    client.post("/api/books", json=VALID_BOOK)
    res = client.post("/api/books", json=VALID_BOOK)
    assert res.status_code == 409
    assert "ISBN" in res.json()["detail"]


def test_create_book_missing_required_field_422(client):
    payload = {k: v for k, v in VALID_BOOK.items() if k != "title"}
    res = client.post("/api/books", json=payload)
    assert res.status_code == 422


def test_create_book_zero_total_copies_422(client):
    payload = {**VALID_BOOK, "total_copies": 0}
    res = client.post("/api/books", json=payload)
    assert res.status_code == 422


def test_create_book_available_exceeds_total_422(client):
    payload = {**VALID_BOOK, "available_copies": 10}
    res = client.post("/api/books", json=payload)
    assert res.status_code == 422


def test_create_book_invalid_year_422(client):
    payload = {**VALID_BOOK, "published_year": 999}
    res = client.post("/api/books", json=payload)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Read All Books / search / filter
# ---------------------------------------------------------------------------
def test_list_books_empty(client):
    res = client.get("/api/books")
    assert res.status_code == 200
    assert res.json() == []


def test_list_books(client):
    client.post("/api/books", json=VALID_BOOK)
    client.post("/api/books", json={**VALID_BOOK, "isbn": "9780061120084",
                                   "title": "To Kill a Mockingbird",
                                   "author": "Harper Lee"})
    res = client.get("/api/books")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_search_by_title(client):
    client.post("/api/books", json=VALID_BOOK)
    client.post("/api/books", json={**VALID_BOOK, "isbn": "9780061120084",
                                   "title": "To Kill a Mockingbird"})
    res = client.get("/api/books", params={"search": "Mockingbird"})
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "To Kill a Mockingbird"


def test_search_by_author(client):
    client.post("/api/books", json=VALID_BOOK)
    res = client.get("/api/books", params={"search": "Scott"})
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_search_by_isbn(client):
    client.post("/api/books", json=VALID_BOOK)
    res = client.get("/api/books", params={"search": "9780743273563"})
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_filter_by_category(client):
    client.post("/api/books", json=VALID_BOOK)
    client.post("/api/books", json={**VALID_BOOK, "isbn": "9780061120084",
                                   "title": "Clean Code", "category": "Technology"})
    res = client.get("/api/books", params={"category": "Technology"})
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["category"] == "Technology"


# ---------------------------------------------------------------------------
# Read Single Book
# ---------------------------------------------------------------------------
def test_read_single_book(client):
    created = client.post("/api/books", json=VALID_BOOK).json()
    res = client.get(f"/api/books/{created['id']}")
    assert res.status_code == 200
    assert res.json()["title"] == VALID_BOOK["title"]


def test_read_missing_book_404(client):
    res = client.get("/api/books/999")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Update Book
# ---------------------------------------------------------------------------
def test_update_book(client):
    created = client.post("/api/books", json=VALID_BOOK).json()
    res = client.put(
        f"/api/books/{created['id']}",
        json={"title": "The Great Gatsby (Revised)", "available_copies": 3},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "The Great Gatsby (Revised)"
    assert data["available_copies"] == 3


def test_update_missing_book_404(client):
    res = client.put("/api/books/999", json={"title": "X"})
    assert res.status_code == 404


def test_update_available_exceeds_total_422(client):
    created = client.post("/api/books", json=VALID_BOOK).json()
    res = client.put(f"/api/books/{created['id']}", json={"available_copies": 50})
    assert res.status_code == 422


def test_update_duplicate_isbn_conflict(client):
    client.post("/api/books", json=VALID_BOOK)
    other = client.post("/api/books", json={**VALID_BOOK, "isbn": "9780061120084"}).json()
    res = client.put(f"/api/books/{other['id']}", json={"isbn": VALID_BOOK["isbn"]})
    assert res.status_code == 409


# ---------------------------------------------------------------------------
# Delete Book
# ---------------------------------------------------------------------------
def test_delete_book(client):
    created = client.post("/api/books", json=VALID_BOOK).json()
    res = client.delete(f"/api/books/{created['id']}")
    assert res.status_code == 204
    # Verify it is gone.
    res = client.get(f"/api/books/{created['id']}")
    assert res.status_code == 404


def test_delete_missing_book_404(client):
    res = client.delete("/api/books/999")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Dashboard Statistics
# ---------------------------------------------------------------------------
def test_stats_empty(client):
    res = client.get("/api/books/stats")
    assert res.status_code == 200
    assert res.json() == {
        "total_titles": 0,
        "total_copies": 0,
        "available_copies": 0,
        "unavailable_copies": 0,
    }


def test_stats_with_books(client):
    client.post("/api/books", json=VALID_BOOK)
    client.post("/api/books", json={**VALID_BOOK, "isbn": "9780061120084",
                                   "title": "Clean Code", "category": "Technology",
                                   "total_copies": 4, "available_copies": 1})
    res = client.get("/api/books/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_titles"] == 2
    assert data["total_copies"] == 9
    assert data["available_copies"] == 6
    assert data["unavailable_copies"] == 3

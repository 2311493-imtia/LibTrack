from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
from fastapi.exceptions import RequestValidationError
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

import os
from datetime import datetime
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment / Database configuration
# ---------------------------------------------------------------------------
# Load variables from backend/.env (never committed to Git).
# The .env file must contain:
#   DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@db.xxxx.supabase.com:6543/postgres
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TESTING = os.getenv("TESTING") == "1"

if DATABASE_URL:
    # Real database (Supabase PostgreSQL via Session Pooler).
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
elif TESTING:
    # SQLite in-memory is allowed ONLY for the automated test suite.
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
else:
    raise RuntimeError(
        "DATABASE_URL is not set. Create a backend/.env file with your Supabase "
        "Session Pooler connection string, e.g.:\n"
        "  DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@db.xxxx.supabase.com:6543/postgres"
    )

# Engine creation
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if ":memory:" in SQLALCHEMY_DATABASE_URL:
        # In-memory SQLite: a single shared connection so all sessions see the same DB.
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args=connect_args,
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args=connect_args,
            echo=False,
        )
else:
    # PostgreSQL / Supabase: connection pooling + pre-ping for reliability.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# SQLAlchemy Model
# ---------------------------------------------------------------------------
class Book(Base):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("isbn", name="uq_books_isbn"),)

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=False)
    isbn = Column(String(13), nullable=False)
    category = Column(String(50), nullable=False)
    publisher = Column(String(100), nullable=True)
    published_year = Column(Integer, nullable=True)
    total_copies = Column(Integer, nullable=False)
    available_copies = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Book title")
    author: str = Field(..., min_length=1, description="Book author")
    isbn: str = Field(..., min_length=1, description="ISBN (13 characters)")
    category: str = Field(..., min_length=1, description="Book category")
    publisher: str = Field(default=None, max_length=100, description="Publisher")
    published_year: int = Field(default=None, ge=1000, le=2100, description="Published year")
    total_copies: int = Field(..., gt=0, description="Total number of copies")
    available_copies: int | None = Field(
        default=None, ge=0,
        description="Available copies (defaults to total_copies)"
    )
    description: str = Field(default=None, max_length=500, description="Book description")

    model_config = ConfigDict(extra="forbid")

    @field_validator("published_year")
    @classmethod
    def validate_published_year(cls, v):
        if v is not None and (v < 1000 or v > 2100):
            raise ValueError("Published year must be between 1000 and 2100")
        return v


class BookUpdate(BaseModel):
    title: str = Field(default=None, min_length=1, description="Book title")
    author: str = Field(default=None, min_length=1, description="Book author")
    isbn: str = Field(default=None, min_length=1, description="ISBN (13 characters)")
    category: str = Field(default=None, min_length=1, description="Book category")
    publisher: str = Field(default=None, max_length=100, description="Publisher")
    published_year: int = Field(default=None, ge=1000, le=2100, description="Published year")
    total_copies: int = Field(default=None, gt=0, description="Total number of copies")
    available_copies: int = Field(
        default=None, ge=0,
        description="Available copies"
    )
    description: str = Field(default=None, max_length=500, description="Book description")


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    category: str
    publisher: str = ""
    published_year: int = 0
    total_copies: int
    available_copies: int
    description: str = ""
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# FastAPI App setup
# ---------------------------------------------------------------------------
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they do not exist yet.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="LibTrack – Book Management",
    description="Library Management System – Midterm MVP",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Dependency: Get DB session
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()},
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request, exc):
    # Catch duplicate ISBN etc.
    return JSONResponse(
        status_code=409,
        content={"detail": "Conflict – likely duplicate ISBN"},
    )


# ---------------------------------------------------------------------------
# CRUD – Create Book
# ---------------------------------------------------------------------------
@app.post("/api/books", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    """Create a new book in the database."""
    # If available_copies not provided in the schema, it defaults to total_copies via Pydantic
    available = book.available_copies if book.available_copies is not None else book.total_copies

    # Validate: available copies cannot exceed total copies
    if available > book.total_copies:
        raise HTTPException(
            status_code=422,
            detail="Available copies cannot exceed total copies",
        )

    db_book = Book(
        title=book.title.strip(),
        author=book.author.strip(),
        isbn=book.isbn.strip(),
        category=book.category.strip(),
        publisher=book.publisher.strip() if book.publisher else None,
        published_year=book.published_year,
        total_copies=book.total_copies,
        available_copies=available,
        description=book.description.strip() if book.description else None,
    )

    try:
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        return db_book
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A book with this ISBN already exists",
        )


# ---------------------------------------------------------------------------
# CRUD – Read All Books (with search and filtering)
# ---------------------------------------------------------------------------
@app.get("/api/books", response_model=list[BookResponse])
def read_books(
    search: str = "",
    category: str = "",
    db: Session = Depends(get_db),
):
    """Retrieve all books, with optional search and category filtering."""
    query = db.query(Book)

    if search:
        query = query.filter(
            (Book.title.ilike(f"%{search}%"))
            | (Book.author.ilike(f"%{search}%"))
            | (Book.isbn.ilike(f"%{search}%"))
        )

    if category:
        query = query.filter(Book.category.ilike(f"%{category}%"))

    books = query.order_by(Book.created_at.desc()).all()
    return books


# ---------------------------------------------------------------------------
# Dashboard Statistics
# (Defined BEFORE /api/books/{book_id} so "stats" is not treated as an id.)
# ---------------------------------------------------------------------------
@app.get("/api/books/stats", response_model=dict)
def get_stats(db: Session = Depends(get_db)):
    """Return dashboard statistics calculated from actual database records."""
    total_titles = db.query(Book).count()
    total_copies_result = db.query(Book.total_copies).all()
    available_copies_result = db.query(Book.available_copies).all()

    total_copies_sum = sum((c[0] or 0) for c in total_copies_result)
    total_available = sum((a[0] or 0) for a in available_copies_result)
    total_unavailable = total_copies_sum - total_available

    return {
        "total_titles": total_titles,
        "total_copies": total_copies_sum,
        "available_copies": total_available,
        "unavailable_copies": total_unavailable,
    }


# ---------------------------------------------------------------------------
# CRUD – Read Single Book
# ---------------------------------------------------------------------------
@app.get("/api/books/{book_id}", response_model=BookResponse)
def read_book(book_id: int, db: Session = Depends(get_db)):
    """Retrieve one specific book by ID."""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book


# ---------------------------------------------------------------------------
# CRUD – Update Book
# ---------------------------------------------------------------------------
@app.put("/api/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
    """Update an existing book."""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Apply updates only for fields that are provided (not None)
    update_data = book.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(db_book, key, value)

    # If available_copies is being set explicitly, validate it
    if "available_copies" in update_data and db_book.total_copies is not None:
        if update_data["available_copies"] > db_book.total_copies:
            raise HTTPException(
                status_code=422,
                detail="Available copies cannot exceed total copies",
            )

    try:
        db.commit()
        db.refresh(db_book)
        return db_book
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A book with this ISBN already exists")


# ---------------------------------------------------------------------------
# CRUD – Delete Book
# ---------------------------------------------------------------------------
@app.delete("/api/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book by ID."""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(db_book)
    db.commit()
    return JSONResponse(status_code=204, content={})


# ---------------------------------------------------------------------------
# Health check (preserve existing endpoint)
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=dict)
def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Hello endpoint (preserve existing endpoint)
# ---------------------------------------------------------------------------
@app.get("/api/hello", response_model=dict)
def hello(name: str = "World") -> dict:
    return {"message": f"Hello, {name}!"}
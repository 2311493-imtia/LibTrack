// BookList: professional table of all books with search, category filter,
// loading/empty/error states, refresh, and View / Edit / Delete actions.

import { useCallback, useEffect, useState } from "react"
import { fetchBooks, deleteBook } from "../api"
import type { Book } from "../types"

interface Props {
  refreshKey: number // bump to reload the list after CRUD operations
  onView: (book: Book) => void
  onEdit: (book: Book) => void
  notify: (message: string, type: "success" | "error") => void
}

export default function BookList({ refreshKey, onView, onEdit, notify }: Props) {
  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")
  const [category, setCategory] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const data = await fetchBooks(search, category)
      setBooks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load books")
    } finally {
      setLoading(false)
    }
  }, [search, category])

  useEffect(() => {
    load()
  }, [load, refreshKey])

  // Categories come from the books currently returned by the backend.
  const categories = Array.from(new Set(books.map((b) => b.category))).sort()

  async function handleDelete(book: Book) {
    const confirmed = window.confirm(
      `Delete "${book.title}"? This cannot be undone.`,
    )
    if (!confirmed) return
    try {
      await deleteBook(book.id)
      notify(`Deleted "${book.title}".`, "success")
      load()
    } catch (err) {
      notify(err instanceof Error ? err.message : "Delete failed", "error")
    }
  }

  return (
    <div className="book-list">
      <div className="toolbar">
        <input
          className="search-input"
          placeholder="Search by title, author or ISBN…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="filter-select"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <button className="btn btn-secondary" onClick={load} title="Refresh">
          ↻ Refresh
        </button>
      </div>

      {loading && <div className="loading-block">Loading books…</div>}
      {!loading && error && <div className="error-box">{error}</div>}
      {!loading && !error && books.length === 0 && (
        <div className="empty-state">
          <p>No books found.</p>
          <p className="muted">Try a different search, or add a new book.</p>
        </div>
      )}
      {!loading && !error && books.length > 0 && (
        <div className="table-wrap">
          <table className="book-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Author</th>
                <th>ISBN</th>
                <th>Category</th>
                <th>Publisher</th>
                <th>Year</th>
                <th>Total</th>
                <th>Available</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {books.map((book) => (
                <tr key={book.id}>
                  <td>{book.id}</td>
                  <td>
                    <button className="link-btn" onClick={() => onView(book)}>
                      {book.title}
                    </button>
                  </td>
                  <td>{book.author}</td>
                  <td>{book.isbn}</td>
                  <td>
                    <span className="badge">{book.category}</span>
                  </td>
                  <td>{book.publisher || "—"}</td>
                  <td>{book.published_year || "—"}</td>
                  <td>{book.total_copies}</td>
                  <td>
                    <span className={book.available_copies === 0 ? "copies-zero" : ""}>
                      {book.available_copies}
                    </span>
                  </td>
                  <td className="actions">
                    <button className="btn btn-sm btn-secondary" onClick={() => onView(book)}>
                      View
                    </button>
                    <button className="btn btn-sm btn-primary" onClick={() => onEdit(book)}>
                      Edit
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(book)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

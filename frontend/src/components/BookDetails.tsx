// BookDetails: shows every field of one book. The data is fetched fresh from
// the backend (GET /api/books/{id}) to demonstrate single-record retrieval.

import { useEffect, useState } from "react"
import { fetchBook } from "../api"
import type { Book } from "../types"

interface Props {
  bookId: number
  onBack: () => void
  onEdit: (book: Book) => void
}

export default function BookDetails({ bookId, onBack, onEdit }: Props) {
  const [book, setBook] = useState<Book | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let active = true
    setLoading(true)
    setError("")
    fetchBook(bookId)
      .then((data) => {
        if (active) setBook(data)
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Failed to load book")
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [bookId])

  if (loading) return <div className="loading-block">Loading book…</div>
  if (error) return <div className="error-box">{error}</div>
  if (!book) return null

  const rows = [
    ["Book ID", String(book.id)],
    ["Title", book.title],
    ["Author", book.author],
    ["ISBN", book.isbn],
    ["Category", book.category],
    ["Publisher", book.publisher || "—"],
    ["Published Year", book.published_year ? String(book.published_year) : "—"],
    ["Total Copies", String(book.total_copies)],
    ["Available Copies", String(book.available_copies)],
    ["Description", book.description || "—"],
    ["Created At", new Date(book.created_at).toLocaleString()],
  ]

  return (
    <div className="details-card">
      <div className="details-header">
        <button className="btn btn-secondary" onClick={onBack}>
          ← Back to list
        </button>
        <button className="btn btn-primary" onClick={() => onEdit(book)}>
          Edit Book
        </button>
      </div>
      <h2>{book.title}</h2>
      <p className="muted">by {book.author}</p>
      <dl className="details-grid">
        {rows.map(([label, value]) => (
          <div className="detail-item" key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

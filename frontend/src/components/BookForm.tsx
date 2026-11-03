// BookForm: used both to add a new book and to edit an existing one.
// Submits to the real backend API and reports success/error back to the parent.

import { useState, type FormEvent } from "react"
import { createBook, updateBook } from "../api"
import type { Book } from "../types"

interface Props {
  book: Book | null // null => add mode, otherwise edit mode
  onDone: (message: string) => void
}

const emptyForm = {
  title: "",
  author: "",
  isbn: "",
  category: "",
  publisher: "",
  published_year: "",
  total_copies: "",
  available_copies: "",
  description: "",
}

export default function BookForm({ book, onDone }: Props) {
  const [form, setForm] = useState(() =>
    book
      ? {
          title: book.title,
          author: book.author,
          isbn: book.isbn,
          category: book.category,
          publisher: book.publisher ?? "",
          published_year: book.published_year ? String(book.published_year) : "",
          total_copies: String(book.total_copies),
          available_copies: String(book.available_copies),
          description: book.description ?? "",
        }
      : emptyForm,
  )
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)

  function set(field: keyof typeof emptyForm, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError("")

    // ----- Client-side validation (server re-validates too) -----
    if (!form.title.trim() || !form.author.trim() || !form.isbn.trim() || !form.category.trim()) {
      setError("Title, Author, ISBN and Category are required.")
      return
    }
    const totalCopies = Number(form.total_copies)
    if (!Number.isInteger(totalCopies) || totalCopies <= 0) {
      setError("Total copies must be a whole number greater than zero.")
      return
    }
    const publishedYear = form.published_year === "" ? null : Number(form.published_year)
    if (publishedYear !== null && (!Number.isInteger(publishedYear) || publishedYear < 1000 || publishedYear > 2100)) {
      setError("Published year must be a valid year between 1000 and 2100.")
      return
    }
    let availableCopies: number | null = null
    if (form.available_copies !== "") {
      availableCopies = Number(form.available_copies)
      if (!Number.isInteger(availableCopies) || availableCopies < 0) {
        setError("Available copies must be a whole number of zero or more.")
        return
      }
      if (availableCopies > totalCopies) {
        setError("Available copies cannot exceed total copies.")
        return
      }
    }

    const payload = {
      title: form.title.trim(),
      author: form.author.trim(),
      isbn: form.isbn.trim(),
      category: form.category.trim(),
      publisher: form.publisher.trim(),
      published_year: publishedYear,
      total_copies: totalCopies,
      available_copies: availableCopies,
      description: form.description.trim(),
    }

    setSaving(true)
    try {
      if (book) {
        await updateBook(book.id, payload)
        onDone("Book updated successfully.")
      } else {
        await createBook(payload)
        onDone("Book added successfully.")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.")
      setSaving(false)
    }
  }

  return (
    <form className="book-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label>
          Title <span className="req">*</span>
          <input value={form.title} onChange={(e) => set("title", e.target.value)} required />
        </label>
        <label>
          Author <span className="req">*</span>
          <input value={form.author} onChange={(e) => set("author", e.target.value)} required />
        </label>
      </div>
      <div className="form-row">
        <label>
          ISBN <span className="req">*</span>
          <input value={form.isbn} onChange={(e) => set("isbn", e.target.value)} required />
        </label>
        <label>
          Category <span className="req">*</span>
          <input value={form.category} onChange={(e) => set("category", e.target.value)} required />
        </label>
      </div>
      <div className="form-row">
        <label>
          Publisher
          <input value={form.publisher} onChange={(e) => set("publisher", e.target.value)} />
        </label>
        <label>
          Published Year
          <input
            type="number"
            value={form.published_year}
            onChange={(e) => set("published_year", e.target.value)}
            placeholder="e.g. 1925"
          />
        </label>
      </div>
      <div className="form-row">
        <label>
          Total Copies <span className="req">*</span>
          <input
            type="number"
            value={form.total_copies}
            onChange={(e) => set("total_copies", e.target.value)}
            min="1"
            required
          />
        </label>
        <label>
          Available Copies
          <input
            type="number"
            value={form.available_copies}
            onChange={(e) => set("available_copies", e.target.value)}
            placeholder="Defaults to total copies"
            min="0"
          />
        </label>
      </div>
      <label>
        Description
        <textarea
          value={form.description}
          onChange={(e) => set("description", e.target.value)}
          rows={3}
        />
      </label>

      {error && <p className="error">{error}</p>}

      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? "Saving…" : book ? "Save Changes" : "Add Book"}
        </button>
      </div>
    </form>
  )
}

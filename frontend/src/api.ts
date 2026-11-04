// API helper: every call talks to the real FastAPI backend through the
// Vite `/api` proxy (see frontend/vite.config.ts). No mock data anywhere.

import type { Book, BookInput, Stats } from "./types"

// Read a human-friendly error message from a failed response.
async function errorMessage(res: Response): Promise<string> {
  try {
    const data = await res.json()
    if (typeof data.detail === "string") return data.detail
    if (Array.isArray(data.detail)) return "Please check the form fields."
  } catch {
    // fall through to generic message
  }
  return `Request failed (${res.status})`
}

// GET /api/books — list with optional search + category filter.
export async function fetchBooks(search = "", category = ""): Promise<Book[]> {
  const params = new URLSearchParams()
  if (search) params.set("search", search)
  if (category) params.set("category", category)
  const res = await fetch(`/api/books?${params.toString()}`)
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json()
}

// GET /api/books/stats — dashboard statistics.
export async function fetchStats(): Promise<Stats> {
  const res = await fetch("/api/books/stats")
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json()
}

// GET /api/books/{id} — single book.
export async function fetchBook(id: number): Promise<Book> {
  const res = await fetch(`/api/books/${id}`)
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json()
}

// POST /api/books — create a book.
export async function createBook(payload: BookInput): Promise<Book> {
  const res = await fetch("/api/books", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json()
}

// PUT /api/books/{id} — update a book.
export async function updateBook(id: number, payload: Partial<BookInput>): Promise<Book> {
  const res = await fetch(`/api/books/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json()
}

// DELETE /api/books/{id} — delete a book.
export async function deleteBook(id: number): Promise<void> {
  const res = await fetch(`/api/books/${id}`, { method: "DELETE" })
  if (!res.ok) throw new Error(await errorMessage(res))
}

// Shared TypeScript types for the LibTrack Book Management module.

export interface Book {
  id: number
  title: string
  author: string
  isbn: string
  category: string
  publisher: string | null
  published_year: number | null
  total_copies: number
  available_copies: number
  description: string | null
  created_at: string
}

// Payload for creating a book.
export interface BookInput {
  title: string
  author: string
  isbn: string
  category: string
  publisher: string
  published_year: number | null
  total_copies: number
  available_copies: number | null
  description: string
}

// Dashboard statistics returned by GET /api/books/stats.
export interface Stats {
  total_titles: number
  total_copies: number
  available_copies: number
  unavailable_copies: number
}

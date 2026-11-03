// LibTrack — Library Management System (Midterm MVP).
// Single-page dashboard app: navigation, dashboard stats, book CRUD.

import { useState } from "react"
import Dashboard from "./components/Dashboard"
import BookList from "./components/BookList"
import BookForm from "./components/BookForm"
import BookDetails from "./components/BookDetails"
import type { Book } from "./types"

type View = "dashboard" | "list" | "add" | "edit" | "details"

interface Toast {
  message: string
  type: "success" | "error"
}

export default function App() {
  const [view, setView] = useState<View>("dashboard")
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [toast, setToast] = useState<Toast | null>(null)

  // Show a toast notification that auto-hides after 3 seconds.
  function notify(message: string, type: "success" | "error" = "success") {
    setToast({ message, type })
    window.setTimeout(() => setToast(null), 3000)
  }

  // Reload dashboard stats + book list after any CRUD operation.
  function refresh() {
    setRefreshKey((k) => k + 1)
  }

  function goToList(message?: string) {
    refresh()
    setView("list")
    if (message) notify(message)
  }

  function openAdd() {
    setSelectedBook(null)
    setView("add")
  }

  function openEdit(book: Book) {
    setSelectedBook(book)
    setView("edit")
  }

  function openDetails(book: Book) {
    setSelectedBook(book)
    setView("details")
  }

  const navItems: { key: View; label: string; icon: string }[] = [
    { key: "dashboard", label: "Dashboard", icon: "🏠" },
    { key: "list", label: "Books", icon: "📚" },
    { key: "add", label: "Add Book", icon: "➕" },
  ]

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">📖</span>
          <div>
            <h1>LibTrack</h1>
            <p>Library Management</p>
          </div>
        </div>
        <nav>
          {navItems.map((item) => (
            <button
              key={item.key}
              className={`nav-item ${view === item.key ? "active" : ""}`}
              onClick={() => {
                if (item.key === "add") openAdd()
                else setView(item.key)
              }}
            >
              <span>{item.icon}</span> {item.label}
            </button>
          ))}
        </nav>
        <footer className="sidebar-footer">
          <p>Midterm MVP</p>
        </footer>
      </aside>

      <main className="content">
        <header className="content-header">
          <h2>
            {view === "dashboard" && "Dashboard"}
            {view === "list" && "Book List"}
            {view === "add" && "Add Book"}
            {view === "edit" && "Edit Book"}
            {view === "details" && "Book Details"}
          </h2>
        </header>

        {view === "dashboard" && <Dashboard refreshKey={refreshKey} />}

        {view === "list" && (
          <BookList
            refreshKey={refreshKey}
            onView={openDetails}
            onEdit={openEdit}
            notify={notify}
          />
        )}

        {view === "add" && (
          <div className="panel">
            <h3>Add a New Book</h3>
            <BookForm
              book={null}
              onDone={(message) => {
                notify(message)
                goToList()
              }}
            />
          </div>
        )}

        {view === "edit" && selectedBook && (
          <div className="panel">
            <h3>Edit Book #{selectedBook.id}</h3>
            <BookForm
              book={selectedBook}
              onDone={(message) => {
                notify(message)
                goToList()
              }}
            />
          </div>
        )}

        {view === "details" && selectedBook && (
          <BookDetails
            bookId={selectedBook.id}
            onBack={() => setView("list")}
            onEdit={openEdit}
          />
        )}
      </main>

      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  )
}

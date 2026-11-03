// Dashboard: statistics cards computed from real database records.

import { useEffect, useState } from "react"
import { fetchStats } from "../api"
import type { Stats } from "../types"

interface Props {
  refreshKey: number // bump this to reload stats after CRUD operations
}

export default function Dashboard({ refreshKey }: Props) {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let active = true
    setLoading(true)
    setError("")
    fetchStats()
      .then((data) => {
        if (active) setStats(data)
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Failed to load stats")
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [refreshKey])

  if (loading) return <div className="stat-grid loading-block">Loading statistics…</div>
  if (error) return <div className="error-box">{error}</div>
  if (!stats) return null

  const cards = [
    { label: "Total Titles", value: stats.total_titles, icon: "📚" },
    { label: "Total Copies", value: stats.total_copies, icon: "🗂️" },
    { label: "Available Copies", value: stats.available_copies, icon: "✅" },
    { label: "Unavailable Copies", value: stats.unavailable_copies, icon: "🚫" },
  ]

  return (
    <div className="stat-grid">
      {cards.map((card) => (
        <div className="stat-card" key={card.label}>
          <div className="stat-icon">{card.icon}</div>
          <div className="stat-value">{card.value}</div>
          <div className="stat-label">{card.label}</div>
        </div>
      ))}
    </div>
  )
}

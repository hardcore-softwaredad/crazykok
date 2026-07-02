import { useEffect, useMemo, useState } from 'react'

type Event = {
  id: number
  name: string
  description: string | null
  location: string | null
  event_date: string | null
  organizer: string | null
  category: string | null
  expected_revenue: number | null
  expected_attendance: number | null
  is_active: boolean
}

const API_BASE = '/api'

function App() {
  const [events, setEvents] = useState<Event[]>([])
  const [query, setQuery] = useState('')
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadEvents = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await fetch(`${API_BASE}/events?q=${encodeURIComponent(query)}`)
        if (!response.ok) {
          throw new Error('Unable to load events')
        }

        const data = (await response.json()) as Event[]
        setEvents(data)
        setSelectedEvent((current) => {
          if (data.length === 0) {
            return null
          }

          return data.find((event) => event.id === current?.id) ?? data[0]
        })
      } catch {
        setError('The API is not available yet.')
        setEvents([])
        setSelectedEvent(null)
      } finally {
        setIsLoading(false)
      }
    }

    loadEvents()
  }, [query])

  const summary = useMemo(
    () => ({
      total: events.length,
      active: events.filter((event) => event.is_active).length,
      revenue: events.reduce((sum, event) => sum + (event.expected_revenue ?? 0), 0),
    }),
    [events],
  )

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Version 0.1</p>
          <h1>Crazy Kok Venues</h1>
          <p>Track trading opportunities, deadlines, and venue notes from one local workspace.</p>
        </div>
        <div className="hero-card">
          <div>
            <strong>{summary.total}</strong>
            <span>Events</span>
          </div>
          <div>
            <strong>{summary.active}</strong>
            <span>Active</span>
          </div>
          <div>
            <strong>€{summary.revenue}</strong>
            <span>Projected</span>
          </div>
        </div>
      </header>

      <section className="toolbar">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search events"
        />
      </section>

      <main className="content-grid">
        <aside className="list-panel">
          {isLoading ? <p className="empty-state">Loading events...</p> : null}
          {!isLoading && events.length === 0 ? (
            <p className="empty-state">No events yet. The first database is ready for research.</p>
          ) : null}
          {events.map((event) => {
            const isSelected = selectedEvent?.id === event.id

            return (
              <button
                key={event.id}
                className={`event-card ${isSelected ? 'selected' : ''}`}
                onClick={() => setSelectedEvent(event)}
                aria-pressed={isSelected}
              >
                <strong>{event.name}</strong>
                <span>{event.location ?? 'Location pending'}</span>
                <small>{event.event_date ?? 'Date TBD'}</small>
              </button>
            )
          })}
        </aside>

        <section className="detail-panel">
          {error ? (
            <p className="empty-state">{error}</p>
          ) : selectedEvent ? (
            <>
              <h2>{selectedEvent.name}</h2>
              <p>{selectedEvent.description ?? 'No description yet.'}</p>
              <dl>
                <div>
                  <dt>Location</dt>
                  <dd>{selectedEvent.location ?? 'TBD'}</dd>
                </div>
                <div>
                  <dt>Organizer</dt>
                  <dd>{selectedEvent.organizer ?? 'TBD'}</dd>
                </div>
                <div>
                  <dt>Category</dt>
                  <dd>{selectedEvent.category ?? 'Uncategorized'}</dd>
                </div>
                <div>
                  <dt>Expected Revenue</dt>
                  <dd>€{selectedEvent.expected_revenue ?? 0}</dd>
                </div>
                <div>
                  <dt>Expected Attendance</dt>
                  <dd>{selectedEvent.expected_attendance ?? 0}</dd>
                </div>
              </dl>
            </>
          ) : (
            <p>No events found yet.</p>
          )}
        </section>
      </main>
    </div>
  )
}

export default App

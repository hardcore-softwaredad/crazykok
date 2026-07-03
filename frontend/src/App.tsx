import { FormEvent, useEffect, useMemo, useState } from 'react'
import logoUrl from './assets/crazykok-logo.png'

type EventRecord = {
  id: number
  name: string
  description: string | null
  location: string | null
  event_date: string | null
  application_deadline: string | null
  organizer: string | null
  category: string | null
  application_status: string
  source_url: string | null
  notes: string | null
  expected_revenue: number | null
  expected_attendance: number | null
  is_active: boolean
}

type EventForm = {
  name: string
  description: string
  location: string
  event_date: string
  application_deadline: string
  organizer: string
  category: string
  application_status: string
  source_url: string
  notes: string
  expected_revenue: string
  expected_attendance: string
  is_active: boolean
}

type SortKey =
  | 'event_date'
  | 'application_deadline'
  | 'name'
  | 'location'
  | 'category'
  | 'application_status'
  | 'expected_revenue'
  | 'expected_attendance'

const API_BASE = '/api'
const STATUS_OPTIONS = ['researching', 'watchlist', 'applied', 'accepted', 'rejected', 'skipped']

const emptyForm: EventForm = {
  name: '',
  description: '',
  location: '',
  event_date: '',
  application_deadline: '',
  organizer: '',
  category: '',
  application_status: 'researching',
  source_url: '',
  notes: '',
  expected_revenue: '',
  expected_attendance: '',
  is_active: true,
}

function toForm(event: EventRecord): EventForm {
  return {
    name: event.name,
    description: event.description ?? '',
    location: event.location ?? '',
    event_date: event.event_date ?? '',
    application_deadline: event.application_deadline ?? '',
    organizer: event.organizer ?? '',
    category: event.category ?? '',
    application_status: event.application_status,
    source_url: event.source_url ?? '',
    notes: event.notes ?? '',
    expected_revenue: event.expected_revenue?.toString() ?? '',
    expected_attendance: event.expected_attendance?.toString() ?? '',
    is_active: event.is_active,
  }
}

function formToPayload(form: EventForm) {
  return {
    name: form.name.trim(),
    description: form.description.trim() || null,
    location: form.location.trim() || null,
    event_date: form.event_date || null,
    application_deadline: form.application_deadline || null,
    organizer: form.organizer.trim() || null,
    category: form.category.trim() || null,
    application_status: form.application_status,
    source_url: form.source_url.trim() || null,
    notes: form.notes.trim() || null,
    expected_revenue: form.expected_revenue ? Number(form.expected_revenue) : null,
    expected_attendance: form.expected_attendance ? Number(form.expected_attendance) : null,
    is_active: form.is_active,
  }
}

function compareValues(a: string | number | null, b: string | number | null) {
  if (a === b) return 0
  if (a === null) return 1
  if (b === null) return -1
  return a > b ? 1 : -1
}

function App() {
  const [events, setEvents] = useState<EventRecord[]>([])
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [activeFilter, setActiveFilter] = useState<'active' | 'archived' | 'all'>('active')
  const [sortKey, setSortKey] = useState<SortKey>('event_date')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null)
  const [form, setForm] = useState<EventForm>(emptyForm)
  const [isCreating, setIsCreating] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedEvent = events.find((event) => event.id === selectedEventId) ?? null

  const loadEvents = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (query) params.set('q', query)
      if (statusFilter) params.set('status', statusFilter)
      if (activeFilter !== 'all') params.set('active', String(activeFilter === 'active'))

      const response = await fetch(`${API_BASE}/events?${params.toString()}`)
      if (!response.ok) {
        throw new Error('Unable to load events')
      }

      const data = (await response.json()) as EventRecord[]
      setEvents(data)
      setSelectedEventId((currentId) => {
        if (isCreating) return currentId
        if (data.length === 0) return null
        return data.some((event) => event.id === currentId) ? currentId : data[0].id
      })
    } catch {
      setError('The API is not available yet.')
      setEvents([])
      setSelectedEventId(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadEvents()
  }, [query, statusFilter, activeFilter])

  useEffect(() => {
    if (selectedEvent && !isCreating) {
      setForm(toForm(selectedEvent))
    }
  }, [selectedEvent?.id, isCreating])

  const sortedEvents = useMemo(() => {
    return [...events].sort((left, right) => {
      const direction = sortDirection === 'asc' ? 1 : -1
      return compareValues(left[sortKey], right[sortKey]) * direction
    })
  }, [events, sortDirection, sortKey])

  const summary = useMemo(
    () => ({
      total: events.length,
      active: events.filter((event) => event.is_active).length,
      deadlines: events.filter((event) => event.application_deadline).length,
      revenue: events.reduce((sum, event) => sum + (event.expected_revenue ?? 0), 0),
    }),
    [events],
  )

  const updateForm = (field: keyof EventForm, value: string | boolean) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const beginCreate = () => {
    setIsCreating(true)
    setSelectedEventId(null)
    setForm(emptyForm)
  }

  const selectEvent = (event: EventRecord) => {
    setIsCreating(false)
    setSelectedEventId(event.id)
    setForm(toForm(event))
  }

  const saveEvent = async (submitEvent: FormEvent) => {
    submitEvent.preventDefault()
    setIsSaving(true)
    setError(null)

    try {
      const url = isCreating ? `${API_BASE}/events` : `${API_BASE}/events/${selectedEventId}`
      const response = await fetch(url, {
        method: isCreating ? 'POST' : 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formToPayload(form)),
      })

      if (!response.ok) {
        throw new Error('Unable to save event')
      }

      const savedEvent = (await response.json()) as EventRecord
      setIsCreating(false)
      setSelectedEventId(savedEvent.id)
      await loadEvents()
    } catch {
      setError('Could not save this event.')
    } finally {
      setIsSaving(false)
    }
  }

  const archiveSelected = async () => {
    if (!selectedEvent) return
    const endpoint = selectedEvent.is_active ? 'archive' : 'restore'
    await fetch(`${API_BASE}/events/${selectedEvent.id}/${endpoint}`, { method: 'POST' })
    await loadEvents()
  }

  const deleteSelected = async () => {
    if (!selectedEvent) return
    const confirmed = window.confirm(`Permanently delete ${selectedEvent.name}?`)
    if (!confirmed) return

    await fetch(`${API_BASE}/events/${selectedEvent.id}`, { method: 'DELETE' })
    setSelectedEventId(null)
    await loadEvents()
  }

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortKey(key)
    setSortDirection('asc')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <img src={logoUrl} alt="Crazy Kok" className="site-logo" />
          <div>
            <p className="eyebrow">Research Workspace</p>
            <h1>Crazy Kok</h1>
          </div>
        </div>
        <div className="summary-strip">
          <span>
            <strong>{summary.total}</strong> rows
          </span>
          <span>
            <strong>{summary.active}</strong> active
          </span>
          <span>
            <strong>{summary.deadlines}</strong> deadlines
          </span>
          <span>
            <strong>€{summary.revenue}</strong> projected
          </span>
        </div>
      </header>

      <section className="filters">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search" />
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
        <select value={activeFilter} onChange={(event) => setActiveFilter(event.target.value as typeof activeFilter)}>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
          <option value="all">All rows</option>
        </select>
        <button className="primary-action" onClick={beginCreate}>
          New event
        </button>
      </section>

      {error ? <p className="notice">{error}</p> : null}

      <main className="workspace">
        <section className="table-panel">
          <table>
            <thead>
              <tr>
                <th>
                  <button onClick={() => toggleSort('name')}>Event</button>
                </th>
                <th>
                  <button onClick={() => toggleSort('event_date')}>Date</button>
                </th>
                <th>
                  <button onClick={() => toggleSort('application_deadline')}>Deadline</button>
                </th>
                <th>
                  <button onClick={() => toggleSort('location')}>Location</button>
                </th>
                <th>
                  <button onClick={() => toggleSort('category')}>Category</button>
                </th>
                <th>
                  <button onClick={() => toggleSort('application_status')}>Status</button>
                </th>
                <th>
                  <button onClick={() => toggleSort('expected_revenue')}>Revenue</button>
                </th>
                <th>
                  <button onClick={() => toggleSort('expected_attendance')}>Attendance</button>
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={8}>Loading events...</td>
                </tr>
              ) : null}
              {!isLoading && sortedEvents.length === 0 ? (
                <tr>
                  <td colSpan={8}>No matching events yet.</td>
                </tr>
              ) : null}
              {sortedEvents.map((event) => (
                <tr
                  key={event.id}
                  className={event.id === selectedEventId ? 'selected-row' : ''}
                  onClick={() => selectEvent(event)}
                >
                  <td>
                    <strong>{event.name}</strong>
                    {!event.is_active ? <span className="pill muted">archived</span> : null}
                  </td>
                  <td>{event.event_date ?? ''}</td>
                  <td>{event.application_deadline ?? ''}</td>
                  <td>{event.location ?? ''}</td>
                  <td>{event.category ?? ''}</td>
                  <td>
                    <span className="pill">{event.application_status}</span>
                  </td>
                  <td>{event.expected_revenue ? `€${event.expected_revenue}` : ''}</td>
                  <td>{event.expected_attendance ?? ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <aside className="editor-panel">
          <div className="panel-heading">
            <h2>{isCreating ? 'New event' : selectedEvent ? 'Edit event' : 'Event detail'}</h2>
            {selectedEvent ? (
              <div className="panel-actions">
                <button onClick={archiveSelected}>{selectedEvent.is_active ? 'Archive' : 'Restore'}</button>
                <button className="danger-action" onClick={deleteSelected}>
                  Delete
                </button>
              </div>
            ) : null}
          </div>

          {isCreating || selectedEvent ? (
            <form className="event-form" onSubmit={saveEvent}>
              <label>
                Event name
                <input value={form.name} onChange={(event) => updateForm('name', event.target.value)} required />
              </label>
              <div className="form-grid">
                <label>
                  Event date
                  <input type="date" value={form.event_date} onChange={(event) => updateForm('event_date', event.target.value)} />
                </label>
                <label>
                  Deadline
                  <input
                    type="date"
                    value={form.application_deadline}
                    onChange={(event) => updateForm('application_deadline', event.target.value)}
                  />
                </label>
              </div>
              <div className="form-grid">
                <label>
                  Location
                  <input value={form.location} onChange={(event) => updateForm('location', event.target.value)} />
                </label>
                <label>
                  Category
                  <input value={form.category} onChange={(event) => updateForm('category', event.target.value)} />
                </label>
              </div>
              <label>
                Organizer
                <input value={form.organizer} onChange={(event) => updateForm('organizer', event.target.value)} />
              </label>
              <div className="form-grid">
                <label>
                  Status
                  <select value={form.application_status} onChange={(event) => updateForm('application_status', event.target.value)}>
                    {STATUS_OPTIONS.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="checkbox-label">
                  <input type="checkbox" checked={form.is_active} onChange={(event) => updateForm('is_active', event.target.checked)} />
                  Active
                </label>
              </div>
              <div className="form-grid">
                <label>
                  Revenue
                  <input
                    type="number"
                    min="0"
                    value={form.expected_revenue}
                    onChange={(event) => updateForm('expected_revenue', event.target.value)}
                  />
                </label>
                <label>
                  Attendance
                  <input
                    type="number"
                    min="0"
                    value={form.expected_attendance}
                    onChange={(event) => updateForm('expected_attendance', event.target.value)}
                  />
                </label>
              </div>
              <label>
                Source URL
                <input value={form.source_url} onChange={(event) => updateForm('source_url', event.target.value)} />
              </label>
              <label>
                Description
                <textarea value={form.description} onChange={(event) => updateForm('description', event.target.value)} rows={3} />
              </label>
              <label>
                Notes
                <textarea value={form.notes} onChange={(event) => updateForm('notes', event.target.value)} rows={5} />
              </label>
              <button className="primary-action" type="submit" disabled={isSaving}>
                {isSaving ? 'Saving...' : 'Save event'}
              </button>
            </form>
          ) : (
            <p className="empty-state">Select a row or create a new event.</p>
          )}
        </aside>
      </main>
    </div>
  )
}

export default App

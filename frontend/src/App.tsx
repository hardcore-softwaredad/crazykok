import { FormEvent, useEffect, useMemo, useState } from 'react'
import logoUrl from './assets/crazykok-logo.png'
import ImportWorkspace from './ImportWorkspace'
import VenueWorkspace from './VenueWorkspace'
import PlanningWorkspace from './PlanningWorkspace'
import EngagementsWorkspace from './EngagementsWorkspace'
import {
  assignOpportunitySeries,
  createOpportunity,
  createSeriesFromOpportunity,
  deleteOpportunity,
  detachOpportunitySeries,
  findOpportunities,
  findOpportunitySeries,
  followOpportunityPage,
  type HalLinks,
  type Opportunity,
  type OpportunitySeries,
  type PageMetadata,
  updateOpportunity,
} from './api'

type EventForm = {
  name: string
  description: string
  location: string
  event_date: string
  application_deadline: string
  organizer: string
  series_name: string
  category: string
  application_status: string
  source_url: string
  notes: string
  expected_revenue: string
  expected_attendance: string
  profit_score: string
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
  | 'profit_score'

const STATUS_OPTIONS = ['researching', 'watchlist', 'applied', 'accepted', 'rejected', 'skipped']

const emptyForm: EventForm = {
  name: '',
  description: '',
  location: '',
  event_date: '',
  application_deadline: '',
  organizer: '',
  series_name: '',
  category: '',
  application_status: 'researching',
  source_url: '',
  notes: '',
  expected_revenue: '',
  expected_attendance: '',
  profit_score: '',
  is_active: true,
}

function toForm(event: Opportunity): EventForm {
  return {
    name: event.name,
    description: event.description ?? '',
    location: event.location ?? '',
    event_date: event.event_date ?? '',
    application_deadline: event.application_deadline ?? '',
    organizer: event.organizer ?? '',
    series_name: event.series_name ?? '',
    category: event.category ?? '',
    application_status: event.application_status,
    source_url: event.source_url ?? '',
    notes: event.notes ?? '',
    expected_revenue: event.expected_revenue?.toString() ?? '',
    expected_attendance: event.expected_attendance?.toString() ?? '',
    profit_score: event.profit_score?.toString() ?? '',
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
    series_name: form.series_name.trim() || null,
    category: form.category.trim() || null,
    application_status: form.application_status,
    source_url: form.source_url.trim() || null,
    notes: form.notes.trim() || null,
    expected_revenue: form.expected_revenue ? Number(form.expected_revenue) : null,
    expected_attendance: form.expected_attendance ? Number(form.expected_attendance) : null,
    profit_score: form.profit_score ? Number(form.profit_score) : null,
    is_active: form.is_active,
  }
}

function OpportunityWorkspace() {
  const [events, setEvents] = useState<Opportunity[]>([])
  const [series, setSeries] = useState<OpportunitySeries[]>([])
  const [page, setPage] = useState<PageMetadata>({ number: 1, size: 25, total_elements: 0, total_pages: 0 })
  const [pageLinks, setPageLinks] = useState<HalLinks>({})
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
  const [seriesSelection, setSeriesSelection] = useState('')
  const [error, setError] = useState<string | null>(null)

  const selectedEvent = events.find((event) => event.id === selectedEventId) ?? null

  const loadEvents = async (href?: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const collection = href
        ? await followOpportunityPage(href)
        : await findOpportunities({
            q: query || undefined,
            status: statusFilter || undefined,
            active: activeFilter === 'all' ? undefined : activeFilter === 'active',
            sort: sortKey,
            direction: sortDirection,
            page_size: 25,
          })
      const data = collection._embedded.opportunities
      setEvents(data)
      setPage(collection.page)
      setPageLinks(collection._links)
      setSelectedEventId((currentId) => {
        if (isCreating) return currentId
        if (data.length === 0) return null
        return data.some((event) => event.id === currentId) ? currentId : data[0].id
      })
    } catch {
      setError('The API is not available yet.')
      setEvents([])
      setPage({ number: 1, size: 25, total_elements: 0, total_pages: 0 })
      setPageLinks({})
      setSelectedEventId(null)
    } finally {
      setIsLoading(false)
    }
  }

  const loadSeries = async () => {
    try {
      const collection = await findOpportunitySeries()
      setSeries(collection._embedded.series)
    } catch {
      setSeries([])
    }
  }

  useEffect(() => {
    loadEvents()
  }, [query, statusFilter, activeFilter, sortKey, sortDirection])

  useEffect(() => {
    loadSeries()
  }, [])

  useEffect(() => {
    if (selectedEvent && !isCreating) {
      setForm(toForm(selectedEvent))
      setSeriesSelection(series.find((item) => item.name === selectedEvent.series_name)?.id.toString() ?? '')
    }
  }, [selectedEvent?.id, selectedEvent?.series_name, isCreating, series])

  const summary = useMemo(
    () => ({
      total: page.total_elements,
      pageCount: events.length,
      active: events.filter((event) => event.is_active).length,
      deadlines: events.filter((event) => event.application_deadline).length,
      revenue: events.reduce((sum, event) => sum + (event.expected_revenue ?? 0), 0),
    }),
    [events, page.total_elements],
  )

  const updateForm = (field: keyof EventForm, value: string | boolean) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const beginCreate = () => {
    setIsCreating(true)
    setSelectedEventId(null)
    setForm(emptyForm)
  }

  const selectEvent = (event: Opportunity) => {
    setIsCreating(false)
    setSelectedEventId(event.id)
    setForm(toForm(event))
  }

  const saveEvent = async (submitEvent: FormEvent) => {
    submitEvent.preventDefault()
    setIsSaving(true)
    setError(null)

    try {
      const payload = formToPayload(form)
      const savedEvent = isCreating
        ? await createOpportunity(payload)
        : await updateOpportunity(selectedEvent as Opportunity, payload)
      setIsCreating(false)
      setSelectedEventId(savedEvent.id)
      await loadEvents()
    } catch {
      setError('Could not save this opportunity.')
    } finally {
      setIsSaving(false)
    }
  }

  const archiveSelected = async () => {
    if (!selectedEvent) return
    await updateOpportunity(selectedEvent, { is_active: !selectedEvent.is_active })
    await loadEvents()
  }

  const deleteSelected = async () => {
    if (!selectedEvent) return
    const confirmed = window.confirm(`Permanently delete ${selectedEvent.name}?`)
    if (!confirmed) return

    await deleteOpportunity(selectedEvent)
    setSelectedEventId(null)
    await loadEvents()
  }

  const attachSelectedSeries = async () => {
    if (!selectedEvent || !seriesSelection) return
    setError(null)
    try {
      const savedEvent = await assignOpportunitySeries(selectedEvent, { series_id: Number(seriesSelection) })
      setSelectedEventId(savedEvent.id)
      await loadEvents()
    } catch {
      setError('Could not attach this opportunity to the selected series.')
    }
  }

  const createSeriesForSelected = async () => {
    if (!selectedEvent) return
    setError(null)
    try {
      const savedEvent = await createSeriesFromOpportunity(selectedEvent, { name: form.series_name || selectedEvent.name })
      setSelectedEventId(savedEvent.id)
      await loadSeries()
      await loadEvents()
    } catch {
      setError('Could not create a series from this opportunity.')
    }
  }

  const detachSeriesFromSelected = async () => {
    if (!selectedEvent) return
    setError(null)
    try {
      const savedEvent = await detachOpportunitySeries(selectedEvent)
      setSelectedEventId(savedEvent.id)
      setSeriesSelection('')
      await loadEvents()
    } catch {
      setError('Could not detach this opportunity from its series.')
    }
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
            <strong>{summary.total}</strong> matching
          </span>
          <span>
            <strong>{summary.pageCount}</strong> on page
          </span>
          <span>
            <strong>{summary.deadlines}</strong> page deadlines
          </span>
          <span>
            <strong>€{summary.revenue}</strong> page projected
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
            New opportunity
        </button>
      </section>

      {error ? <p className="notice">{error}</p> : null}

      <main className="workspace">
        <section className="table-panel">
          <table>
            <thead>
              <tr>
                <th>
                  <button onClick={() => toggleSort('name')}>Opportunity</button>
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
                <th>
                  <button onClick={() => toggleSort('profit_score')}>Score</button>
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={9}>Loading opportunities...</td>
                </tr>
              ) : null}
              {!isLoading && events.length === 0 ? (
                <tr>
                  <td colSpan={9}>No matching opportunities yet.</td>
                </tr>
              ) : null}
              {events.map((event) => (
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
                  <td>{event.profit_score ?? ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination" aria-label="Opportunity pages">
            <button disabled={!pageLinks.prev || isLoading} onClick={() => pageLinks.prev && loadEvents(pageLinks.prev.href)}>
              Previous
            </button>
            <span>Page {page.number}{page.total_pages ? ` of ${page.total_pages}` : ''}</span>
            <button disabled={!pageLinks.next || isLoading} onClick={() => pageLinks.next && loadEvents(pageLinks.next.href)}>
              Next
            </button>
          </div>
        </section>

        <aside className="editor-panel">
          <div className="panel-heading">
            <h2>{isCreating ? 'New opportunity' : selectedEvent ? 'Edit opportunity' : 'Opportunity detail'}</h2>
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
                Opportunity name
                <input value={form.name} onChange={(event) => updateForm('name', event.target.value)} required />
              </label>
              <div className="form-grid">
                <label>
                  Opportunity date
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
              <label>
                Opportunity series
                <input value={form.series_name} onChange={(event) => updateForm('series_name', event.target.value)} placeholder="Recurring event name" />
              </label>
              {!isCreating && selectedEvent ? (
                <section className="series-tools" aria-label="Opportunity series tools">
                  <p>
                    Current series: <strong>{selectedEvent.series_name ?? 'None'}</strong>
                  </p>
                  <div className="form-grid">
                    <label>
                      Attach existing series
                      <select value={seriesSelection} onChange={(event) => setSeriesSelection(event.target.value)}>
                        <option value="">Choose a series</option>
                        {series.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.opportunity_count})</option>)}
                      </select>
                    </label>
                    <button type="button" className="quiet-action" onClick={attachSelectedSeries} disabled={!seriesSelection}>Attach</button>
                  </div>
                  <div className="inline-actions">
                    <button type="button" className="quiet-action" onClick={createSeriesForSelected}>Create series from this opportunity</button>
                    <button type="button" className="quiet-action" onClick={detachSeriesFromSelected} disabled={!selectedEvent.series_name}>Detach from series</button>
                  </div>
                </section>
              ) : null}
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
                Profit score
                <input type="number" min="0" max="100" value={form.profit_score} onChange={(event) => updateForm('profit_score', event.target.value)} />
              </label>
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
                {isSaving ? 'Saving...' : 'Save opportunity'}
              </button>
            </form>
          ) : (
            <p className="empty-state">Select a row or create a new opportunity.</p>
          )}
        </aside>
      </main>
    </div>
  )
}

function App() {
  const [view, setView] = useState<'opportunities' | 'planning' | 'engagements' | 'venues' | 'import'>('venues')

  return (
    <div>
      <nav className="app-navigation" aria-label="Primary navigation">
        <div className="nav-brand"><img src={logoUrl} alt="" /><strong>Crazy Kok</strong></div>
        <div className="nav-links">
          <button className={view === 'opportunities' ? 'active' : ''} onClick={() => setView('opportunities')}>Opportunities</button>
          <button className={view === 'planning' ? 'active' : ''} onClick={() => setView('planning')}>Map &amp; calendar</button>
          <button className={view === 'engagements' ? 'active' : ''} onClick={() => setView('engagements')}>Engagements</button>
          <button className={view === 'venues' ? 'active' : ''} onClick={() => setView('venues')}>Venues</button>
          <button className={view === 'import' ? 'active' : ''} onClick={() => setView('import')}>Import venues</button>
        </div>
      </nav>
      {view === 'opportunities' ? <OpportunityWorkspace /> : view === 'planning' ? <PlanningWorkspace /> : view === 'engagements' ? <EngagementsWorkspace /> : view === 'venues' ? <VenueWorkspace /> : <ImportWorkspace />}
    </div>
  )
}

export default App

import { useEffect, useMemo, useState } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { findPlanning, type PlanningOpportunity } from './api'

type Filters = {
  dateFrom: string
  dateTo: string
  maxDistance: string
  status: string
  minScore: string
}

type Selection =
  | { kind: 'opportunity' | 'deadline'; opportunity: PlanningOpportunity }
  | { kind: 'operation'; opportunity: PlanningOpportunity; operationId: number }

const emptyFilters: Filters = { dateFrom: '', dateTo: '', maxDistance: '', status: '', minScore: '' }

function FitMarkers({ opportunities }: { opportunities: PlanningOpportunity[] }) {
  const map = useMap()

  useEffect(() => {
    const points = opportunities.flatMap((opportunity) => {
      const venue = opportunity.venue
      return venue?.latitude != null && venue.longitude != null
        ? [[venue.latitude, venue.longitude] as [number, number]]
        : []
    })
    if (points.length === 1) map.setView(points[0], 11)
    if (points.length > 1) map.fitBounds(points, { padding: [30, 30] })
  }, [map, opportunities])
  return null
}

export default function PlanningWorkspace() {
  const [filters, setFilters] = useState<Filters>(emptyFilters)
  const [opportunities, setOpportunities] = useState<PlanningOpportunity[]>([])
  const [warnings, setWarnings] = useState<{ code: 'missing_coordinates' | 'missing_date'; opportunity_id: number; title: string }[]>([])
  const [selection, setSelection] = useState<Selection | null>(null)
  const [view, setView] = useState<'map' | 'calendar'>('map')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setIsLoading(true)
    setError(null)
    findPlanning({
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      max_distance_km: filters.maxDistance || undefined,
      status: filters.status || undefined,
      min_score: filters.minScore || undefined,
    })
      .then((result) => {
        if (controller.signal.aborted) return
        setOpportunities(result.opportunities)
        setWarnings(result.warnings)
        setSelection(null)
      })
      .catch(() => {
        if (!controller.signal.aborted) setError('Could not load planning data.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false)
      })
    return () => controller.abort()
  }, [filters])

  const mapOpportunities = opportunities.filter(
    (opportunity) => opportunity.venue?.latitude != null && opportunity.venue.longitude != null,
  )
  const calendarEvents = useMemo(
    () => opportunities.flatMap((opportunity) => {
      const events = []
      if (opportunity.event_date) {
        events.push({
          id: `opportunity-${opportunity.id}`,
          title: opportunity.name,
          start: opportunity.event_date,
          allDay: true,
          classNames: ['calendar-opportunity'],
          extendedProps: { kind: 'opportunity', opportunity },
        })
      }
      if (opportunity.application_deadline) {
        events.push({
          id: `deadline-${opportunity.id}`,
          title: `Deadline · ${opportunity.name}`,
          start: opportunity.application_deadline,
          allDay: true,
          classNames: ['calendar-deadline'],
          extendedProps: { kind: 'deadline', opportunity },
        })
      }
      opportunity.operations.forEach((operation) => {
        if (!opportunity.event_date) return
        events.push({
          id: `operation-${operation.id}`,
          title: `Committed · ${opportunity.name}`,
          start: opportunity.event_date,
          allDay: true,
          classNames: ['calendar-operation'],
          extendedProps: { kind: 'operation', opportunity, operationId: operation.id },
        })
      })
      return events
    }),
    [opportunities],
  )

  const initialDate = calendarEvents[0]?.start
  const missingCoordinates = warnings.filter((warning) => warning.code === 'missing_coordinates')
  const missingDates = warnings.filter((warning) => warning.code === 'missing_date')
  const selectedOperation = selection?.kind === 'operation'
    ? selection.opportunity.operations.find((operation) => operation.id === selection.operationId)
    : null

  return (
    <div className="planning-shell">
      <header className="planning-header">
        <div>
          <p className="eyebrow">Decision desk</p>
          <h1>Map &amp; calendar</h1>
          <p>See where the promising work is, when decisions are due, and what is already committed.</p>
        </div>
        <div className="view-switcher" aria-label="Planning view">
          <button className={view === 'map' ? 'active' : ''} onClick={() => setView('map')}>Map</button>
          <button className={view === 'calendar' ? 'active' : ''} onClick={() => setView('calendar')}>Calendar</button>
        </div>
      </header>

      <section className="planning-filters" aria-label="Planning filters">
        <label>From<input type="date" value={filters.dateFrom} onChange={(event) => setFilters({ ...filters, dateFrom: event.target.value })} /></label>
        <label>To<input type="date" value={filters.dateTo} onChange={(event) => setFilters({ ...filters, dateTo: event.target.value })} /></label>
        <label>Within<input type="number" min="0" placeholder="km" value={filters.maxDistance} onChange={(event) => setFilters({ ...filters, maxDistance: event.target.value })} /></label>
        <label>Status<select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
          <option value="">Any status</option>
          <option value="researching">Researching</option><option value="watchlist">Watchlist</option>
          <option value="applied">Applied</option><option value="accepted">Accepted</option>
          <option value="committed">Committed</option><option value="cancelled">Cancelled</option>
        </select></label>
        <label>Score<input type="number" min="0" max="100" placeholder="minimum" value={filters.minScore} onChange={(event) => setFilters({ ...filters, minScore: event.target.value })} /></label>
        <button type="button" className="quiet-action" onClick={() => setFilters(emptyFilters)}>Clear</button>
      </section>

      {error ? <p className="notice">{error}</p> : null}
      {warnings.length ? <section className="planning-warnings" aria-label="Planning data warnings">
        {missingCoordinates.length ? <p><strong>{missingCoordinates.length}</strong> {missingCoordinates.length === 1 ? 'opportunity has' : 'opportunities have'} no map coordinates: {missingCoordinates.map((item) => item.title).join(', ')}.</p> : null}
        {missingDates.length ? <p><strong>{missingDates.length}</strong> {missingDates.length === 1 ? 'opportunity has' : 'opportunities have'} no date: {missingDates.map((item) => item.title).join(', ')}.</p> : null}
      </section> : null}

      <main className="planning-layout">
        <section className="planning-canvas" aria-busy={isLoading}>
          {isLoading ? <p className="map-empty">Loading the planning board…</p> : null}
          {!isLoading && view === 'map' ? <MapContainer center={[52.86, 6.61]} zoom={9} scrollWheelZoom className="planning-map">
            <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <FitMarkers opportunities={mapOpportunities} />
            {mapOpportunities.map((opportunity) => <CircleMarker
              key={opportunity.id}
              center={[opportunity.venue!.latitude!, opportunity.venue!.longitude!]}
              radius={9}
              pathOptions={{ color: '#172b26', fillColor: opportunity.operations.length ? '#ef7b45' : '#f2c14e', fillOpacity: 0.9 }}
              eventHandlers={{ click: () => setSelection({ kind: 'opportunity', opportunity }) }}
            ><Popup><button className="marker-detail" onClick={() => setSelection({ kind: 'opportunity', opportunity })}><strong>{opportunity.name}</strong><span>{opportunity.venue?.name}</span><span>{opportunity.distance_km} km · score {opportunity.profit_score ?? '—'}</span></button></Popup></CircleMarker>)}
          </MapContainer> : null}
          {!isLoading && view === 'calendar' ? <div className="planning-calendar">
            <FullCalendar
              key={initialDate ?? 'empty'}
              plugins={[dayGridPlugin, interactionPlugin]}
              initialView="dayGridMonth"
              initialDate={initialDate}
              events={calendarEvents}
              eventClick={(info) => setSelection(info.event.extendedProps as Selection)}
              height="auto"
            />
            <div className="calendar-legend"><span className="opportunity">Opportunity</span><span className="deadline">Application deadline</span><span className="operation">Committed operation</span></div>
          </div> : null}
        </section>

        <aside className="planning-detail" aria-label="Planning detail">
          {selection ? <>
            <p className="eyebrow">{selection.kind === 'deadline' ? 'Application deadline' : selection.kind}</p>
            <h2>{selection.opportunity.name}</h2>
            <dl>
              <div><dt>Opportunity date</dt><dd>{selection.opportunity.event_date ?? 'Missing date'}</dd></div>
              <div><dt>Deadline</dt><dd>{selection.opportunity.application_deadline ?? 'None recorded'}</dd></div>
              <div><dt>Venue</dt><dd>{selection.opportunity.venue?.name ?? 'No venue linked'}</dd></div>
              <div><dt>Distance</dt><dd>{selection.opportunity.distance_km != null ? `${selection.opportunity.distance_km} km straight-line` : 'Unknown'}</dd></div>
              <div><dt>Score</dt><dd>{selection.opportunity.profit_score ?? 'Not scored'}</dd></div>
              <div><dt>Status</dt><dd>{selectedOperation?.status ?? selection.opportunity.application_status}</dd></div>
            </dl>
            <a className="primary-action detail-link" href={selectedOperation?._links.self.href ?? selection.opportunity._links.self.href}>Open {selection.kind === 'operation' ? 'operation' : 'opportunity'} detail</a>
          </> : <div className="empty-state"><strong>Pick a marker or calendar entry</strong><p>Its opportunity or operation detail will appear here.</p></div>}
        </aside>
      </main>
    </div>
  )
}

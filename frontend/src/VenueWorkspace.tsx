import { FormEvent, useEffect, useMemo, useState } from 'react'
import { findVenues, type Venue as VenueRecord } from './api'

type FieldSpec = {
  name: string
  label: string
  type: 'string' | 'text' | 'enum' | 'url' | 'email' | 'phone' | 'multivalue' | 'integer' | 'decimal' | 'date' | 'boolean'
  section: string
  required: boolean
  read_only_after_create: boolean
  enum: string[]
}

type VenueSchema = { schema_version: number; fields: FieldSpec[]; sections: string[] }
type RelatedTab = 'overview' | 'contacts' | 'documents' | 'photos' | 'opportunities' | 'notes' | 'statistics'

const API_BASE = '/api'

function valueForInput(value: unknown): string | boolean {
  if (typeof value === 'boolean') return value
  return value === null || value === undefined ? '' : String(value)
}

function safeExternalUrl(value: unknown): string | null {
  if (typeof value !== 'string') return null
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null
  } catch {
    return null
  }
}

function toPayload(form: Record<string, string | boolean>, fields: FieldSpec[]) {
  return Object.fromEntries(
    fields.map((field) => {
      const raw = form[field.name]
      if (field.type === 'boolean') return [field.name, Boolean(raw)]
      if (raw === '') return [field.name, null]
      if (field.type === 'integer') return [field.name, Number.parseInt(String(raw), 10)]
      if (field.type === 'decimal') return [field.name, Number.parseFloat(String(raw))]
      return [field.name, String(raw).trim() || null]
    }),
  )
}

function VenueField({
  field,
  value,
  disabled,
  onChange,
}: {
  field: FieldSpec
  value: string | boolean
  disabled: boolean
  onChange: (value: string | boolean) => void
}) {
  if (field.type === 'boolean') {
    return (
      <label className="checkbox-label field-control">
        <input type="checkbox" checked={Boolean(value)} disabled={disabled} onChange={(event) => onChange(event.target.checked)} />
        {field.label}
      </label>
    )
  }
  if (field.enum.length) {
    return (
      <label className="field-control">
        {field.label}
        <select value={String(value)} disabled={disabled} required={field.required} onChange={(event) => onChange(event.target.value)}>
          <option value="">Unknown</option>
          {field.enum.map((option) => <option key={option} value={option}>{option.replace(/_/g, ' ')}</option>)}
        </select>
      </label>
    )
  }
  if (field.type === 'text') {
    return (
      <label className="field-control field-control-wide">
        {field.label}
        <textarea value={String(value)} disabled={disabled} rows={3} onChange={(event) => onChange(event.target.value)} />
      </label>
    )
  }
  const inputType = field.type === 'integer' || field.type === 'decimal' ? 'number' : field.type === 'phone' ? 'tel' : field.type
  return (
    <label className="field-control">
      {field.label}
      <input
        type={inputType === 'multivalue' || inputType === 'string' ? 'text' : inputType}
        step={field.type === 'decimal' ? 'any' : undefined}
        value={String(value)}
        disabled={disabled}
        required={field.required}
        onChange={(event) => onChange(event.target.value)}
      />
      {field.type === 'multivalue' ? <small>Separate values with semicolons</small> : null}
    </label>
  )
}

function RelatedPanel({ venue, tab }: { venue: VenueRecord; tab: Exclude<RelatedTab, 'overview'> }) {
  const [items, setItems] = useState<Record<string, unknown>[]>([])
  const [error, setError] = useState('')
  const [text, setText] = useState('')
  const [secondary, setSecondary] = useState('')
  const [externalId, setExternalId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const endpoint = tab === 'statistics' ? 'statistics' : tab

  const load = () => {
    setError('')
    return fetch(`${API_BASE}/venues/${venue.id}/${endpoint}`)
      .then(async (response) => {
        if (!response.ok) throw new Error('Unable to load this section')
        const result = await response.json() as Record<string, unknown>[] | Record<string, unknown>
        setItems(Array.isArray(result) ? result : [result])
      })
      .catch((reason: Error) => setError(reason.message))
  }

  useEffect(() => { void load() }, [endpoint, venue.id])

  const addItem = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    let body: BodyInit
    let headers: HeadersInit | undefined = { 'Content-Type': 'application/json' }
    let url = `${API_BASE}/venues/${venue.id}/${endpoint}`
    if (tab === 'contacts') {
      body = JSON.stringify({ contact_external_id: externalId, name: text, email: secondary || null })
    } else if (tab === 'notes') {
      body = JSON.stringify({ body: text, origin: 'user', note_type: 'internal' })
    } else if ((tab === 'documents' || tab === 'photos') && file) {
      const data = new FormData()
      data.append('file', file)
      if (tab === 'documents') {
        data.append('document_external_id', externalId)
        data.append('document_type', 'venue_document')
        data.append('title', text)
      } else {
        data.append('alt_text', text)
        if (secondary) data.append('caption', secondary)
      }
      body = data
      headers = undefined
      url += '/upload'
    } else {
      return
    }
    const response = await fetch(url, { method: 'POST', headers, body })
    if (!response.ok) {
      setError('Unable to add this record.')
      return
    }
    setText(''); setSecondary(''); setExternalId(''); setFile(null)
    await load()
  }

  const archiveItem = async (id: unknown) => {
    await fetch(`${API_BASE}/venues/${venue.id}/${endpoint}/${String(id)}`, { method: 'DELETE' })
    await load()
  }

  const canCreate = ['contacts', 'documents', 'photos', 'notes'].includes(tab)

  return (
    <section className="related-panel">
      {error ? <p className="notice">{error}</p> : null}
      {canCreate ? (
        <form className="related-form" onSubmit={addItem}>
          {tab === 'contacts' || tab === 'documents' ? <label>Stable external ID<input value={externalId} onChange={(event) => setExternalId(event.target.value)} required /></label> : null}
          <label>{tab === 'notes' ? 'Note' : tab === 'photos' ? 'Alternative text' : tab === 'contacts' ? 'Contact name' : 'Document title'}
            {tab === 'notes' ? <textarea value={text} onChange={(event) => setText(event.target.value)} required /> : <input value={text} onChange={(event) => setText(event.target.value)} required />}
          </label>
          {tab === 'contacts' ? <label>Email<input type="email" value={secondary} onChange={(event) => setSecondary(event.target.value)} /></label> : null}
          {tab === 'photos' ? <label>Caption<input value={secondary} onChange={(event) => setSecondary(event.target.value)} /></label> : null}
          {tab === 'documents' || tab === 'photos' ? <label>File<input type="file" accept={tab === 'photos' ? 'image/jpeg,image/png,image/webp' : 'application/pdf,image/jpeg,image/png,image/webp'} onChange={(event) => setFile(event.target.files?.[0] ?? null)} required /></label> : null}
          <button className="primary-action">Add {tab.slice(0, -1)}</button>
        </form>
      ) : null}
      {!error && items.length === 0 ? <p className="empty-state">No {tab} recorded yet.</p> : null}
      {items.map((item, index) => (
        <article className="related-card" key={String(item.id ?? index)}>
          {tab === 'photos' && item.local_path ? <img className="venue-photo" src={`${API_BASE}/venues/${venue.id}/photos/${String(item.id)}/content`} alt={String(item.alt_text ?? '')} /> : null}
          {tab === 'documents' && (item.local_path || safeExternalUrl(item.url)) ? (
            <div className="document-actions">
              {item.local_path ? <a className="button-link primary-action" href={`${API_BASE}/venues/${venue.id}/documents/${String(item.id)}/preview`} target="_blank" rel="noreferrer">Preview attachment</a> : null}
              {item.local_path ? <a className="button-link" href={`${API_BASE}/venues/${venue.id}/documents/${String(item.id)}/download`}>Download attachment</a> : null}
              {safeExternalUrl(item.url) ? <a className="button-link" href={safeExternalUrl(item.url) ?? undefined} target="_blank" rel="noreferrer">Open document link</a> : null}
            </div>
          ) : null}
          {Object.entries(item).filter(([key, value]) => !['id', 'venue_id', 'local_path', 'url'].includes(key) && value !== null).map(([key, value]) => (
            <p key={key}><strong>{key.replace(/_/g, ' ')}:</strong> {String(value)}</p>
          ))}
          {canCreate ? <button className="danger-action" onClick={() => archiveItem(item.id)}>Archive</button> : null}
        </article>
      ))}
    </section>
  )
}

function CoordinatePreview({
  latitude,
  longitude,
  onPick,
}: {
  latitude: string | boolean
  longitude: string | boolean
  onPick: (latitude: number, longitude: number) => void
}) {
  const lat = Number(latitude)
  const lon = Number(longitude)
  const locate = () => navigator.geolocation?.getCurrentPosition((position) => onPick(position.coords.latitude, position.coords.longitude))
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || latitude === '' || longitude === '') {
    return <div className="map-placeholder"><p>Enter verified latitude and longitude to preview the venue location.</p><button type="button" onClick={locate}>Use current location</button></div>
  }
  const delta = 0.008
  const bbox = `${lon - delta},${lat - delta},${lon + delta},${lat + delta}`
  const embed = `https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(bbox)}&layer=mapnik&marker=${lat}%2C${lon}`
  return (
    <div className="map-preview">
      <iframe title="Venue map preview" src={embed} loading="lazy" />
      <div className="map-actions"><a href={`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=17/${lat}/${lon}`} target="_blank" rel="noreferrer">Open location in OpenStreetMap</a><button type="button" onClick={locate}>Use current location</button></div>
    </div>
  )
}

export default function VenueWorkspace() {
  const [schema, setSchema] = useState<VenueSchema | null>(null)
  const [venues, setVenues] = useState<VenueRecord[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form, setForm] = useState<Record<string, string | boolean>>({})
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('')
  const [active, setActive] = useState<'true' | 'false' | 'all'>('true')
  const [creating, setCreating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [activeSection, setActiveSection] = useState('Identity')
  const [tab, setTab] = useState<RelatedTab>('overview')

  const selected = venues.find((venue) => venue.id === selectedId) ?? null

  useEffect(() => {
    fetch(`${API_BASE}/venues/schema`).then((response) => response.json()).then(setSchema).catch(() => setError('Unable to load venue schema.'))
  }, [])

  const loadVenues = async () => {
    try {
      const collection = await findVenues({
        q: query || undefined,
        research_status: status || undefined,
        active: active === 'all' ? undefined : active,
        page_size: 100,
      })
      const data = collection._embedded.venues
      setVenues(data)
      setSelectedId((current) => creating ? current : data.some((venue) => venue.id === current) ? current : data[0]?.id ?? null)
      setError('')
    } catch {
      setError('Unable to load venues.')
    }
  }

  useEffect(() => { void loadVenues() }, [query, status, active])

  useEffect(() => {
    if (!schema || !selected || creating) return
    setForm(Object.fromEntries(schema.fields.map((field) => [field.name, valueForInput(selected[field.name])])))
  }, [schema, selected?.id, creating])

  const fieldsBySection = useMemo(() => {
    if (!schema) return new Map<string, FieldSpec[]>()
    return new Map(schema.sections.map((section) => [section, schema.fields.filter((field) => field.section === section)]))
  }, [schema])

  const beginCreate = () => {
    if (!schema) return
    setCreating(true)
    setSelectedId(null)
    setTab('overview')
    setActiveSection('Identity')
    setForm(Object.fromEntries(schema.fields.map((field) => [field.name, field.name === 'active' ? true : field.name === 'research_status' ? 'discovered' : field.name === 'confidence_rating' ? 'E' : ''])))
  }

  const save = async (event: FormEvent) => {
    event.preventDefault()
    if (!schema) return
    setSaving(true)
    setError('')
    try {
      const payload = toPayload(form, schema.fields)
      const options = {
        method: creating ? 'POST' : 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }
      let response = await fetch(creating ? `${API_BASE}/venues` : `${API_BASE}/venues/${selectedId}`, options)
      if (response.status === 409 && creating) {
        const problem = await response.json() as { detail?: { code?: string; candidates?: { venue_name: string }[] } }
        if (problem.detail?.code === 'probable_duplicate') {
          const names = problem.detail.candidates?.map((candidate) => candidate.venue_name).join(', ')
          const confirmed = window.confirm(`Possible duplicate: ${names}. Create this as a distinct venue anyway?`)
          if (confirmed) {
            response = await fetch(`${API_BASE}/venues?allow_duplicate=true&duplicate_reason=${encodeURIComponent('Reviewed as distinct in venue form')}`, options)
          } else {
            throw new Error('Creation cancelled so the possible duplicate can be reviewed.')
          }
        } else {
          throw new Error(JSON.stringify(problem.detail))
        }
      }
      if (!response.ok) {
        const problem = await response.json() as { detail?: unknown }
        throw new Error(typeof problem.detail === 'string' ? problem.detail : JSON.stringify(problem.detail))
      }
      const saved = await response.json() as VenueRecord
      setCreating(false)
      setSelectedId(saved.id)
      await loadVenues()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to save venue.')
    } finally {
      setSaving(false)
    }
  }

  const toggleArchive = async () => {
    if (!selected) return
    await fetch(`${API_BASE}/venues/${selected.id}/${selected.active ? 'archive' : 'restore'}`, { method: 'POST' })
    await loadVenues()
  }

  return (
    <div className="venue-workspace">
      <section className="filters venue-filters">
        <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search venues, towns, postcodes…" />
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All research statuses</option>
          {['discovered', 'identified', 'researched', 'verified', 'complete', 'archived'].map((option) => <option key={option}>{option}</option>)}
        </select>
        <select value={active} onChange={(event) => setActive(event.target.value as typeof active)}>
          <option value="true">Active</option><option value="false">Archived</option><option value="all">All</option>
        </select>
        <a className="button-link" href={`${API_BASE}/venues/export.csv${query ? `?q=${encodeURIComponent(query)}` : ''}`}>Export research CSV</a>
        <button className="primary-action" onClick={beginCreate}>New venue</button>
      </section>

      {error ? <p className="notice">{error}</p> : null}
      <main className="venue-layout">
        <section className="venue-list" aria-label="Venues">
          {venues.length === 0 ? <p className="empty-state">No matching venues.</p> : venues.map((venue) => (
            <button key={venue.id} className={`venue-list-row ${venue.id === selectedId ? 'selected' : ''}`} onClick={() => { setCreating(false); setSelectedId(venue.id); setTab('overview') }}>
              <strong>{venue.venue_name}</strong>
              <span>{[venue.town, venue.municipality].filter(Boolean).join(' · ') || 'Location unknown'}</span>
              <span><span className="pill">{venue.research_status ?? 'discovered'}</span> <span className="pill muted">{venue.confidence_rating ?? 'E'}</span></span>
            </button>
          ))}
        </section>

        <section className="venue-detail">
          {!schema ? <p>Loading schema…</p> : creating || selected ? (
            <>
              <div className="panel-heading">
                <div><p className="eyebrow">{creating ? 'New venue' : selected?.venue_external_id}</p><h2>{creating ? 'Create venue' : selected?.venue_name}</h2></div>
                {!creating && selected ? <button onClick={toggleArchive}>{selected.active ? 'Archive' : 'Restore'}</button> : null}
              </div>
              {!creating ? (
                <nav className="tabs" aria-label="Venue detail">
                  {(['overview', 'contacts', 'documents', 'photos', 'opportunities', 'notes', 'statistics'] as RelatedTab[]).map((name) => (
                    <button key={name} className={tab === name ? 'active' : ''} onClick={() => setTab(name)}>{name}</button>
                  ))}
                </nav>
              ) : null}
              {tab === 'overview' ? (
                <form onSubmit={save} className="venue-form">
                  <nav className="section-nav" aria-label="Venue field groups">
                    {schema.sections.map((section) => <button type="button" key={section} className={activeSection === section ? 'active' : ''} onClick={() => setActiveSection(section)}>{section}</button>)}
                  </nav>
                  <div className="field-grid">
                    {(fieldsBySection.get(activeSection) ?? []).map((field) => (
                      <VenueField
                        key={field.name}
                        field={field}
                        value={form[field.name] ?? ''}
                        disabled={!creating && field.read_only_after_create}
                        onChange={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
                      />
                    ))}
                  </div>
                  {activeSection === 'Address & map' ? (
                    <CoordinatePreview
                      latitude={form.latitude ?? ''}
                      longitude={form.longitude ?? ''}
                      onPick={(latitude, longitude) => setForm((current) => ({
                        ...current, latitude: String(latitude), longitude: String(longitude), geocode_source: 'manual', geocode_precision: 'exact',
                      }))}
                    />
                  ) : null}
                  <button className="primary-action" type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save venue'}</button>
                </form>
              ) : selected ? <RelatedPanel venue={selected} tab={tab} /> : null}
            </>
          ) : <p className="empty-state">Select a venue or create one.</p>}
        </section>
      </main>
    </div>
  )
}

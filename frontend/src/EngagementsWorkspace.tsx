import { FormEvent, useEffect, useState } from 'react'
import {
  createEngagement,
  deleteEngagement,
  findEngagementComparisons,
  findEngagements,
  findOpportunities,
  updateEngagement,
  type ComparisonResponse,
  type Engagement,
  type Opportunity,
} from './api'

type EngagementForm = {
  opportunity_id: string; status: string; commitment_date: string; pitch_number: string
  setup_start_at: string; setup_end_at: string; teardown_start_at: string; teardown_end_at: string
  arrival_plan: string; staffing_notes: string; equipment_notes: string; inventory_notes: string
  travel_notes: string; notes: string; calendar_visibility: boolean; attended: boolean
  revenue_eur: string; costs_eur: string; weather_notes: string; best_selling_items: string
  operational_notes: string; customer_notes: string; rating: string; attend_again: string
  lessons_learned: string
}

const emptyEngagement: EngagementForm = {
  opportunity_id: '', status: 'committed', commitment_date: '', pitch_number: '', setup_start_at: '',
  setup_end_at: '', teardown_start_at: '', teardown_end_at: '', arrival_plan: '', staffing_notes: '',
  equipment_notes: '', inventory_notes: '', travel_notes: '', notes: '', calendar_visibility: true,
  attended: true, revenue_eur: '0', costs_eur: '0', weather_notes: '', best_selling_items: '',
  operational_notes: '', customer_notes: '', rating: '', attend_again: '', lessons_learned: '',
}

const localDateTime = (value: string | null) => value ? value.slice(0, 16) : ''
const nullable = (value: string) => value.trim() || null

function engagementForm(engagement: Engagement): EngagementForm {
  return {
    opportunity_id: String(engagement.opportunity_id), status: engagement.status,
    commitment_date: engagement.commitment_date ?? '', pitch_number: engagement.pitch_number ?? '',
    setup_start_at: localDateTime(engagement.setup_start_at), setup_end_at: localDateTime(engagement.setup_end_at),
    teardown_start_at: localDateTime(engagement.teardown_start_at), teardown_end_at: localDateTime(engagement.teardown_end_at),
    arrival_plan: engagement.arrival_plan ?? '', staffing_notes: engagement.staffing_notes ?? '',
    equipment_notes: engagement.equipment_notes ?? '', inventory_notes: engagement.inventory_notes ?? '',
    travel_notes: engagement.travel_notes ?? '', notes: engagement.notes ?? '', calendar_visibility: engagement.calendar_visibility,
    attended: engagement.attended, revenue_eur: String(engagement.revenue_eur), costs_eur: String(engagement.costs_eur),
    weather_notes: engagement.weather_notes ?? '', best_selling_items: engagement.best_selling_items ?? '',
    operational_notes: engagement.operational_notes ?? '', customer_notes: engagement.customer_notes ?? '',
    rating: engagement.rating ? String(engagement.rating) : '',
    attend_again: engagement.attend_again === null ? '' : String(engagement.attend_again),
    lessons_learned: engagement.lessons_learned ?? '',
  }
}

export default function EngagementsWorkspace() {
  const [engagements, setEngagements] = useState<Engagement[]>([])
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<EngagementForm>(emptyEngagement)
  const [groupBy, setGroupBy] = useState<ComparisonResponse['group_by']>('series')
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const selected = engagements.find((item) => item.id === selectedId) ?? null

  const load = async () => {
    try {
      const [engagementData, opportunityData, comparisonData] = await Promise.all([
        findEngagements(), findOpportunities({ active: true, page_size: 100 }), findEngagementComparisons(groupBy),
      ])
      setEngagements(engagementData._embedded.engagements)
      setOpportunities(opportunityData._embedded.opportunities)
      setComparison(comparisonData)
      setSelectedId((id) => engagementData._embedded.engagements.some((item) => item.id === id) ? id : engagementData._embedded.engagements[0]?.id ?? null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load engagements.')
    }
  }

  useEffect(() => { load() }, [groupBy])
  useEffect(() => {
    if (selected && !creating) setForm(engagementForm(selected))
  }, [selectedId, creating, engagements])

  const payload = () => ({
    ...form, opportunity_id: Number(form.opportunity_id), commitment_date: nullable(form.commitment_date),
    pitch_number: nullable(form.pitch_number), setup_start_at: nullable(form.setup_start_at), setup_end_at: nullable(form.setup_end_at),
    teardown_start_at: nullable(form.teardown_start_at), teardown_end_at: nullable(form.teardown_end_at),
    arrival_plan: nullable(form.arrival_plan), staffing_notes: nullable(form.staffing_notes), equipment_notes: nullable(form.equipment_notes),
    inventory_notes: nullable(form.inventory_notes), travel_notes: nullable(form.travel_notes), notes: nullable(form.notes),
    revenue_eur: Number(form.revenue_eur), costs_eur: Number(form.costs_eur),
    rating: form.rating ? Number(form.rating) : null,
    attend_again: form.attend_again === '' ? null : form.attend_again === 'true',
    weather_notes: nullable(form.weather_notes), best_selling_items: nullable(form.best_selling_items),
    operational_notes: nullable(form.operational_notes), customer_notes: nullable(form.customer_notes),
    lessons_learned: nullable(form.lessons_learned),
  })

  const save = async (event: FormEvent) => {
    event.preventDefault(); setError(null)
    try { await (creating ? createEngagement(payload()) : updateEngagement(selected as Engagement, payload())); setCreating(false); await load() }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save engagement.') }
  }
  const remove = async () => {
    if (!selected || !window.confirm(`Delete the engagement for ${selected.opportunity_name}?`)) return
    await deleteEngagement(selected); setSelectedId(null); await load()
  }
  const updateForm = (key: keyof EngagementForm, value: string | boolean) => setForm((current) => ({ ...current, [key]: value }))

  return <div className="app-shell operations-shell">
    <header className="topbar"><div><p className="eyebrow">Committed appearances</p><h1>Engagements</h1></div>
      <button className="primary-action" onClick={() => { setCreating(true); setSelectedId(null); setForm(emptyEngagement) }}>New engagement</button>
    </header>
    {error ? <p className="notice">{error}</p> : null}
    <main className="workspace">
      <section className="table-panel"><table><thead><tr><th>Opportunity</th><th>Date</th><th>Status</th><th>Pitch</th><th>Profit</th></tr></thead>
        <tbody>{engagements.map((item) => <tr key={item.id} className={item.id === selectedId ? 'selected-row' : ''} onClick={() => { setCreating(false); setSelectedId(item.id) }}>
          <td><strong>{item.opportunity_name}</strong></td><td>{item.event_date ?? ''}</td><td><span className="pill">{item.status}</span></td>
          <td>{item.pitch_number ?? ''}</td><td>{item.status === 'completed' ? `€${item.profit_eur}` : 'Not completed'}</td></tr>)}</tbody></table>
        <section className="comparison-panel"><div className="panel-heading"><h2>Year-over-year</h2><select aria-label="Compare by" value={groupBy} onChange={(event) => setGroupBy(event.target.value as ComparisonResponse['group_by'])}>
          <option value="series">Series</option><option value="venue">Venue</option><option value="organizer">Organizer</option><option value="municipality">Municipality</option></select></div>
          {comparison?.groups.length ? comparison.groups.map((group) => <div key={group.group} className="comparison-group"><strong>{group.group}</strong>{group.years.map((year) => <span key={year.year}>{year.year}: €{year.profit_eur} profit ({year.engagement_count})</span>)}</div>) : <p className="empty-state">Complete an engagement to start comparing years.</p>}
        </section>
      </section>
      <aside className="editor-panel"><div className="panel-heading"><h2>{creating ? 'New engagement' : selected?.opportunity_name ?? 'Engagement detail'}</h2>{selected ? <button className="danger-action" onClick={remove}>Delete</button> : null}</div>
        {(creating || selected) ? <form className="event-form" onSubmit={save}>
          <label>Opportunity<select required disabled={!creating} value={form.opportunity_id} onChange={(event) => updateForm('opportunity_id', event.target.value)}><option value="">Choose an opportunity</option>{opportunities.map((item) => <option key={item.id} value={item.id}>{item.name}{item.event_date ? ` — ${item.event_date}` : ''}</option>)}</select></label>
          <div className="form-grid"><label>Status<select value={form.status} onChange={(event) => updateForm('status', event.target.value)}><option>committed</option><option>planned</option><option>completed</option><option>cancelled</option><option>no_show</option></select></label><label>Commitment date<input type="date" value={form.commitment_date} onChange={(event) => updateForm('commitment_date', event.target.value)} /></label></div>
          <label>Pitch number<input value={form.pitch_number} onChange={(event) => updateForm('pitch_number', event.target.value)} /></label>
          <div className="form-grid"><label>Setup starts<input type="datetime-local" value={form.setup_start_at} onChange={(event) => updateForm('setup_start_at', event.target.value)} /></label><label>Setup ends<input type="datetime-local" value={form.setup_end_at} onChange={(event) => updateForm('setup_end_at', event.target.value)} /></label></div>
          <div className="form-grid"><label>Teardown starts<input type="datetime-local" value={form.teardown_start_at} onChange={(event) => updateForm('teardown_start_at', event.target.value)} /></label><label>Teardown ends<input type="datetime-local" value={form.teardown_end_at} onChange={(event) => updateForm('teardown_end_at', event.target.value)} /></label></div>
          {(['arrival_plan', 'staffing_notes', 'equipment_notes', 'inventory_notes', 'travel_notes', 'notes'] as const).map((key) => <label key={key}>{key.replace(/_/g, ' ')}<textarea rows={2} value={form[key]} onChange={(event) => updateForm(key, event.target.value)} /></label>)}
          <label className="checkbox-label"><input type="checkbox" checked={form.calendar_visibility} onChange={(event) => updateForm('calendar_visibility', event.target.checked)} />Show in calendars</label>
          <section className="outcome-form"><h3>Actuals</h3>
            <label className="checkbox-label"><input type="checkbox" checked={form.attended} onChange={(event) => updateForm('attended', event.target.checked)} />Attended</label>
            <div className="form-grid"><label>Revenue €<input type="number" min="0" step="0.01" value={form.revenue_eur} onChange={(event) => updateForm('revenue_eur', event.target.value)} /></label><label>Costs €<input type="number" min="0" step="0.01" value={form.costs_eur} onChange={(event) => updateForm('costs_eur', event.target.value)} /></label></div>
            <p className="calculated-profit">Calculated profit: €{(Number(form.revenue_eur || 0) - Number(form.costs_eur || 0)).toFixed(2)}</p>
            <div className="form-grid"><label>Rating<select value={form.rating} onChange={(event) => updateForm('rating', event.target.value)}><option value="">Not rated</option>{[1,2,3,4,5].map((rating) => <option key={rating}>{rating}</option>)}</select></label><label>Attend again?<select value={form.attend_again} onChange={(event) => updateForm('attend_again', event.target.value)}><option value="">Undecided</option><option value="true">Yes</option><option value="false">No</option></select></label></div>
            {(['weather_notes', 'best_selling_items', 'operational_notes', 'customer_notes', 'lessons_learned'] as const).map((key) => <label key={key}>{key.replace(/_/g, ' ')}<textarea rows={2} value={form[key]} onChange={(event) => updateForm(key, event.target.value)} /></label>)}
          </section>
          <button className="primary-action" type="submit">Save engagement</button>
        </form> : <p className="empty-state">Select an engagement or create one.</p>}
      </aside>
    </main>
  </div>
}

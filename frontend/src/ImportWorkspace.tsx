import { FormEvent, useEffect, useState } from 'react'

type PreviewRow = {
  row: number
  external_id: string
  venue_name: string
  action: string
  changes: Record<string, { before: unknown; after: unknown }>
  warnings: string[]
  duplicate_candidates?: { id: number; venue_name: string; score: number; signals: string[] }[]
}

type RelatedPreviewRow = { file: string; row: number; external_id: string; venue_external_id: string; action: string; changes: Record<string, { before: unknown; after: unknown }> }
type Preview = {
  preview_token: string
  filename: string
  rows: PreviewRow[]
  related?: Record<string, RelatedPreviewRow[]>
  errors: { file?: string; row: number; field: string; message: string }[]
}

const API_BASE = '/api'

type ImportHistory = { id: number; filename: string; created: number; updated: number; unchanged: number; skipped: number; completed_at: string }

export default function ImportWorkspace() {
  const [file, setFile] = useState<File | null>(null)
  const [contactsFile, setContactsFile] = useState<File | null>(null)
  const [documentsFile, setDocumentsFile] = useState<File | null>(null)
  const [aliasesFile, setAliasesFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<Preview | null>(null)
  const [resolutions, setResolutions] = useState<Record<string, Record<string, string>>>({})
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [history, setHistory] = useState<ImportHistory[]>([])

  const loadHistory = () => fetch(`${API_BASE}/venue-imports`).then((response) => response.ok ? response.json() : []).then((rows) => setHistory(rows as ImportHistory[])).catch(() => undefined)
  useEffect(() => { void loadHistory() }, [])

  const upload = async (event: FormEvent) => {
    event.preventDefault()
    if (!file) return
    setBusy(true)
    setMessage('')
    const body = new FormData()
    body.append('venues_file', file)
    if (contactsFile) body.append('contacts_file', contactsFile)
    if (documentsFile) body.append('documents_file', documentsFile)
    if (aliasesFile) body.append('aliases_file', aliasesFile)
    try {
      const response = await fetch(`${API_BASE}/venue-imports/preview`, { method: 'POST', body })
      const result = await response.json()
      if (!response.ok) throw new Error(JSON.stringify(result.detail))
      setPreview(result as Preview)
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Unable to preview this file.')
    } finally {
      setBusy(false)
    }
  }

  const apply = async () => {
    if (!preview) return
    setBusy(true)
    setMessage('')
    try {
      const response = await fetch(`${API_BASE}/venue-imports/apply`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preview_token: preview.preview_token, resolutions }),
      })
      const result = await response.json() as { batch_id?: number; counts?: Record<string, number>; detail?: unknown }
      if (!response.ok) throw new Error(JSON.stringify(result.detail))
      setMessage(`Import applied: ${JSON.stringify(result.counts)}`)
      setPreview(null)
      setFile(null)
      await loadHistory()
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Unable to apply this import.')
    } finally {
      setBusy(false)
    }
  }

  const resolve = (row: number, resolution: Record<string, string>) => setResolutions((current) => ({ ...current, [String(row)]: resolution }))
  const unresolvedRows = preview?.rows.filter(
    (row) => ['blocked_duplicate', 'blocked_confidence'].includes(row.action) && !resolutions[String(row.row)],
  ) ?? []
  const canApply = Boolean(preview) && !busy && preview!.errors.length === 0 && unresolvedRows.length === 0
  const applyLabel = busy
    ? 'Applying…'
    : preview?.errors.length
      ? `Fix ${preview.errors.length} error${preview.errors.length === 1 ? '' : 's'} before applying`
      : unresolvedRows.length
        ? `Resolve ${unresolvedRows.length} row${unresolvedRows.length === 1 ? '' : 's'} before applying`
        : 'Apply reviewed batch'

  return (
    <main className="import-workspace">
      <section className="import-intro">
        <p className="eyebrow">Human-reviewed batch workflow</p>
        <h2>Venue research import</h2>
        <p>Start with templates for new research, or export current records for a refresh. Give those files to ChatGPT and upload the returned CSV files below.</p>
        <div className="research-file-options">
          <article>
            <h3>New research batch</h3>
            <p>The complete kit contains instructions, examples, and templates for venues, contacts, documents, and aliases.</p>
            <a className="button-link primary-action" href={`${API_BASE}/venues/import-kit.zip`}>Download complete research kit</a>
          </article>
          <article>
            <h3>Update existing research</h3>
            <p>Export current records with their stable IDs. Give ChatGPT the venue export and only the related exports you want refreshed.</p>
            <div className="export-links">
              <a className="button-link" href={`${API_BASE}/venues/export.csv`}>Export venues</a>
              <a className="button-link" href={`${API_BASE}/venue-imports/export/contacts.csv`}>Export contacts</a>
              <a className="button-link" href={`${API_BASE}/venue-imports/export/documents.csv`}>Export documents</a>
              <a className="button-link" href={`${API_BASE}/venue-imports/export/aliases.csv`}>Export aliases</a>
            </div>
          </article>
        </div>
      </section>
      <form className="upload-card" onSubmit={upload}>
        <div className="primary-upload">
          <div>
            <h3>Upload venues</h3>
            <p>This is the only file required for a normal venue import.</p>
          </div>
          <label>Venue CSV<input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] ?? null)} required /></label>
        </div>
        <details className="companion-uploads">
          <summary>Optional companion CSVs</summary>
          <p>Use these only when ChatGPT returned the matching companion files from the kit or updated related-record exports.</p>
          <div className="upload-fields">
            <label>Contacts CSV<input type="file" accept=".csv,text/csv" onChange={(event) => setContactsFile(event.target.files?.[0] ?? null)} /></label>
            <label>Documents CSV<input type="file" accept=".csv,text/csv" onChange={(event) => setDocumentsFile(event.target.files?.[0] ?? null)} /></label>
            <label>Aliases CSV<input type="file" accept=".csv,text/csv" onChange={(event) => setAliasesFile(event.target.files?.[0] ?? null)} /></label>
          </div>
        </details>
        <button className="primary-action" disabled={busy || !file}>{busy ? 'Reading…' : 'Preview import'}</button>
      </form>
      {message ? <p className="notice">{message}</p> : null}
      {preview ? (
        <section className="preview-panel">
          <div className="panel-heading">
            <div><p className="eyebrow">Zero-write preview</p><h2>{preview.filename}</h2></div>
            <div className="apply-import-action">
              <button type="button" className="primary-action" disabled={!canApply} onClick={apply}>{applyLabel}</button>
              {!canApply && !busy ? <small>The button will enable when every issue shown below is resolved.</small> : null}
            </div>
          </div>
          {preview.errors.map((error, index) => <p className="validation-error" key={index}>{error.file ? `${error.file}, ` : ''}row {error.row}, {error.field}: {error.message}</p>)}
          <div className="preview-table-wrap"><table className="preview-table"><thead><tr><th>Row</th><th>Venue</th><th>Action</th><th>Changes / resolution</th></tr></thead><tbody>
            {preview.rows.map((row) => (
              <tr key={row.row}><td>{row.row}</td><td><strong>{row.venue_name}</strong><br /><small>{row.external_id}</small></td><td><span className={`pill action-${row.action}`}>{row.action.replace(/_/g, ' ')}</span></td><td>
                {Object.entries(row.changes).map(([field, change]) => <div className="field-diff" key={field}><strong>{field.replace(/_/g, ' ')}</strong>: <del>{String(change.before ?? 'unknown')}</del> → <ins>{String(change.after ?? 'unknown')}</ins></div>)}
                {row.action === 'blocked_confidence' ? <div className="resolution"><button type="button" aria-pressed={resolutions[String(row.row)]?.action === 'skip'} onClick={() => resolve(row.row, { action: 'skip' })}>Skip</button><button type="button" aria-pressed={resolutions[String(row.row)]?.action === 'override'} onClick={() => resolve(row.row, { action: 'override', reason: 'Reviewed during import' })}>Approve override</button></div> : null}
                {row.action === 'blocked_duplicate' ? <div className="resolution">
                  <button type="button" aria-pressed={resolutions[String(row.row)]?.action === 'skip'} onClick={() => resolve(row.row, { action: 'skip' })}>Skip</button>
                  {row.duplicate_candidates?.map((candidate) => <button type="button" aria-pressed={resolutions[String(row.row)]?.venue_id === String(candidate.id)} key={candidate.id} onClick={() => resolve(row.row, { action: 'map', venue_id: String(candidate.id) })}>Map to {candidate.venue_name} ({candidate.score})</button>)}
                  <button type="button" aria-pressed={resolutions[String(row.row)]?.action === 'create_distinct'} onClick={() => resolve(row.row, { action: 'create_distinct', reason: 'Reviewed as distinct' })}>Create as distinct</button>
                </div> : null}
                {resolutions[String(row.row)] ? <p className="resolution-selected">Selected: {resolutions[String(row.row)].action.replace(/_/g, ' ')}</p> : null}
              </td></tr>
            ))}
          </tbody></table></div>
          {Object.entries(preview.related ?? {}).map(([kind, rows]) => (
            <section className="related-import-preview" key={kind}>
              <h3>{kind}</h3>
              {rows.map((row) => <p key={`${kind}-${row.row}`}><span className="pill">{row.action}</span> {row.external_id} → {row.venue_external_id}</p>)}
            </section>
          ))}
        </section>
      ) : null}
      <section className="preview-panel import-history">
        <div className="panel-heading"><h2>Import history</h2></div>
        {history.length === 0 ? <p className="empty-state">No applied venue imports yet.</p> : history.map((item) => (
          <article className="history-row" key={item.id}>
            <div><strong>{item.filename}</strong><br /><small>{new Date(item.completed_at).toLocaleString()}</small></div>
            <span>{item.created} created · {item.updated} updated · {item.unchanged} unchanged · {item.skipped} skipped</span>
            <a className="button-link" href={`${API_BASE}/venue-imports/${item.id}/report.csv`}>Download report</a>
          </article>
        ))}
      </section>
    </main>
  )
}

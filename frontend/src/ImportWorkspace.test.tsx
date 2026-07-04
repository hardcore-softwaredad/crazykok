import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ImportWorkspace from './ImportWorkspace'


describe('venue import workspace', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('previews a CSV and sends the reviewed apply request', async () => {
    vi.stubGlobal('FormData', class { append() {} })
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      const body = url.endsWith('/venue-imports')
        ? []
        : url.endsWith('/venue-imports/apply')
          ? { batch_id: 1, counts: { created: 1, updated: 0, unchanged: 0, skipped: 0 } }
          : {
        preview_token: 'preview-1', filename: 'venues.csv', errors: [],
        rows: [{ row: 2, external_id: 'VEN-1', venue_name: 'Town Square', action: 'create', changes: {}, warnings: [] }],
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response)
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    render(<ImportWorkspace />)

    expect(screen.getByRole('link', { name: 'Download complete research kit' })).toHaveAttribute('href', '/api/venues/import-kit.zip')
    expect(screen.getByRole('link', { name: 'Export venues' })).toHaveAttribute('href', '/api/venues/export.csv')
    expect(screen.getByRole('link', { name: 'Export contacts' })).toHaveAttribute('href', '/api/venue-imports/export/contacts.csv')

    await user.upload(screen.getByLabelText('Venue CSV'), new File(['venue_external_id,venue_name\nVEN-1,Town Square'], 'venues.csv', { type: 'text/csv' }))
    fireEvent.submit(screen.getByRole('button', { name: 'Preview import' }).closest('form') as HTMLFormElement)

    expect(await screen.findByText('Zero-write preview')).toBeInTheDocument()
    expect(screen.getByText('Town Square')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Apply reviewed batch' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/api/venue-imports/apply', expect.objectContaining({ method: 'POST' })))
    expect(await screen.findByText(/Import applied/)).toBeInTheDocument()
  })

  it('explains why apply is disabled and enables it after resolving a row', async () => {
    vi.stubGlobal('FormData', class { append() {} })
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => Promise.resolve({
      ok: true,
      json: () => Promise.resolve(String(input).endsWith('/venue-imports') ? [] : {
        preview_token: 'preview-2', filename: 'venues.csv', errors: [],
        rows: [{ row: 2, external_id: 'VEN-1', venue_name: 'Town Square', action: 'blocked_confidence', changes: {}, warnings: ['Lower confidence'] }],
      }),
    } as Response)))
    const user = userEvent.setup()
    render(<ImportWorkspace />)
    await user.upload(screen.getByLabelText('Venue CSV'), new File(['venue_external_id,venue_name\nVEN-1,Town Square'], 'venues.csv', { type: 'text/csv' }))
    fireEvent.submit(screen.getByRole('button', { name: 'Preview import' }).closest('form') as HTMLFormElement)

    expect(await screen.findByRole('button', { name: 'Resolve 1 row before applying' })).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Approve override' }))
    expect(screen.getByRole('button', { name: 'Approve override' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Apply reviewed batch' })).toBeEnabled()
  })
})

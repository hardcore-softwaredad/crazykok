import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import VenueWorkspace from './VenueWorkspace'


const schema = {
  schema_version: 1,
  sections: ['Identity', 'Access & parking'],
  fields: [
    { name: 'venue_external_id', label: 'Venue External Id', type: 'string', section: 'Identity', required: true, read_only_after_create: true, enum: [] },
    { name: 'venue_name', label: 'Venue Name', type: 'string', section: 'Identity', required: true, read_only_after_create: false, enum: [] },
    { name: 'active', label: 'Active', type: 'boolean', section: 'Identity', required: false, read_only_after_create: false, enum: [] },
    { name: 'parking_available', label: 'Parking Available', type: 'enum', section: 'Access & parking', required: false, read_only_after_create: false, enum: ['yes', 'no', 'limited', 'unknown'] },
  ],
}

const venue = {
  id: 1,
  venue_external_id: 'VEN-NL-DR-ASSEN-TEST',
  venue_name: 'Test Square',
  town: 'Assen',
  municipality: 'Assen',
  research_status: 'researched',
  confidence_rating: 'B',
  active: true,
  parking_available: 'limited',
}

function jsonResponse(value: unknown, mediaType = 'application/json') {
  return Promise.resolve(new Response(JSON.stringify(value), {
    status: 200,
    headers: { 'Content-Type': mediaType },
  }))
}

function apiRoot() {
  return jsonResponse({
    version: '1',
    _links: {
      'venue-search': {
        href: '/api/v1/venues{?q,research_status,active,page_size}',
        templated: true,
      },
    },
  }, 'application/hal+json')
}

function venueCollection(venues: typeof venue[]) {
  return jsonResponse({
    _links: { self: { href: '/api/v1/venues' } },
    page: { number: 1, size: 100, total_elements: venues.length, total_pages: venues.length ? 1 : 0 },
    _embedded: { venues },
  }, 'application/hal+json')
}

describe('venue workspace', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('loads venues and maps semantic enums to controls in the React client', async () => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url === '/api/v1') return apiRoot()
      if (url.endsWith('/venues/schema')) return jsonResponse(schema)
      if (url.includes('/v1/venues?')) return venueCollection([venue])
      return jsonResponse([])
    }))

    const user = userEvent.setup()
    render(<VenueWorkspace />)

    expect(await screen.findByRole('heading', { name: 'Test Square' })).toBeInTheDocument()
    expect(screen.getByLabelText('Venue External Id')).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Access & parking' }))
    expect(screen.getByRole('combobox', { name: 'Parking Available' })).toHaveValue('limited')
  })

  it('creates a venue through the API using generated semantic fields', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url === '/api/v1') return apiRoot()
      if (url.endsWith('/venues/schema')) return jsonResponse(schema)
      if (url.includes('/v1/venues?')) return venueCollection([])
      if (url.endsWith('/venues') && init?.method === 'POST') return jsonResponse(venue)
      return jsonResponse([])
    })
    vi.stubGlobal('fetch', fetchMock)

    const user = userEvent.setup()
    render(<VenueWorkspace />)
    await screen.findByText('No matching venues.')
    await user.click(screen.getByRole('button', { name: 'New venue' }))
    await user.type(screen.getByLabelText('Venue External Id'), venue.venue_external_id)
    await user.type(screen.getByLabelText('Venue Name'), venue.venue_name)
    await user.click(screen.getByRole('button', { name: 'Save venue' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/api/venues', expect.objectContaining({ method: 'POST' })))
  })
})

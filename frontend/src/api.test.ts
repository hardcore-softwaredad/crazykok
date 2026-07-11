import { beforeEach, expect, test, vi } from 'vitest'

import { findOpportunities, updateOpportunity, type Opportunity } from './api'


const halResponse = (body: unknown) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/hal+json' },
  })


beforeEach(() => {
  vi.restoreAllMocks()
})


test('discovers search and follows the returned resource self link', async () => {
  const opportunity: Opportunity = {
    id: 42,
    name: 'Linked market',
    description: null,
    location: 'Assen',
    event_date: null,
    application_deadline: null,
    organizer: null,
    category: null,
    application_status: 'watchlist',
    source_url: null,
    notes: null,
    expected_revenue: null,
    expected_attendance: null,
    is_active: true,
    venue_id: null,
    series_name: null,
    _links: {
      self: { href: 'https://api.example.test/v1/opportunities/by-stable-link' },
      collection: { href: 'https://api.example.test/v1/opportunities' },
    },
  }
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(halResponse({
      version: '1',
      _links: {
        self: { href: 'https://api.example.test/v1' },
        opportunities: { href: 'https://api.example.test/v1/opportunities' },
        'opportunity-search': {
          href: 'https://api.example.test/v1/opportunities{?q,status,page,page_size}',
          templated: true,
        },
      },
    }))
    .mockResolvedValueOnce(halResponse({
      _links: { self: { href: 'https://api.example.test/v1/opportunities?q=market' } },
      page: { number: 1, size: 25, total_elements: 1, total_pages: 1 },
      _embedded: { opportunities: [opportunity] },
    }))
    .mockResolvedValueOnce(halResponse({ ...opportunity, application_status: 'applied' }))
  vi.stubGlobal('fetch', fetchMock)

  const collection = await findOpportunities({ q: 'market' })
  await updateOpportunity(collection._embedded.opportunities[0], { application_status: 'applied' })

  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    'https://api.example.test/v1/opportunities?q=market',
    expect.objectContaining({ headers: expect.objectContaining({ Accept: 'application/hal+json' }) }),
  )
  expect(fetchMock).toHaveBeenNthCalledWith(
    3,
    opportunity._links.self.href,
    expect.objectContaining({ method: 'PATCH' }),
  )
})

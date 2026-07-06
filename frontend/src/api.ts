export type HalLink = {
  href: string
  templated?: boolean
}

export type HalLinks = Record<string, HalLink>

export type PageMetadata = {
  number: number
  size: number
  total_elements: number
  total_pages: number
}

export type Opportunity = {
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
  profit_score?: number | null
  is_active: boolean
  venue_id: number | null
  _links: HalLinks
}

export type OpportunityCollection = {
  _links: HalLinks
  page: PageMetadata
  _embedded: { opportunities: Opportunity[] }
}

export type Venue = Record<string, unknown> & {
  id: number
  venue_external_id: string
  venue_name: string
  town: string | null
  municipality: string | null
  venue_category_primary: string | null
  research_status: string | null
  confidence_rating: string | null
  active: boolean
  _links: HalLinks
}

export type VenueCollection = {
  _links: HalLinks
  page: PageMetadata
  _embedded: { venues: Venue[] }
}

export type PlanningOperation = {
  id: number
  status: string
  commitment_date: string | null
  _links: HalLinks
}

export type PlanningOpportunity = {
  id: number
  name: string
  event_date: string | null
  application_deadline: string | null
  application_status: string
  profit_score: number | null
  distance_km: number | null
  venue?: {
    id: number
    name: string
    latitude: number | null
    longitude: number | null
  }
  operations: PlanningOperation[]
  _links: HalLinks
}

export type PlanningResponse = {
  opportunities: PlanningOpportunity[]
  warnings: {
    code: 'missing_coordinates' | 'missing_date'
    opportunity_id: number
    title: string
  }[]
  _links: HalLinks
}

type ApiRoot = {
  version: string
  _links: HalLinks
}

type Problem = {
  detail?: string
  title?: string
}

const HAL_ACCEPT = 'application/hal+json'
const API_ROOT = '/api/v1'
const allowedApiOrigins = new Set([window.location.origin])
let rootPromise: Promise<ApiRoot> | null = null

async function request<T>(href: string, init?: RequestInit): Promise<T> {
  const target = new URL(href, window.location.origin)
  if (!allowedApiOrigins.has(target.origin)) {
    throw new Error('The API returned a link to an untrusted origin')
  }
  const response = await fetch(href, {
    ...init,
    headers: {
      Accept: HAL_ACCEPT,
      ...init?.headers,
    },
  })
  if (!response.ok) {
    const problem = (await response.json().catch(() => ({}))) as Problem
    throw new Error(problem.detail ?? problem.title ?? `API request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  if (!response.headers.get('content-type')?.includes(HAL_ACCEPT)) {
    throw new Error('The API returned an unsupported representation')
  }
  return (await response.json()) as T
}

function apiRoot(): Promise<ApiRoot> {
  rootPromise ??= request<ApiRoot>(API_ROOT).then((root) => {
    Object.values(root._links).forEach((link) => {
      const concretePart = link.href.split('{', 1)[0]
      allowedApiOrigins.add(new URL(concretePart, window.location.origin).origin)
    })
    return root
  }).catch((error: unknown) => {
    rootPromise = null
    throw error
  })
  return rootPromise
}

function expandQueryTemplate(link: HalLink, values: Record<string, string | number | boolean | undefined>) {
  if (!link.templated) return link.href
  const match = link.href.match(/\{\?([^}]+)\}$/)
  if (!match) throw new Error('Unsupported API URI template')
  const allowed = new Set(match[1].split(','))
  const url = new URL(link.href.slice(0, match.index), window.location.origin)
  Object.entries(values).forEach(([key, value]) => {
    if (allowed.has(key) && value !== undefined && value !== '') {
      url.searchParams.set(key, String(value))
    }
  })
  return url.toString()
}

export async function findOpportunities(
  filters: Record<string, string | number | boolean | undefined>,
): Promise<OpportunityCollection> {
  const root = await apiRoot()
  return request<OpportunityCollection>(expandQueryTemplate(root._links['opportunity-search'], filters))
}

export function followOpportunityPage(href: string): Promise<OpportunityCollection> {
  return request<OpportunityCollection>(href)
}

export async function findVenues(
  filters: Record<string, string | number | boolean | undefined>,
): Promise<VenueCollection> {
  const root = await apiRoot()
  return request<VenueCollection>(expandQueryTemplate(root._links['venue-search'], filters))
}

export async function createOpportunity(payload: unknown): Promise<Opportunity> {
  const root = await apiRoot()
  return request<Opportunity>(root._links.opportunities.href, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateOpportunity(opportunity: Opportunity, payload: unknown): Promise<Opportunity> {
  return request<Opportunity>(opportunity._links.self.href, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function deleteOpportunity(opportunity: Opportunity): Promise<void> {
  return request<void>(opportunity._links.self.href, { method: 'DELETE' })
}

export async function findPlanning(
  filters: Record<string, string | number | boolean | undefined>,
): Promise<PlanningResponse> {
  const root = await apiRoot()
  return request<PlanningResponse>(expandQueryTemplate(root._links.planning, filters))
}

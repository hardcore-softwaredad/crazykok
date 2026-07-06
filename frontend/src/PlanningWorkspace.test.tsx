import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import PlanningWorkspace from './PlanningWorkspace'
import { findPlanning } from './api'


vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return { ...actual, findPlanning: vi.fn() }
})

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  CircleMarker: ({ children, eventHandlers }: { children: React.ReactNode; eventHandlers: { click: () => void } }) => <div role="button" tabIndex={0} onClick={eventHandlers.click}>{children}</div>,
  Popup: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useMap: () => ({ setView: vi.fn(), fitBounds: vi.fn() }),
}))

vi.mock('@fullcalendar/react', () => ({
  default: ({ events, eventClick }: { events: Array<{ id: string; title: string; extendedProps: unknown }>; eventClick: (info: { event: { extendedProps: unknown } }) => void }) => (
    <div data-testid="calendar">
      {events.map((event) => <button key={event.id} onClick={() => eventClick({ event: { extendedProps: event.extendedProps } })}>{event.title}</button>)}
    </div>
  ),
}))

const opportunity = {
  id: 7,
  name: 'Summer market',
  event_date: '2026-08-20',
  application_deadline: '2026-07-20',
  application_status: 'accepted',
  profit_score: 84,
  distance_km: 31.4,
  venue: { id: 3, name: 'Market square', latitude: 52.9, longitude: 6.5 },
  operations: [{
    id: 11,
    status: 'committed',
    commitment_date: '2026-07-05',
    _links: { self: { href: 'http://localhost/api/v1/operations/11' } },
  }],
  _links: { self: { href: 'http://localhost/api/v1/opportunities/7' } },
}

describe('PlanningWorkspace', () => {
  beforeEach(() => {
    vi.mocked(findPlanning).mockResolvedValue({
      opportunities: [opportunity],
      warnings: [
        { code: 'missing_coordinates', opportunity_id: 8, title: 'Research lead' },
        { code: 'missing_date', opportunity_id: 8, title: 'Research lead' },
      ],
      _links: { self: { href: 'http://localhost/api/v1/planning' } },
    })
  })

  it('shows map records, data warnings, filters, and selected detail', async () => {
    render(<PlanningWorkspace />)

    expect(await screen.findByText(/opportunity has no map coordinates/i)).toBeInTheDocument()
    fireEvent.click(screen.getByText('Summer market'))
    expect(screen.getByRole('heading', { name: 'Summer market' })).toBeInTheDocument()
    expect(screen.getByText('31.4 km straight-line')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Within'), { target: { value: '40' } })
    await waitFor(() => expect(findPlanning).toHaveBeenLastCalledWith(expect.objectContaining({ max_distance_km: '40' })))
  })

  it('renders deadlines and committed operations in the calendar with operation click-through', async () => {
    render(<PlanningWorkspace />)
    await screen.findByTestId('map')
    fireEvent.click(screen.getByRole('button', { name: 'Calendar' }))

    expect(screen.getByRole('button', { name: 'Deadline · Summer market' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Committed · Summer market' }))
    expect(screen.getByRole('link', { name: 'Open operation detail' })).toHaveAttribute(
      'href',
      'http://localhost/api/v1/operations/11',
    )
  })
})

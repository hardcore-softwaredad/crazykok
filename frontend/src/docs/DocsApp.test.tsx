import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import DocsApp from './DocsApp'


describe('decision log application', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/')
    window.scrollTo = vi.fn()
  })

  afterEach(() => vi.unstubAllGlobals())

  it('lists generated ADRs and searches their body and metadata', async () => {
    const user = userEvent.setup()
    window.history.replaceState({}, '', '/decisions')
    render(<DocsApp />)

    expect(screen.getByRole('heading', { name: 'Decision Log' })).toBeInTheDocument()
    expect(screen.getByText(/\d+ decisions/)).toBeInTheDocument()
    await user.type(screen.getByRole('searchbox', { name: 'Search decisions' }), 'filesystem gatekeeper')
    expect(screen.getByText('1 decision')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Use A Filesystem-Backed Decision Log/i })).toBeInTheDocument()
  })

  it('offers decisions and the interactive API from the docs portal', () => {
    render(<DocsApp />)
    expect(screen.getByRole('heading', { name: 'Project Docs' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Browse decisions/ })).toHaveAttribute('href', '/decisions')
    expect(screen.getByRole('link', { name: /Open API reference/ })).toHaveAttribute('href', '/api-reference')
  })

  it('renders a direct ADR route with adjacent navigation', () => {
    window.history.replaceState({}, '', '/adr/filesystem-backed-decision-log')
    render(<DocsApp />)

    expect(screen.getByRole('heading', { name: 'Use A Filesystem-Backed Decision Log', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Adjacent decisions' })).toBeInTheDocument()
    expect(screen.getByText(/Keep ADR Markdown files/)).toBeInTheDocument()
  })

  it('resolves ADR resources to published asset paths', () => {
    window.history.replaceState({}, '', '/adr/self-hosted-authentication-service')
    render(<DocsApp />)

    expect(screen.getByRole('img', { name: 'Authentication surface map' })).toHaveAttribute(
      'src',
      '/adr-assets/0031-self-hosted-authentication-service/auth-surface-map.svg',
    )
    expect(screen.getByRole('img', { name: 'Machine-to-machine API authentication sequence' })).toHaveAttribute(
      'src',
      '/adr-assets/0031-self-hosted-authentication-service/service-to-service-auth-sequence.svg',
    )
    expect(screen.getByRole('link', { name: 'Deployment authentication setup' })).toHaveAttribute(
      'href',
      '/document/doc-assets/DEPLOYMENT.md#authentication-setup',
    )
  })

  it('renders a linked Markdown document inside the docs application', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, text: () => Promise.resolve('# Deployment\n\n## Authentication setup\n\nRead the [Trail request](requests/2026-07-13-trail-input-capture.md).\n\n| Very wide field | Description |\n| --- | --- |\n| `AUTHENTICATION_CONFIGURATION_WITH_A_LONG_NAME` | Scroll instead of overflowing the page. |') })))
    window.history.replaceState({}, '', '/document/doc-assets/DEPLOYMENT.md')
    render(<DocsApp />)

    expect(await screen.findByRole('heading', { name: 'Deployment', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Authentication setup', level: 2 })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Trail request' })).toHaveAttribute('href', '/document/doc-assets/requests/2026-07-13-trail-input-capture.md')
    expect(screen.getByRole('table').parentElement).toHaveClass('table-scroll')
  })

  it('shows a useful not-found view', () => {
    window.history.replaceState({}, '', '/adr/not-real')
    render(<DocsApp />)
    expect(screen.getByRole('heading', { name: 'Decision not found' })).toBeInTheDocument()
  })
})

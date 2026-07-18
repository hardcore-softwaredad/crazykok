const nativeFetch = window.fetch.bind(window)
const explorer = document.querySelector('#hal-explorer')
const actions = document.querySelector('#hal-actions')
const result = document.querySelector('#hal-result')
const source = document.querySelector('#hal-source')

function linkEntries(links) {
  return Object.entries(links || {}).flatMap(([relation, value]) =>
    (Array.isArray(value) ? value : [value]).map((link) => ({ relation, ...link })),
  )
}

async function follow(link) {
  result.textContent = 'Loading…'
  try {
    const response = await nativeFetch(link.href, { headers: { Accept: 'application/hal+json' } })
    const payload = await response.json()
    result.textContent = JSON.stringify(payload, null, 2)
    if (response.ok && payload?._links) showLinks(link.href, payload._links)
  } catch (error) {
    result.textContent = `Request failed: ${error.message}`
  }
}

function showLinks(url, links) {
  const entries = linkEntries(links)
  if (!entries.length) return
  source.textContent = url
  actions.replaceChildren()
  for (const link of entries) {
    const button = document.createElement('button')
    button.type = 'button'
    button.textContent = link.templated ? `${link.relation} · template` : `GET · ${link.relation}`
    button.title = link.href
    button.disabled = Boolean(link.templated)
    if (!link.templated) button.addEventListener('click', () => follow(link))
    actions.append(button)
  }
  explorer.hidden = false
}

// Observe responses made by Scalar's client without coupling the explorer to
// Scalar internals. The extension survives renderer upgrades or replacement.
window.fetch = async (...args) => {
  const response = await nativeFetch(...args)
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/hal+json')) {
    response.clone().json().then((payload) => {
      if (payload?._links) showLinks(response.url, payload._links)
    }).catch(() => {})
  }
  return response
}

document.querySelector('#hal-close').addEventListener('click', () => { explorer.hidden = true })

Scalar.createApiReference('#app', {
  url: '/openapi.json',
  theme: 'none',
  layout: 'modern',
  defaultHttpClient: { targetKey: 'shell', clientKey: 'curl' },
  hideModels: false,
  hideDownloadButton: false,
  metaData: { title: 'Crazy Kok API Reference' },
  customCss: `
    :root { --scalar-color-accent: #a54a2c; --scalar-font: Inter, ui-sans-serif, system-ui, sans-serif; }
    .dark-mode { --scalar-color-accent: #f1a33c; }
  `,
})

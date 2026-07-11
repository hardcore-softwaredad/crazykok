import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { createRequire } from 'node:module'

const root = path.resolve(import.meta.dirname, '..')
const require = createRequire(path.join(root, 'frontend', 'package.json'))
const yaml = require('js-yaml')
const directory = path.join(root, 'docs', 'adr')

const classifications = {
  '0001': ['process', ['adr', 'documentation'], ['decision record', 'architecture history']],
  '0002': ['architecture', ['local-first', 'privacy'], ['offline application', 'local backend']],
  '0003': ['data', ['database', 'sqlite'], ['relational storage', 'primary database']],
  '0004': ['backend', ['api', 'fastapi'], ['Python API', 'web backend']],
  '0005': ['frontend', ['react', 'typescript'], ['browser application', 'Vite']],
  '0006': ['data', ['data-model', 'normalization'], ['relational model', 'database design']],
  '0007': ['domain', ['opportunity', 'opportunity-series'], ['dated vendor chance', 'recurring opportunity']],
  '0008': ['data', ['documents', 'local-storage'], ['vendor documents', 'file metadata']],
  '0009': ['data', ['csv', 'portability'], ['import export', 'spreadsheet']],
  '0010': ['process', ['milestones', 'planning'], ['release planning', 'semantic versioning']],
  '0011': ['product', ['distance', 'schoonebeek'], ['home base', 'travel origin']],
  '0012': ['data', ['provenance', 'research'], ['source tracking', 'data audit']],
  '0013': ['product', ['confidence', 'uncertainty'], ['estimated values', 'unknown values']],
  '0014': ['data', ['alembic', 'migrations'], ['schema migration', 'database evolution']],
  '0015': ['backend', ['services', 'thin-routes'], ['service layer', 'route handler']],
  '0016': ['security', ['authentication', 'local-first'], ['single user', 'access control']],
  '0017': ['product', ['research', 'scraping'], ['data collection', 'manual entry']],
  '0018': ['process', ['business-logic', 'testing'], ['automated tests', 'quality assurance']],
  '0019': ['process', ['ai-agents', 'documentation'], ['coding agent rules', 'documentation compliance']],
  '0020': ['product', ['local-first', 'portability'], ['private tool', 'single user']],
  '0021': ['frontend', ['calendar', 'map'], ['planning views', 'Leaflet', 'FullCalendar']],
  '0022': ['domain', ['application', 'engagement', 'opportunity'], ['domain language', 'event terminology', 'trading terminology']],
  '0023': ['domain', ['engagement', 'opportunity'], ['committed work', 'discovery record']],
  '0024': ['architecture', ['calendar', 'ics'], ['iCalendar feed', 'calendar subscription']],
  '0025': ['product', ['commerce', 'scope'], ['inventory', 'point of sale', 'orders']],
  '0026': ['domain', ['location', 'venue'], ['venue management', 'geocoding', 'address']],
}

for (const filename of fs.readdirSync(directory).filter((name) => /^\d{4}-.+\.md$/.test(name)).sort()) {
  const fullPath = path.join(directory, filename)
  const source = fs.readFileSync(fullPath, 'utf8')
  if (source.startsWith('---\n')) continue

  const fileMatch = filename.match(/^(\d{4})-(.+)\.md$/)
  const headingMatch = source.match(/^# ADR (\d{4}): (.+)$/m)
  const statusMatch = source.match(/^- Status: (.+)$/m)
  const dateMatch = source.match(/^- Date: (\d{4}-\d{2}-\d{2})$/m)
  if (!fileMatch || !headingMatch || !statusMatch || !dateMatch) {
    throw new Error(`Cannot migrate malformed ADR: ${filename}`)
  }
  const [category, tags, keywords] = classifications[fileMatch[1]] ?? ['architecture', ['adr'], []]
  const metadata = {
    schema_version: 1,
    id: fileMatch[1],
    slug: fileMatch[2],
    title: headingMatch[2],
    status: statusMatch[1].toLowerCase(),
    date: dateMatch[1],
    category,
    tags: [...tags].sort(),
    keywords,
    supersedes: [],
    superseded_by: [],
  }
  const body = source
    .replace(/\n- Status: .+\n- Date: \d{4}-\d{2}-\d{2}\n/, '\n')
    .trim()
  const frontMatter = yaml.dump(metadata, { lineWidth: -1, noRefs: true, quotingType: '"', forceQuotes: false }).trim()
  fs.writeFileSync(fullPath, `---\n${frontMatter}\n---\n\n${body}\n`)
}

console.log('ADR migration complete')

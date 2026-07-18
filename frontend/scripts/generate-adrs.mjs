import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import * as yaml from 'js-yaml'

const frontendRoot = path.resolve(import.meta.dirname, '..')
const sourceDirectory = process.env.ADR_SOURCE_DIR
  ? path.resolve(process.env.ADR_SOURCE_DIR)
  : path.resolve(frontendRoot, '..', 'docs', 'adr')
const docsSourceDirectory = path.dirname(sourceDirectory)
const outputFile = path.resolve(frontendRoot, 'src', 'docs', 'generated', 'adrs.json')
const assetSourceDirectory = path.join(sourceDirectory, 'assets')
const assetOutputDirectory = path.resolve(frontendRoot, 'public', 'adr-assets')
const docsOutputDirectory = path.resolve(frontendRoot, 'public', 'doc-assets')
const statuses = new Set(['proposed', 'accepted', 'rejected', 'deprecated', 'superseded'])
const categories = new Set(['architecture', 'backend', 'data', 'deployment', 'domain', 'frontend', 'process', 'product', 'security'])
const requiredSections = ['Context', 'Decision', 'Consequences', 'Alternatives Considered', 'Review Trigger']
const expectedKeys = new Set(['schema_version', 'id', 'slug', 'title', 'status', 'date', 'category', 'tags', 'keywords', 'supersedes', 'superseded_by'])

function fail(filename, message) {
  throw new Error(`${filename}: ${message}`)
}

function plainText(markdown) {
  return markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/[*_>~-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function parse(filename) {
  const source = fs.readFileSync(path.join(sourceDirectory, filename), 'utf8')
  if (!source.startsWith('---\n')) fail(filename, 'missing YAML front matter')
  const end = source.indexOf('\n---\n', 4)
  if (end < 0) fail(filename, 'unterminated YAML front matter')
  const metadata = yaml.load(source.slice(4, end))
  const markdown = source.slice(end + 5).trim()
  if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) fail(filename, 'front matter must be a mapping')
  const unknown = Object.keys(metadata).filter((key) => !expectedKeys.has(key))
  const missing = [...expectedKeys].filter((key) => !(key in metadata))
  if (unknown.length) fail(filename, `unknown metadata: ${unknown.join(', ')}`)
  if (missing.length) fail(filename, `missing metadata: ${missing.join(', ')}`)
  const match = filename.match(/^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$/)
  if (!match) fail(filename, 'filename must be NNNN-kebab-case.md')
  const heading = markdown.match(/^# ADR (\d{4}): (.+)$/m)
  if (!heading) fail(filename, 'missing canonical H1')
  const id = String(metadata.id).padStart(4, '0')
  if (id !== match[1] || id !== heading[1]) fail(filename, 'filename, metadata, and H1 IDs must agree')
  if (metadata.slug !== match[2]) fail(filename, 'filename and metadata slugs must agree')
  if (metadata.title !== heading[2]) fail(filename, 'metadata and H1 titles must agree')
  if (metadata.schema_version !== 1) fail(filename, 'unsupported schema_version')
  if (!statuses.has(metadata.status)) fail(filename, 'invalid status')
  if (!categories.has(metadata.category)) fail(filename, 'invalid category')
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(metadata.date))) fail(filename, 'date must use YYYY-MM-DD')
  if (!Array.isArray(metadata.tags) || metadata.tags.length === 0) fail(filename, 'at least one tag is required')
  if (metadata.tags.some((tag) => !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(tag))) fail(filename, 'tags must use lower-case kebab-case')
  if (!Array.isArray(metadata.keywords) || !Array.isArray(metadata.supersedes) || !Array.isArray(metadata.superseded_by)) fail(filename, 'keywords and relationships must be arrays')
  if (/<\/?[A-Za-z][^>]*>/.test(markdown)) fail(filename, 'raw HTML is not allowed')
  const headings = [...markdown.matchAll(/^## (.+)$/gm)].map((entry) => entry[1])
  for (const section of requiredSections) if (!headings.includes(section)) fail(filename, `missing section: ${section}`)
  if (new Set(headings).size !== headings.length) fail(filename, 'duplicate H2 section')
  return {
    schemaVersion: metadata.schema_version,
    id,
    slug: metadata.slug,
    title: metadata.title,
    status: metadata.status,
    date: String(metadata.date),
    category: metadata.category,
    tags: metadata.tags,
    keywords: metadata.keywords,
    supersedes: metadata.supersedes,
    supersededBy: metadata.superseded_by,
    markdown,
    searchText: plainText(`${id} ${metadata.title} ${metadata.status} ${metadata.category} ${metadata.tags.join(' ')} ${metadata.keywords.join(' ')} ${markdown}`),
    sourcePath: `docs/adr/${filename}`,
  }
}

const filenames = fs.readdirSync(sourceDirectory).filter((filename) => filename.endsWith('.md')).sort()
const records = filenames.map(parse)
for (const field of ['id', 'slug']) {
  const values = records.map((record) => record[field])
  if (new Set(values).size !== values.length) throw new Error(`Duplicate ADR ${field}`)
}
const ids = new Set(records.map((record) => record.id))
for (const record of records) {
  for (const related of [...record.supersedes, ...record.supersededBy]) {
    if (!ids.has(related)) fail(record.sourcePath, `relationship references missing ADR ${related}`)
    if (related === record.id) fail(record.sourcePath, 'ADR cannot reference itself')
  }
}
records.sort((left, right) => left.id.localeCompare(right.id))
fs.mkdirSync(path.dirname(outputFile), { recursive: true })
fs.writeFileSync(outputFile, `${JSON.stringify(records, null, 2)}\n`)
if (fs.existsSync(assetSourceDirectory)) {
  fs.rmSync(assetOutputDirectory, { recursive: true, force: true })
  fs.cpSync(assetSourceDirectory, assetOutputDirectory, {
    recursive: true,
    filter: (source) => !source.endsWith('.mmd'),
  })
}
if (fs.existsSync(docsSourceDirectory)) {
  fs.rmSync(docsOutputDirectory, { recursive: true, force: true })
  fs.mkdirSync(docsOutputDirectory, { recursive: true })
  for (const entry of fs.readdirSync(docsSourceDirectory, { withFileTypes: true })) {
    if (entry.name === 'adr') continue
    fs.cpSync(path.join(docsSourceDirectory, entry.name), path.join(docsOutputDirectory, entry.name), { recursive: true })
  }
}
console.log(`Generated ${records.length} ADR records at ${outputFile}`)

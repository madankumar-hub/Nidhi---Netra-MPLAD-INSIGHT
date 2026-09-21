/**
 * CSV bulk import for sanctioned works (FR15).
 *
 * The backend has accepted batches since the first release; this is the
 * operator-facing half. Parsing happens in the browser so the reviewer can see
 * exactly what will be sent and fix a malformed file before anything reaches
 * the database - the API still validates every row server-side.
 */
import { useMemo, useState } from 'react'
import type { ChangeEvent } from 'react'
import { FileUp, Upload } from 'lucide-react'
import { projectsAdminApi } from '@/api'
import { useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { InlineMessage } from '@/components/ui/States'
import type { ProjectCreatePayload } from '@/types'

/** Columns the API requires. Everything else in the file is optional. */
const REQUIRED_COLUMNS = [
  'title',
  'mp_name',
  'state',
  'district',
  'category',
  'executing_agency',
  'sanction_year',
  'allocated_amount',
] as const

const NUMERIC_COLUMNS = new Set([
  'sanction_year',
  'allocated_amount',
  'spent_amount',
  'estimated_cost',
  'progress_percent',
  'planned_progress_percent',
  'beneficiaries',
  'latitude',
  'longitude',
])

interface ParseResult {
  rows: ProjectCreatePayload[]
  errors: string[]
  headers: string[]
}

/**
 * Split one CSV line, honouring quoted fields containing commas.
 * Deliberately small: MPLAD extracts are plain comma-separated exports, and a
 * parser dependency is not worth it for one screen.
 */
function splitCsvLine(line: string): string[] {
  const cells: string[] = []
  let current = ''
  let inQuotes = false

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index]
    if (char === '"') {
      if (inQuotes && line[index + 1] === '"') {
        current += '"'
        index += 1
      } else {
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      cells.push(current)
      current = ''
    } else {
      current += char
    }
  }
  cells.push(current)
  return cells.map((cell) => cell.trim())
}

function parseCsv(text: string): ParseResult {
  const errors: string[] = []
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)

  if (lines.length < 2) {
    return { rows: [], errors: ['The file needs a header row and at least one data row.'], headers: [] }
  }

  const headers = splitCsvLine(lines[0]).map((header) => header.toLowerCase())
  const missing = REQUIRED_COLUMNS.filter((column) => !headers.includes(column))
  if (missing.length > 0) {
    return { rows: [], errors: [`Missing required column(s): ${missing.join(', ')}`], headers }
  }

  const rows: ProjectCreatePayload[] = []
  lines.slice(1).forEach((line, index) => {
    const lineNumber = index + 2
    const cells = splitCsvLine(line)
    if (cells.length !== headers.length) {
      errors.push(`Row ${lineNumber}: expected ${headers.length} columns, found ${cells.length}.`)
      return
    }

    const record: Record<string, string | number> = {}
    let rowFailed = false

    headers.forEach((header, position) => {
      const raw = cells[position]
      if (raw === '') return

      if (NUMERIC_COLUMNS.has(header)) {
        const value = Number(raw)
        if (!Number.isFinite(value)) {
          errors.push(`Row ${lineNumber}: "${header}" must be a number, found "${raw}".`)
          rowFailed = true
          return
        }
        record[header] = value
      } else {
        record[header] = raw
      }
    })

    if (!rowFailed) rows.push(record as unknown as ProjectCreatePayload)
  })

  return { rows, errors, headers }
}

interface BulkImportDialogProps {
  open: boolean
  onClose: () => void
  onImported: () => void
}

export function BulkImportDialog({ open, onClose, onImported }: BulkImportDialogProps) {
  const { t } = useI18n()
  const [fileName, setFileName] = useState<string | null>(null)
  const [parsed, setParsed] = useState<ParseResult | null>(null)
  const [readError, setReadError] = useState<string | null>(null)

  const importRows = useMutation(projectsAdminApi.bulkImport)

  const sampleHeader = useMemo(() => REQUIRED_COLUMNS.join(','), [])

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const input = event.target as unknown as { files?: FileList | null }
    const file = input.files?.[0]
    setReadError(null)
    setParsed(null)
    if (!file) {
      setFileName(null)
      return
    }
    setFileName(file.name)
    try {
      const text = await file.text()
      setParsed(parseCsv(text))
    } catch {
      setReadError(t('import.readFailed'))
    }
  }

  const submit = async () => {
    if (!parsed || parsed.rows.length === 0) return
    const result = await importRows.run(parsed.rows)
    if (result) {
      onImported()
      onClose()
      setParsed(null)
      setFileName(null)
    }
  }

  const canSubmit = (parsed?.rows.length ?? 0) > 0 && !importRows.pending

  return (
    <Modal open={open} title={t('import.title')} onClose={onClose} size="lg">
      <div className="space-y-4">
        <p className="text-sm text-ink-700">{t('import.description')}</p>

        <div className="rounded border border-ink-200 bg-ink-50 p-3">
          <p className="data-label">{t('import.requiredColumns')}</p>
          <code className="mt-1 block overflow-x-auto whitespace-pre text-xs text-ink-800">
            {sampleHeader}
          </code>
        </div>

        <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded border border-dashed border-ink-300 bg-white px-4 py-8 text-center hover:border-ink-500 hover:bg-ink-50">
          <FileUp className="h-7 w-7 text-ink-400" aria-hidden />
          <span className="text-sm font-medium text-ink-800">
            {fileName ?? t('import.chooseFile')}
          </span>
          <span className="text-xs text-ink-500">{t('import.chooseHint')}</span>
          <input type="file" accept=".csv,text/csv" className="sr-only" onChange={handleFile} />
        </label>

        {readError ? <InlineMessage tone="warning">{readError}</InlineMessage> : null}

        {parsed ? (
          <div className="space-y-3">
            <InlineMessage tone={parsed.rows.length > 0 ? 'success' : 'warning'}>
              {parsed.rows.length.toLocaleString('en-IN')} {t('import.rowsReady')}
              {parsed.errors.length > 0
                ? ` · ${parsed.errors.length.toLocaleString('en-IN')} ${t('import.rowsSkipped')}`
                : ''}
            </InlineMessage>

            {parsed.errors.length > 0 ? (
              <div className="max-h-40 overflow-y-auto rounded border border-saffron-300 bg-saffron-50 p-3">
                <ul className="space-y-1 text-xs text-ink-800">
                  {parsed.errors.slice(0, 20).map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
                {parsed.errors.length > 20 ? (
                  <p className="mt-2 text-xs text-ink-600">
                    +{parsed.errors.length - 20} {t('import.moreErrors')}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

        {importRows.error ? (
          <InlineMessage tone="warning">{importRows.error.message}</InlineMessage>
        ) : null}
      </div>

      <div className="mt-6 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          {t('common.cancel')}
        </Button>
        <Button
          onClick={submit}
          disabled={!canSubmit}
          loading={importRows.pending}
          icon={<Upload className="h-4 w-4" aria-hidden />}
        >
          {t('import.submit')}
        </Button>
      </div>
    </Modal>
  )
}

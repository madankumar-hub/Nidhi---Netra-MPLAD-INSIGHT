import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useI18n } from '@/i18n'
import type { EnumFamily } from '@/i18n'
import { ChartFrame, ChartTable } from './ChartFrame'
import { ChartTooltip } from './tooltip'
import { formatLakh, formatNumber, formatPercent, formatPeriod } from '@/utils/format'
import {
  CHART_INK,
  RISK_COLORS,
  REVIEW_STATUS_COLORS,
  SEQUENTIAL_BLUE,
  SERIES,
  STATUS_COLORS,
  STATUS_PALETTE,
} from '@/utils/constants'
import type {
  KeyValueAmount,
  KeyValueCount,
  ProgressPoint,
  ProjectStatus,
  RiskLevel,
  TimelinePoint,
  TrendPoint,
} from '@/types'

const AXIS_PROPS = {
  stroke: CHART_INK.axis,
  tick: { fill: CHART_INK.muted, fontSize: 11 },
  tickLine: false,
} as const

const GRID = <CartesianGrid stroke={CHART_INK.grid} strokeDasharray="3 3" vertical={false} />

const LEGEND_STYLE = { fontSize: 12, color: CHART_INK.secondary, paddingTop: 8 }

const lakh = (value: number) => formatLakh(value)
const pct = (value: number) => formatPercent(value)
const count = (value: number) => formatNumber(value)

// ---------------------------------------------------------------------------
// Funds: allocated vs spent over time (two series, one axis, same unit)
// ---------------------------------------------------------------------------
export function SpendingTimelineChart({
  data,
  title,
  emptyLabel,
  labels,
}: {
  data: TimelinePoint[]
  title: string
  emptyLabel: string
  labels: { spent: string; allocated: string }
}) {
  const rows = data.map((point) => ({
    period: formatPeriod(point.period),
    spent: point.spent,
    cumulative: point.cumulative_spent,
  }))
  return (
    <ChartFrame
      title={title}
      hasData={rows.length > 0}
      emptyLabel={emptyLabel}
      tableView={
        <ChartTable
          head={['Period', labels.spent, 'Cumulative']}
          rows={rows.map((r) => [r.period, formatLakh(r.spent), formatLakh(r.cumulative)])}
        />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 4 }}>
          <defs>
            <linearGradient id="cumulativeFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={SERIES.allocated} stopOpacity={0.24} />
              <stop offset="100%" stopColor={SERIES.allocated} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          {GRID}
          <XAxis dataKey="period" {...AXIS_PROPS} />
          <YAxis {...AXIS_PROPS} width={62} tickFormatter={(v: number) => `₹${v}L`} />
          <Tooltip content={<ChartTooltip formatter={lakh} />} cursor={{ stroke: CHART_INK.axis }} />
          <Legend wrapperStyle={LEGEND_STYLE} />
          <Area
            type="monotone"
            dataKey="cumulative"
            name="Cumulative expenditure"
            stroke={SERIES.allocated}
            strokeWidth={2}
            fill="url(#cumulativeFill)"
            dot={{ r: 3, strokeWidth: 0, fill: SERIES.allocated }}
            activeDot={{ r: 5, stroke: '#ffffff', strokeWidth: 2 }}
          />
          <Line
            type="monotone"
            dataKey="spent"
            name={labels.spent}
            stroke={SERIES.spent}
            strokeWidth={2}
            dot={{ r: 3, strokeWidth: 0, fill: SERIES.spent }}
            activeDot={{ r: 5, stroke: '#ffffff', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}

// ---------------------------------------------------------------------------
// Progress: actual vs planned (two series, percentage axis)
// ---------------------------------------------------------------------------
export function ProgressTimelineChart({
  data,
  title,
  emptyLabel,
  labels,
}: {
  data: ProgressPoint[]
  title: string
  emptyLabel: string
  labels: { actual: string; planned: string }
}) {
  const rows = data.map((point) => ({
    period: formatPeriod(point.period),
    actual: point.actual,
    planned: point.planned ?? null,
  }))
  const hasPlanned = rows.some((row) => row.planned !== null)
  return (
    <ChartFrame
      title={title}
      hasData={rows.length > 0}
      emptyLabel={emptyLabel}
      tableView={
        <ChartTable
          head={['Period', labels.actual, labels.planned]}
          rows={rows.map((r) => [
            r.period,
            formatPercent(r.actual),
            r.planned === null ? '—' : formatPercent(r.planned),
          ])}
        />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          {GRID}
          <XAxis dataKey="period" {...AXIS_PROPS} />
          <YAxis {...AXIS_PROPS} width={44} domain={[0, 100]} tickFormatter={(v: number) => `${v}%`} />
          <Tooltip content={<ChartTooltip formatter={pct} />} cursor={{ stroke: CHART_INK.axis }} />
          {hasPlanned ? <Legend wrapperStyle={LEGEND_STYLE} /> : null}
          <Line
            type="monotone"
            dataKey="actual"
            name={labels.actual}
            stroke={SERIES.actual}
            strokeWidth={2}
            dot={{ r: 3, strokeWidth: 0, fill: SERIES.actual }}
            activeDot={{ r: 5, stroke: '#ffffff', strokeWidth: 2 }}
          />
          {hasPlanned ? (
            <Line
              type="monotone"
              dataKey="planned"
              name={labels.planned}
              stroke={SERIES.planned}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
            />
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}

// ---------------------------------------------------------------------------
// Utilisation: spent vs remaining (two slices, direct-labelled)
// ---------------------------------------------------------------------------
export function UtilizationDonut({
  allocated,
  spent,
  title,
  labels,
}: {
  allocated: number
  spent: number
  title: string
  labels: { spent: string; remaining: string }
}) {
  const { t } = useI18n()
  const remaining = Math.max(allocated - spent, 0)
  const rows = [
    { name: labels.spent, value: Number(spent.toFixed(2)), color: SERIES.spent },
    { name: labels.remaining, value: Number(remaining.toFixed(2)), color: '#c3c2b7' },
  ]
  const utilisation = allocated > 0 ? (spent / allocated) * 100 : 0
  return (
    <ChartFrame
      title={title}
      hasData={allocated > 0}
      emptyLabel={t('chart.noAllocation')}
      tableView={
        <ChartTable
          head={[t('chart.slice'), t('chart.amount')]}
          rows={rows.map((r) => [r.name, formatLakh(r.value)])}
        />
      }
    >
      <div className="relative h-full w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={rows}
              dataKey="value"
              nameKey="name"
              innerRadius="62%"
              outerRadius="88%"
              paddingAngle={2}
              stroke="#ffffff"
              strokeWidth={2}
            >
              {rows.map((row) => (
                <Cell key={row.name} fill={row.color} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip formatter={lakh} />} />
            <Legend wrapperStyle={LEGEND_STYLE} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center pb-6">
          <span className="text-2xl font-semibold text-ink-900">{utilisation.toFixed(1)}%</span>
          <span className="text-[11px] uppercase tracking-wide text-ink-500">
            {t('chart.utilisedCaption')}
          </span>
        </div>
      </div>
    </ChartFrame>
  )
}

// ---------------------------------------------------------------------------
// Allocated vs spent by dimension (two series, one axis)
// ---------------------------------------------------------------------------
export function AllocationByDimensionChart({
  data,
  title,
  emptyLabel,
  labels,
  height = 320,
  horizontal = true,
  family,
}: {
  data: KeyValueAmount[]
  title: string
  emptyLabel: string
  labels: { allocated: string; spent: string }
  height?: number
  horizontal?: boolean
  /** Controlled vocabulary the labels belong to, so Hindi mode translates them. */
  family?: EnumFamily
}) {
  const { t, tEnum } = useI18n()
  // Translate first, then truncate - truncating English and translating the
  // stub would produce nonsense, and Devanagari is wider than Latin.
  const display = (label: string) => (family ? tEnum(family, label) : label)
  const rows = data.map((row) => {
    const shown = display(row.label)
    return {
      label: shown.length > 28 ? `${shown.slice(0, 27)}…` : shown,
      fullLabel: shown,
      allocated: row.allocated,
      spent: row.spent,
    }
  })
  return (
    <ChartFrame
      title={title}
      hasData={rows.length > 0}
      emptyLabel={emptyLabel}
      height={height}
      tableView={
        <ChartTable
          head={[
            t('chart.group'),
            labels.allocated,
            labels.spent,
            t('chart.utilisationColumn'),
          ]}
          rows={data.map((r) => [
            display(r.label),
            formatLakh(r.allocated),
            formatLakh(r.spent),
            formatPercent(r.utilization_percent),
          ])}
        />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          layout={horizontal ? 'vertical' : 'horizontal'}
          margin={{ top: 8, right: 12, bottom: 0, left: horizontal ? 8 : 0 }}
          barGap={2}
        >
          <CartesianGrid
            stroke={CHART_INK.grid}
            strokeDasharray="3 3"
            horizontal={!horizontal}
            vertical={horizontal}
          />
          {horizontal ? (
            <>
              <XAxis type="number" {...AXIS_PROPS} tickFormatter={(v: number) => `₹${v}L`} />
              <YAxis type="category" dataKey="label" width={150} {...AXIS_PROPS} />
            </>
          ) : (
            <>
              <XAxis dataKey="label" {...AXIS_PROPS} interval={0} angle={-25} textAnchor="end" height={70} />
              <YAxis {...AXIS_PROPS} width={62} tickFormatter={(v: number) => `₹${v}L`} />
            </>
          )}
          <Tooltip
            content={<ChartTooltip formatter={lakh} />}
            cursor={{ fill: 'rgba(11,11,11,0.04)' }}
          />
          <Legend wrapperStyle={LEGEND_STYLE} />
          <Bar dataKey="allocated" name={labels.allocated} fill={SERIES.allocated} radius={[0, 4, 4, 0]} />
          <Bar dataKey="spent" name={labels.spent} fill={SERIES.spent} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}

// ---------------------------------------------------------------------------
// Single-series magnitude (counts). One hue, light to dark by rank.
// ---------------------------------------------------------------------------
export function CountBarChart({
  data,
  title,
  emptyLabel,
  seriesLabel,
  height = 280,
  horizontal = false,
  family,
}: {
  data: KeyValueCount[]
  title: string
  emptyLabel: string
  seriesLabel: string
  height?: number
  horizontal?: boolean
  /** Controlled vocabulary the labels belong to, so Hindi mode translates them. */
  family?: EnumFamily
}) {
  const { t, tEnum } = useI18n()
  const display = (label: string) => (family ? tEnum(family, label) : label)
  const rows = data.map((row) => {
    const shown = display(row.label)
    return { label: shown.length > 30 ? `${shown.slice(0, 29)}…` : shown, value: row.value }
  })
  return (
    <ChartFrame
      title={title}
      hasData={rows.some((row) => row.value > 0)}
      emptyLabel={emptyLabel}
      height={height}
      tableView={
        <ChartTable
          head={[t('chart.group'), seriesLabel]}
          rows={data.map((r) => [display(r.label), r.value])}
        />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          layout={horizontal ? 'vertical' : 'horizontal'}
          margin={{ top: 8, right: 16, bottom: 0, left: horizontal ? 8 : 0 }}
        >
          <CartesianGrid
            stroke={CHART_INK.grid}
            strokeDasharray="3 3"
            horizontal={!horizontal}
            vertical={horizontal}
          />
          {horizontal ? (
            <>
              <XAxis type="number" {...AXIS_PROPS} allowDecimals={false} />
              <YAxis type="category" dataKey="label" width={170} {...AXIS_PROPS} />
            </>
          ) : (
            <>
              <XAxis dataKey="label" {...AXIS_PROPS} interval={0} angle={-20} textAnchor="end" height={64} />
              <YAxis {...AXIS_PROPS} width={44} allowDecimals={false} />
            </>
          )}
          <Tooltip content={<ChartTooltip formatter={count} />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
          <Bar dataKey="value" name={seriesLabel} radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}>
            {rows.map((row, index) => (
              <Cell
                key={row.label}
                fill={SEQUENTIAL_BLUE[Math.min(index + 2, SEQUENTIAL_BLUE.length - 1)]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}

// ---------------------------------------------------------------------------
// State distributions (status colours + legend, never colour alone)
// ---------------------------------------------------------------------------
function colourForState(label: string): string {
  if (label in STATUS_COLORS) return STATUS_COLORS[label as ProjectStatus]
  if (label in REVIEW_STATUS_COLORS) return REVIEW_STATUS_COLORS[label]
  if (label in RISK_COLORS) return RISK_COLORS[label as RiskLevel]
  return STATUS_PALETTE.neutral
}

export function StateDonutChart({
  data,
  title,
  emptyLabel,
  height = 280,
}: {
  data: KeyValueCount[]
  title: string
  emptyLabel: string
  height?: number
}) {
  const { t, tEnum } = useI18n()
  // The raw label drives the status colour lookup, so it is kept on the row and
  // only the rendered text is translated. Translating in place would silently
  // fall through to the neutral colour in Hindi.
  const rows = data
    .filter((row) => row.value > 0)
    .map((row) => ({ ...row, rawLabel: row.label, label: tEnum('projectStatus', row.label) }))
  const total = rows.reduce((sum, row) => sum + row.value, 0)
  return (
    <ChartFrame
      title={title}
      hasData={rows.length > 0}
      emptyLabel={emptyLabel}
      height={height}
      tableView={
        <ChartTable
          head={[t('chart.stateColumn'), t('chart.works'), t('chart.share')]}
          rows={rows.map((r) => [
            r.label,
            r.value,
            total ? `${((r.value / total) * 100).toFixed(1)}%` : '—',
          ])}
        />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={rows}
            dataKey="value"
            nameKey="label"
            innerRadius="55%"
            outerRadius="85%"
            paddingAngle={2}
            stroke="#ffffff"
            strokeWidth={2}
          >
            {rows.map((row) => (
              <Cell key={row.rawLabel} fill={colourForState(row.rawLabel)} />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip formatter={count} />} />
          <Legend wrapperStyle={LEGEND_STYLE} />
        </PieChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}

export function StateBarChart({
  data,
  title,
  emptyLabel,
  seriesLabel,
  height = 280,
  family = 'projectStatus',
}: {
  data: KeyValueCount[]
  title: string
  emptyLabel: string
  seriesLabel: string
  height?: number
  /** Which vocabulary the state labels come from - statuses, review states or
   *  risk levels all land here and each has its own map. */
  family?: EnumFamily
}) {
  const { t, tEnum } = useI18n()
  // As in the donut: the raw label picks the colour, the translated one is what
  // the axis and the table show.
  const rows = data.map((row) => ({
    ...row,
    rawLabel: row.label,
    label: tEnum(family, row.label),
  }))
  return (
    <ChartFrame
      title={title}
      hasData={rows.some((row) => row.value > 0)}
      emptyLabel={emptyLabel}
      height={height}
      tableView={
        <ChartTable
          head={[t('chart.stateColumn'), seriesLabel]}
          rows={rows.map((r) => [r.label, r.value])}
        />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
          {GRID}
          <XAxis dataKey="label" {...AXIS_PROPS} interval={0} angle={-20} textAnchor="end" height={64} />
          <YAxis {...AXIS_PROPS} width={44} allowDecimals={false} />
          <Tooltip content={<ChartTooltip formatter={count} />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
          <Bar dataKey="value" name={seriesLabel} radius={[4, 4, 0, 0]}>
            {rows.map((row) => (
              <Cell key={row.rawLabel} fill={colourForState(row.rawLabel)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}

// ---------------------------------------------------------------------------
// Trends (two series, one axis, same unit)
// ---------------------------------------------------------------------------
export function TrendChart({
  data,
  title,
  emptyLabel,
  labels,
  height = 300,
  formatPeriodLabel = false,
}: {
  data: TrendPoint[]
  title: string
  emptyLabel: string
  labels: { allocated: string; spent: string }
  height?: number
  formatPeriodLabel?: boolean
}) {
  const rows = data.map((point) => ({
    period: formatPeriodLabel ? formatPeriod(point.period) : point.period,
    allocated: point.allocated,
    spent: point.spent,
  }))
  return (
    <ChartFrame
      title={title}
      hasData={rows.length > 0}
      emptyLabel={emptyLabel}
      height={height}
      tableView={
        <ChartTable
          head={['Period', labels.allocated, labels.spent]}
          rows={rows.map((r) => [r.period, formatLakh(r.allocated), formatLakh(r.spent)])}
        />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 4 }} barGap={2}>
          {GRID}
          <XAxis dataKey="period" {...AXIS_PROPS} />
          <YAxis {...AXIS_PROPS} width={62} tickFormatter={(v: number) => `₹${v}L`} />
          <Tooltip content={<ChartTooltip formatter={lakh} />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
          <Legend wrapperStyle={LEGEND_STYLE} />
          <Bar dataKey="allocated" name={labels.allocated} fill={SERIES.allocated} radius={[4, 4, 0, 0]} />
          <Bar dataKey="spent" name={labels.spent} fill={SERIES.spent} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}

export { ChartFrame, ChartTable }

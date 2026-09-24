interface LegendItem {
  label: string
  color: string
  radius?: number
  count?: number
}

/** Colour key for the markers. Every colour is paired with a text label. */
export function MapLegend({ title, items }: { title: string; items: LegendItem[] }) {
  return (
    <div className="rounded border border-ink-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-600">{title}</p>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1.5">
        {items.map((item) => {
          const size = Math.round((item.radius ?? 6) * 1.6)
          return (
            <li key={item.label} className="flex items-center gap-1.5 text-sm text-ink-800">
              <span
                aria-hidden
                className="inline-block shrink-0 rounded-full border border-white shadow"
                style={{ width: size, height: size, backgroundColor: item.color }}
              />
              {item.label}
              {item.count !== undefined ? (
                <span className="tabular-nums text-ink-500">({item.count})</span>
              ) : null}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

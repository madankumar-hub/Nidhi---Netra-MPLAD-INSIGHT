import type { ReactNode } from 'react'

export interface TabDefinition {
  id: string
  label: string
  icon?: ReactNode
  badge?: number | string
}

interface TabsProps {
  tabs: TabDefinition[]
  active: string
  onChange: (id: string) => void
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="border-b border-ink-200">
      <div className="-mb-px flex gap-1 overflow-x-auto" role="tablist">
        {tabs.map((tab) => {
          const selected = tab.id === active
          return (
            <button
              key={tab.id}
              role="tab"
              type="button"
              aria-selected={selected}
              onClick={() => onChange(tab.id)}
              className={`tap-target flex shrink-0 items-center gap-2 border-b-2 px-3 py-2.5 text-sm
                font-medium transition-colors ${
                  selected
                    ? 'border-ink-800 text-ink-900'
                    : 'border-transparent text-ink-500 hover:border-ink-300 hover:text-ink-700'
                }`}
            >
              {tab.icon}
              {tab.label}
              {tab.badge !== undefined && tab.badge !== 0 ? (
                <span className="rounded-full bg-ink-100 px-1.5 py-0.5 text-[11px] font-semibold text-ink-700">
                  {tab.badge}
                </span>
              ) : null}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function TabPanel({ id, active, children }: { id: string; active: string; children: ReactNode }) {
  if (id !== active) return null
  return (
    <div role="tabpanel" className="pt-5">
      {children}
    </div>
  )
}

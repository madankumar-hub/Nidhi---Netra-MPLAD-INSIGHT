import type { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return <section className={`surface ${className}`}>{children}</section>
}

interface CardHeaderProps {
  title: ReactNode
  description?: ReactNode
  actions?: ReactNode
  icon?: ReactNode
}

export function CardHeader({ title, description, actions, icon }: CardHeaderProps) {
  return (
    <header className="flex flex-col gap-3 border-b border-ink-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
      <div className="flex items-start gap-3">
        {icon ? <span className="mt-0.5 text-ink-500">{icon}</span> : null}
        <div>
          <h2 className="text-base font-semibold text-ink-900">{title}</h2>
          {description ? <p className="mt-0.5 text-sm text-ink-600">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </header>
  )
}

export function CardBody({ children, className = '' }: CardProps) {
  return <div className={`px-4 py-4 sm:px-5 ${className}`}>{children}</div>
}

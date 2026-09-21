interface SpinnerProps {
  label?: string
  className?: string
}

export function Spinner({ label, className = '' }: SpinnerProps) {
  return (
    <div className={`flex items-center justify-center gap-3 text-sm text-ink-600 ${className}`} role="status">
      <span
        className="h-5 w-5 animate-spin rounded-full border-2 border-ink-300 border-t-ink-700"
        aria-hidden
      />
      {label ? <span>{label}</span> : null}
      <span className="sr-only">Loading</span>
    </div>
  )
}

export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-hidden>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="skeleton h-10 w-full" />
      ))}
    </div>
  )
}

export function SkeletonCards({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-hidden>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="surface p-4">
          <div className="skeleton h-4 w-24" />
          <div className="skeleton mt-3 h-5 w-full" />
          <div className="skeleton mt-2 h-5 w-3/4" />
          <div className="skeleton mt-4 h-2 w-full" />
          <div className="skeleton mt-4 h-8 w-full" />
        </div>
      ))}
    </div>
  )
}

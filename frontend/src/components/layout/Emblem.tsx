/**
 * Placeholder emblem mark. Deliberately an abstract civic motif rather than the
 * State Emblem of India, which may not be reproduced without authorisation.
 */
export function Emblem({ className = 'h-9 w-9' }: { className?: string }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-md bg-white/10 ring-1 ring-white/25 ${className}`}
      aria-hidden
    >
      <svg viewBox="0 0 32 32" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M16 3.5 26.5 9v6.2c0 6.2-4.2 11.6-10.5 13.3C9.7 26.8 5.5 21.4 5.5 15.2V9L16 3.5Z" />
        <path d="M11 16.5h10M13 20h6M16 9.5v4" strokeLinecap="round" />
      </svg>
    </span>
  )
}

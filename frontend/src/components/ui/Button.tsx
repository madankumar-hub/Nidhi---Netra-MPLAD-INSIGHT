import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'accent' | 'onDark'
type Size = 'sm' | 'md'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-ink-800 text-white hover:bg-ink-900 disabled:bg-ink-300',
  secondary: 'border border-ink-300 bg-white text-ink-800 hover:bg-ink-50 disabled:text-ink-400',
  ghost: 'text-ink-700 hover:bg-ink-100 disabled:text-ink-400',
  danger: 'bg-[#8f1d1d] text-white hover:bg-[#751818] disabled:bg-ink-300',
  accent: 'bg-saffron-700 text-white hover:bg-saffron-800 disabled:bg-ink-300',
  // For use on the dark hero band. Defined as its own variant rather than by
  // overriding `secondary` with utility classes: two conflicting background
  // utilities have the same specificity, so which one wins depends on their
  // order in the generated stylesheet - which is how this button ended up
  // white-on-white.
  onDark:
    'border border-white/40 bg-white/5 text-white hover:bg-white/15 hover:border-white/60 ' +
    'disabled:border-white/20 disabled:text-white/40',
}

const SIZES: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: ReactNode
  loading?: boolean
}

export function Button({
  variant = 'primary',
  size = 'md',
  icon,
  loading = false,
  children,
  className = '',
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-md font-medium
        transition-colors disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
    >
      {loading ? (
        <span
          className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
          aria-hidden
        />
      ) : (
        icon
      )}
      {children}
    </button>
  )
}

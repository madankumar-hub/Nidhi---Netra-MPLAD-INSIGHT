/**
 * Minimal React typings for offline type-checking.
 *
 * This is NOT a replacement for @types/react. It exists so `tsc` can verify
 * this repository's own source (imports resolve, hooks are used correctly,
 * no unused locals, props line up) on a machine with no npm registry access.
 * `npm install && npm run build` on a normal machine uses the real typings.
 */
// module: react
export type Key = string | number
export type ReactNode =
  | ReactElement
  | string
  | number
  | boolean
  | null
  | undefined
  | Iterable<ReactNode>

export interface ReactElement {
  type: unknown
  props: unknown
  key: Key | null
}

export interface RefObject<T> {
  readonly current: T | null
}
export interface MutableRefObject<T> {
  current: T
}

export type SetStateAction<S> = S | ((prev: S) => S)
export type Dispatch<A> = (value: A) => void

export function useState<S>(initial: S | (() => S)): [S, Dispatch<SetStateAction<S>>]
export function useState<S = undefined>(): [
  S | undefined,
  Dispatch<SetStateAction<S | undefined>>,
]
export function useEffect(effect: () => void | (() => void), deps?: readonly unknown[]): void
export function useLayoutEffect(effect: () => void | (() => void), deps?: readonly unknown[]): void
export function useMemo<T>(factory: () => T, deps: readonly unknown[]): T
export function useCallback<T extends (...args: never[]) => unknown>(
  callback: T,
  deps: readonly unknown[],
): T
export function useRef<T>(initial: T): MutableRefObject<T>
export function useRef<T>(initial: T | null): RefObject<T>
export function useRef<T = undefined>(): MutableRefObject<T | undefined>
export function useId(): string
export function useContext<T>(context: Context<T>): T
export function useReducer<S, A>(
  reducer: (state: S, action: A) => S,
  initial: S,
): [S, Dispatch<A>]

export interface Provider<T> {
  (props: { value: T; children?: ReactNode }): ReactElement | null
}
export interface Context<T> {
  Provider: Provider<T>
  Consumer: (props: { children: (value: T) => ReactNode }) => ReactElement | null
}
export function createContext<T>(defaultValue: T): Context<T>

export function memo<P>(component: (props: P) => ReactElement | null): (props: P) => ReactElement | null
export function forwardRef<T, P>(
  render: (props: P, ref: RefObject<T>) => ReactElement | null,
): (props: P & { ref?: RefObject<T> }) => ReactElement | null
export const Fragment: unknown
export const StrictMode: (props: { children?: ReactNode }) => ReactElement | null

// --- Events -------------------------------------------------------------
export interface SyntheticEvent<T = Element> {
  target: EventTarget & T
  currentTarget: EventTarget & T
  preventDefault(): void
  stopPropagation(): void
}
export interface FormEvent<T = Element> extends SyntheticEvent<T> {}
export interface ChangeEvent<T = Element> extends SyntheticEvent<T> {
  target: EventTarget & T
}
export interface MouseEvent<T = Element> extends SyntheticEvent<T> {}
export interface KeyboardEvent<T = Element> extends SyntheticEvent<T> {
  key: string
}

// --- Intrinsic element props -------------------------------------------
export interface HTMLAttributes<T> {
  className?: string
  id?: string
  style?: Record<string, string | number>
  title?: string
  role?: string
  tabIndex?: number
  hidden?: boolean
  children?: ReactNode
  onClick?: (event: MouseEvent<T>) => void
  onKeyDown?: (event: KeyboardEvent<T>) => void
  onSubmit?: (event: FormEvent<T>) => void
  onChange?: (event: ChangeEvent<T>) => void
  onFocus?: (event: SyntheticEvent<T>) => void
  onBlur?: (event: SyntheticEvent<T>) => void
  [dataAttr: `data-${string}`]: string | number | boolean | undefined
  [ariaAttr: `aria-${string}`]: string | number | boolean | undefined
}

export interface InputHTMLAttributes<T> extends HTMLAttributes<T> {
  type?: string
  name?: string
  value?: string | number
  defaultValue?: string | number
  checked?: boolean
  placeholder?: string
  required?: boolean
  disabled?: boolean
  readOnly?: boolean
  autoComplete?: string
  autoFocus?: boolean
  inputMode?: 'none' | 'text' | 'decimal' | 'numeric' | 'tel' | 'search' | 'email' | 'url'
  min?: string | number
  max?: string | number
  step?: string | number
  minLength?: number
  maxLength?: number
  pattern?: string
  accept?: string
  multiple?: boolean
}

export interface TextareaHTMLAttributes<T> extends HTMLAttributes<T> {
  name?: string
  value?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
  readOnly?: boolean
  rows?: number
  cols?: number
  minLength?: number
  maxLength?: number
}

export interface SelectHTMLAttributes<T> extends HTMLAttributes<T> {
  name?: string
  value?: string | number
  defaultValue?: string | number
  required?: boolean
  disabled?: boolean
  multiple?: boolean
  size?: number
}

export interface ButtonHTMLAttributes<T> extends HTMLAttributes<T> {
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  name?: string
  value?: string | number
  form?: string
}

export interface AnchorHTMLAttributes<T> extends HTMLAttributes<T> {
  href?: string
  target?: string
  rel?: string
  download?: string | boolean
}

export interface SVGProps<T> extends HTMLAttributes<T> {
  width?: string | number
  height?: string | number
  viewBox?: string
  fill?: string
  stroke?: string
  strokeWidth?: string | number
  strokeLinecap?: string
  strokeLinejoin?: string
  d?: string
  x?: string | number
  y?: string | number
  cx?: string | number
  cy?: string | number
  r?: string | number
  points?: string
  transform?: string
  opacity?: string | number
}

export type ComponentType<P = Record<string, unknown>> = (props: P) => ReactElement | null
export type FC<P = Record<string, unknown>> = ComponentType<P>
export type PropsWithChildren<P = unknown> = P & { children?: ReactNode }

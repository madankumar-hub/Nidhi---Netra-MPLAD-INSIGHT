/** Minimal react-router-dom typings for offline type-checking. */
// module: react-router-dom
import type { ReactElement, ReactNode } from 'react'

export interface NavLinkRenderProps {
  isActive: boolean
  isPending: boolean
}
export interface LinkProps {
  to: string
  replace?: boolean
  state?: unknown
  className?: string
  children?: ReactNode
  title?: string
  target?: string
  rel?: string
  onClick?: (event: unknown) => void
  [ariaAttr: `aria-${string}`]: string | number | boolean | undefined
}
export function Link(props: LinkProps): ReactElement | null
export function NavLink(
  props: Omit<LinkProps, 'className'> & {
    end?: boolean
    className?: string | ((props: NavLinkRenderProps) => string)
    children?: ReactNode | ((props: NavLinkRenderProps) => ReactNode)
  },
): ReactElement | null

export function BrowserRouter(props: { children?: ReactNode; basename?: string }): ReactElement | null
export function Routes(props: { children?: ReactNode }): ReactElement | null
export function Route(props: {
  path?: string
  index?: boolean
  element?: ReactNode
  children?: ReactNode
}): ReactElement | null
export function Navigate(props: { to: string; replace?: boolean; state?: unknown }): ReactElement | null
export function Outlet(): ReactElement | null

export interface Location {
  pathname: string
  search: string
  hash: string
  state: unknown
  key: string
}
export interface NavigateOptions {
  replace?: boolean
  state?: unknown
}
export type NavigateFunction = {
  (to: string, options?: NavigateOptions): void
  (delta: number): void
}
export function useNavigate(): NavigateFunction
export function useLocation(): Location
export function useParams<T extends Record<string, string | undefined> = Record<string, string | undefined>>(): T
export function useSearchParams(): [URLSearchParams, (next: URLSearchParams | Record<string, string>) => void]

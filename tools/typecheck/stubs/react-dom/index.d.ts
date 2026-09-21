/** Minimal react-dom/client typings for offline type-checking. */
// module: react-dom/client
import type { ReactNode } from 'react'
export interface Root {
  render(children: ReactNode): void
  unmount(): void
}
export function createRoot(container: Element | DocumentFragment): Root

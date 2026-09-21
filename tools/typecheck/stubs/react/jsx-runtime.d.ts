/**
 * JSX namespace for offline type-checking.
 *
 * Under `"jsx": "react-jsx"` TypeScript resolves the JSX namespace from the
 * jsxImportSource module (`react/jsx-runtime`), not from the global scope.
 *
 * IntrinsicElements is intentionally permissive: validating the full DOM prop
 * surface is the real @types/react's job. What this offline check is for is
 * catching unresolved imports, unused locals, bad hook usage, our own component
 * prop mismatches, and - most importantly - translation keys that do not exist
 * in the dictionary.
 */
import type { Key, ReactElement, ReactNode } from './index'

export const jsx: (type: unknown, props: unknown, key?: unknown) => ReactElement
export const jsxs: (type: unknown, props: unknown, key?: unknown) => ReactElement
export const Fragment: unknown

export namespace JSX {
  interface Element extends ReactElement {}
  interface ElementClass {
    render(): ReactNode
  }
  interface ElementAttributesProperty {
    props: Record<string, unknown>
  }
  interface ElementChildrenAttribute {
    children: Record<string, unknown>
  }
  interface IntrinsicAttributes {
    key?: Key
  }
  interface IntrinsicElements {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    [elemName: string]: any
  }
}

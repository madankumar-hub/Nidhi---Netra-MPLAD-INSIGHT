/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_DEV_API_TARGET?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

/** Vite handles these imports; declared so `tsc` resolves them too. */
declare module '*.css'
declare module '*.svg' {
  const src: string
  export default src
}

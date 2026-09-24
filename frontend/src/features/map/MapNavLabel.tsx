/**
 * Navigation hooks for the layouts. A component (not a string) so the label
 * follows the language switch without touching the main dictionaries.
 */
import { useMapText } from './mapText'

export { Map as MapNavIcon } from 'lucide-react'

export function MapNavLabel() {
  const tm = useMapText()
  return <>{tm('navLabel')}</>
}

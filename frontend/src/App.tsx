import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/AuthContext'
import { I18nProvider } from '@/i18n'
import { AppRoutes } from '@/routes'

export default function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </I18nProvider>
  )
}

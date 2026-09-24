import { Navigate, Route, Routes } from 'react-router-dom'
import { PublicLayout } from '@/layouts/PublicLayout'
import { AdminLayout } from '@/layouts/AdminLayout'
import { ProtectedRoute } from '@/features/auth/ProtectedRoute'
import { HomePage } from '@/pages/HomePage'
import { ProjectsPage } from '@/pages/ProjectsPage'
import { SchemeDetailPage } from '@/pages/SchemeDetailPage'
import { StatisticsPage } from '@/pages/StatisticsPage'
import { AboutPage } from '@/pages/AboutPage'
import { LoginPage } from '@/pages/LoginPage'
import { SignupPage } from '@/pages/SignupPage'
import { RequestAccessPage } from '@/pages/RequestAccessPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { AdminDashboardPage } from '@/pages/admin/AdminDashboardPage'
import { AdminProjectsPage } from '@/pages/admin/AdminProjectsPage'
import { AdminSchemeDetailPage } from '@/pages/admin/AdminSchemeDetailPage'
import { AdminAnalyticsPage } from '@/pages/admin/AdminAnalyticsPage'
import { AdminFlaggedPage } from '@/pages/admin/AdminFlaggedPage'
import { AdminDelayedPage } from '@/pages/admin/AdminDelayedPage'
import { AdminReviewQueuePage } from '@/pages/admin/AdminReviewQueuePage'
import { AdminCitizenReportsPage } from '@/pages/admin/AdminCitizenReportsPage'
import { AdminActivityPage } from '@/pages/admin/AdminActivityPage'
import { AdminAccessRequestsPage } from '@/pages/admin/AdminAccessRequestsPage'
import { AdminUsersPage } from '@/pages/admin/AdminUsersPage'
import { PublicMapPage } from '@/pages/PublicMapPage'
import { AdminMapPage } from '@/pages/admin/AdminMapPage'

/** Officer, Auditor and Admin may enter the officials' portal. */
const INTERNAL = ['officer', 'auditor', 'admin'] as const

export function AppRoutes() {
  return (
    <Routes>
      {/* ---------------- Citizen portal ---------------- */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/scheme/:id" element={<SchemeDetailPage />} />
        <Route path="/statistics" element={<StatisticsPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/map" element={<PublicMapPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/request-access" element={<RequestAccessPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      {/* ---------------- Officials' portal ---------------- */}
      <Route
        element={
          <ProtectedRoute roles={[...INTERNAL]}>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/admin" element={<AdminDashboardPage />} />
        <Route path="/admin/projects" element={<AdminProjectsPage />} />
        {/* SRS FR7b: the administrative detail page lives at its own route. */}
        <Route path="/admin/scheme/:id" element={<AdminSchemeDetailPage />} />
        <Route path="/admin/projects/:id" element={<AdminSchemeDetailPage />} />
        <Route path="/admin/flagged" element={<AdminFlaggedPage />} />
        <Route path="/admin/delayed" element={<AdminDelayedPage />} />
        <Route path="/admin/reviews" element={<AdminReviewQueuePage />} />
        <Route path="/admin/citizen-reports" element={<AdminCitizenReportsPage />} />
        <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
        <Route path="/admin/map" element={<AdminMapPage />} />
        <Route path="/admin/activity" element={<AdminActivityPage />} />
        {/* Administrator only - granting official roles. */}
        <Route
          path="/admin/access-requests"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminAccessRequestsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminUsersPage />
            </ProtectedRoute>
          }
        />
        <Route path="/admin/*" element={<Navigate to="/admin" replace />} />
      </Route>
    </Routes>
  )
}
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Activity,
  ArrowLeft,
  ClipboardCheck,
  ExternalLink,
  Info,
  IndianRupee,
  ListChecks,
  MessageSquareWarning,
  Pencil,
  Settings2,
  StickyNote,
  TrendingUp,
  TriangleAlert,
} from 'lucide-react'
import { adminApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useAuth } from '@/features/auth/AuthContext'
import { useI18n } from '@/i18n'
import { Badge, ReviewStatusBadge, RiskBadge, StatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { DataGrid, DataRow, StatCard } from '@/components/ui/Metrics'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { Tabs, TabPanel } from '@/components/ui/Tabs'
import { ActivityTimeline } from '@/features/admin/ActivityTimeline'
import { CitizenReportsPanel } from '@/features/admin/CitizenReportsPanel'
import { FinancialPanel } from '@/features/admin/FinancialPanel'
import { ProgressPanel } from '@/features/admin/ProgressPanel'
import { ProjectFormDialog } from '@/features/admin/ProjectFormDialog'
import { StatusChangeDialog } from '@/features/admin/StatusChangeDialog'
import { NotesPanel } from '@/features/notes/NotesPanel'
import { ReviewPanel } from '@/features/reviews/ReviewPanel'
import { MitigationPanel } from '@/features/risk/MitigationPanel'
import { RiskPanel } from '@/features/risk/RiskPanel'
import { MapNavIcon, ProjectLocationPanel, useMapText } from '@/features/map'
import { formatDate, formatDateTime, formatLakh, formatNumber, formatPercent } from '@/utils/format'

/**
 * ADMIN / AUDITOR work detail page (SRS FR7b).
 *
 * A distinct, role-protected route from the citizen page - not the same
 * component with conditional sections. It carries everything the citizen page
 * shows plus risk analysis, mitigation tracking, reviews, internal notes and
 * the audit trail.
 */
export function AdminSchemeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const { t, tEnum } = useI18n()
  const { isReviewer } = useAuth()
  const [tab, setTab] = useState('overview')
  const [version, setVersion] = useState(0)
  const [statusOpen, setStatusOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)

  const project = useApi(
    (signal) => adminApi.getAdminProject(projectId, signal),
    [projectId, version],
    { enabled: Number.isFinite(projectId) },
  )
  const activity = useApi(
    (signal) => adminApi.listProjectActivity(projectId, signal),
    [projectId, version],
    { enabled: Number.isFinite(projectId) },
  )

  const reload = () => setVersion((value) => value + 1)
  const tm = useMapText()
  if (!Number.isFinite(projectId)) {
    return <EmptyState title={t('common.empty')} />
  }

  if (project.loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner label={t('common.loading')} />
      </div>
    )
  }

  if (project.error || !project.data) {
    return <ErrorState error={project.error} onRetry={project.reload} retryLabel={t('common.retry')} />
  }

  const p = project.data

  const tabs = [
    { id: 'overview', label: t('tab.overview'), icon: <Info className="h-4 w-4" aria-hidden /> },
    {
      id: 'financial',
      label: t('tab.financial'),
      icon: <IndianRupee className="h-4 w-4" aria-hidden />,
    },
    { id: 'progress', label: t('tab.progress'), icon: <TrendingUp className="h-4 w-4" aria-hidden /> },
    { id: 'location', label: tm('locationTab'), icon: <MapNavIcon className="h-4 w-4" aria-hidden /> },
    {
      id: 'risk',
      label: t('tab.risk'),
      icon: <TriangleAlert className="h-4 w-4" aria-hidden />,
      badge: p.open_risk_factors,
    },
    {
      id: 'mitigation',
      label: t('tab.mitigation'),
      icon: <ListChecks className="h-4 w-4" aria-hidden />,
      badge: p.open_mitigations,
    },
    { id: 'review', label: t('tab.review'), icon: <ClipboardCheck className="h-4 w-4" aria-hidden /> },
    { id: 'notes', label: t('tab.notes'), icon: <StickyNote className="h-4 w-4" aria-hidden /> },
    {
      id: 'reports',
      label: t('tab.reports'),
      icon: <MessageSquareWarning className="h-4 w-4" aria-hidden />,
      badge: p.citizen_report_count,
    },
    { id: 'activity', label: t('tab.activity'), icon: <Activity className="h-4 w-4" aria-hidden /> },
  ]

  return (
    <div>
      <Link
        to="/admin/projects"
        className="inline-flex items-center gap-1.5 text-sm text-ink-600 hover:text-ink-900"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        {t('admin.projectsTitle')}
      </Link>

      <header className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-ink-500">{p.project_code}</span>
            <StatusBadge status={p.status} />
            <ReviewStatusBadge status={p.review_status} />
            {p.risk_level ? <RiskBadge level={p.risk_level} score={p.risk_score} /> : null}
            {p.is_overdue ? <Badge tone="danger">{t('field.overdue')}</Badge> : null}
          </div>
          <h1 className="mt-2 text-xl font-semibold leading-snug text-ink-900">{p.title}</h1>
          <p className="mt-1 text-sm text-ink-600">
            {tEnum('district', p.district)}, {tEnum('state', p.state)} ·{' '}
            {tEnum('category', p.category)} · {p.mp_name}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {isReviewer ? (
            <Button
              variant="secondary"
              onClick={() => setEditOpen(true)}
              icon={<Pencil className="h-4 w-4" aria-hidden />}
            >
              Edit record
            </Button>
          ) : null}
          {isReviewer ? (
            <Button
              variant="secondary"
              onClick={() => setStatusOpen(true)}
              icon={<Settings2 className="h-4 w-4" aria-hidden />}
            >
              {t('status.change')}
            </Button>
          ) : null}
          <Link to={`/scheme/${p.id}`} target="_blank" rel="noreferrer">
            <Button variant="ghost" icon={<ExternalLink className="h-4 w-4" aria-hidden />}>
              {t('nav.citizenPortal')}
            </Button>
          </Link>
        </div>
      </header>

      <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatCard label={t('field.allocated')} value={formatLakh(p.allocated_amount)} />
        <StatCard label={t('field.spent')} value={formatLakh(p.spent_amount)} />
        <StatCard
          label={t('field.utilization')}
          value={formatPercent(p.utilization_percent)}
          tone={p.utilization_percent > 100 ? 'danger' : 'default'}
        />
        <StatCard label={t('field.progress')} value={formatPercent(p.progress_percent)} />
        <StatCard
          label={t('risk.score')}
          value={p.risk_score === null || p.risk_score === undefined ? '—' : p.risk_score.toFixed(1)}
          tone={
            p.risk_level === 'CRITICAL' || p.risk_level === 'HIGH'
              ? 'danger'
              : p.risk_level === 'MEDIUM'
                ? 'warning'
                : 'success'
          }
        />
      </div>

      <div className="mt-6">
        <Tabs tabs={tabs} active={tab} onChange={setTab} />

        <TabPanel id="overview" active={tab}>
          <Card>
            <CardHeader title={t('detail.projectInformation')} />
            <CardBody>
              <DataGrid>
                <DataRow label={t('field.projectId')}>{p.project_code}</DataRow>
                <DataRow label={t('field.mp')}>
                  {p.mp_name}
                  {p.constituency ? ` (${tEnum('constituency', p.constituency)})` : ''}
                </DataRow>
                <DataRow label={t('field.house')}>{p.house}</DataRow>
                <DataRow label={t('field.state')}>{tEnum('state', p.state)}</DataRow>
                <DataRow label={t('field.district')}>{tEnum('district', p.district)}</DataRow>
                <DataRow label={t('field.block')}>{p.block ?? t('common.notRecorded')}</DataRow>
                <DataRow label={t('field.location')}>{p.location ?? t('common.notRecorded')}</DataRow>
                <DataRow label={t('field.category')}>{tEnum('category', p.category)}</DataRow>
                <DataRow label={t('field.agency')}>{tEnum('agency', p.executing_agency)}</DataRow>
                <DataRow label={t('field.contractor')}>
                  {p.contractor ?? t('common.notRecorded')}
                </DataRow>
                <DataRow label={t('field.sanctionYear')}>{p.sanction_year}</DataRow>
                <DataRow label={t('field.sanctionDate')}>{formatDate(p.sanction_date)}</DataRow>
                <DataRow label={t('field.startDate')}>{formatDate(p.start_date)}</DataRow>
                <DataRow label={t('field.endDate')}>{formatDate(p.planned_end_date)}</DataRow>
                <DataRow label={t('field.actualEndDate')}>{formatDate(p.actual_end_date)}</DataRow>
                <DataRow label={t('field.beneficiaries')}>{formatNumber(p.beneficiaries)}</DataRow>
                <DataRow label={t('field.status')}>{p.status}</DataRow>
                <DataRow label={t('field.reviewStatus')}>{p.review_status}</DataRow>
                <DataRow label={t('admin.lastReviewed')}>
                  {p.last_reviewed_at ? formatDateTime(p.last_reviewed_at) : t('admin.awaitingFirstReview')}
                </DataRow>
                <DataRow label={t('admin.recordUpdated')}>{formatDateTime(p.updated_at)}</DataRow>
              </DataGrid>

              {p.description ? (
                <div className="mt-4 border-t border-ink-100 pt-4">
                  <p className="data-label">{t('field.description')}</p>
                  <p className="mt-1 text-sm leading-relaxed text-ink-700">{p.description}</p>
                </div>
              ) : null}

              {p.remarks ? (
                <div className="mt-4 border-t border-ink-100 pt-4">
                  <p className="data-label">Remarks</p>
                  <p className="mt-1 text-sm leading-relaxed text-ink-700">{p.remarks}</p>
                </div>
              ) : null}
            </CardBody>
          </Card>
        </TabPanel>

        <TabPanel id="financial" active={tab}>
          <FinancialPanel project={p} canAct={isReviewer} onChanged={reload} />
        </TabPanel>

        <TabPanel id="progress" active={tab}>
          <ProgressPanel project={p} canAct={isReviewer} onChanged={reload} />
        </TabPanel>
        <TabPanel id="location" active={tab}>
          <ProjectLocationPanel project={p} canEdit={isReviewer} onSaved={reload} />
        </TabPanel>
        <TabPanel id="risk" active={tab}>
          <RiskPanel projectId={projectId} canAct={isReviewer} onAssessmentChange={reload} />
        </TabPanel>

        <TabPanel id="mitigation" active={tab}>
          <MitigationPanel projectId={projectId} canAct={isReviewer} />
        </TabPanel>

        <TabPanel id="review" active={tab}>
          <ReviewPanel projectId={projectId} canAct={isReviewer} onReviewed={reload} />
        </TabPanel>

        <TabPanel id="notes" active={tab}>
          <NotesPanel projectId={projectId} canAct={isReviewer} />
        </TabPanel>

        <TabPanel id="reports" active={tab}>
          <CitizenReportsPanel projectId={projectId} canAct={isReviewer} />
        </TabPanel>

        <TabPanel id="activity" active={tab}>
          <Card>
            <CardHeader
              title={t('activity.title')}
              icon={<Activity className="h-4 w-4" aria-hidden />}
            />
            <CardBody>
              {activity.loading ? (
                <Spinner label={t('common.loading')} />
              ) : activity.error ? (
                <ErrorState error={activity.error} onRetry={activity.reload} retryLabel={t('common.retry')} />
              ) : (
                <ActivityTimeline entries={activity.data ?? []} />
              )}
            </CardBody>
          </Card>
        </TabPanel>
      </div>

      {editOpen ? (
        <ProjectFormDialog
          open={editOpen}
          project={p}
          onClose={() => setEditOpen(false)}
          onSaved={reload}
        />
      ) : null}

      <StatusChangeDialog
        open={statusOpen}
        projectId={projectId}
        currentStatus={p.status}
        onClose={() => setStatusOpen(false)}
        onChanged={reload}
      />
    </div>
  )
}

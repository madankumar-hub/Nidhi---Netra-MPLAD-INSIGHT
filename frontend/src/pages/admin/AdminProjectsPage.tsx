import { useCallback, useMemo, useState } from 'react'
import { FileUp, Plus } from 'lucide-react'
import { adminApi, projectsAdminApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useDebounce } from '@/hooks/useDebounce'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { ProjectFilters } from '@/features/citizen/ProjectFilters'
import { AdminProjectTable } from '@/features/admin/AdminProjectTable'
import { Button } from '@/components/ui/Button'
import { Checkbox, SelectInput } from '@/components/ui/Field'
import { Pagination } from '@/components/ui/Pagination'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { ProjectFormDialog } from '@/features/admin/ProjectFormDialog'
import { BulkImportDialog } from '@/features/admin/BulkImportDialog'
import { ExportMenu } from '@/features/admin/ExportMenu'
import { useAuth } from '@/features/auth/AuthContext'
import { REVIEW_STATUSES, RISK_LEVELS } from '@/utils/constants'
import type { ProjectQuery, ReviewStatus, RiskLevel } from '@/types'

const INITIAL: ProjectQuery = { page: 1, page_size: 20, sort_by: 'updated_at', sort_dir: 'desc' }

export function AdminProjectsPage() {
  const { t } = useI18n()
  const { isReviewer, isAdmin } = useAuth()
  const [createOpen, setCreateOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [query, setQuery] = useState<ProjectQuery>(INITIAL)
  const [searchInput, setSearchInput] = useState('')
  const search = useDebounce(searchInput, 400)

  const effectiveQuery = useMemo(() => ({ ...query, search }), [query, search])
  const filters = useApi((signal) => adminApi.getAdminFilters(signal), [])
  const projects = useApi(
    (signal) => adminApi.listAdminProjects(effectiveQuery, signal),
    [JSON.stringify(effectiveQuery)],
  )
  const removeProject = useMutation(projectsAdminApi.deleteProject)

  const handleDelete = useCallback(
    async (projectId: number) => {
      // A destructive, irreversible action gets an explicit confirmation.
      if (!window.confirm(t('admin.deleteConfirm'))) return
      const result = await removeProject.run(projectId)
      if (result) projects.reload()
    },
    [removeProject, projects, t],
  )

  const patch = useCallback((update: Partial<ProjectQuery>) => {
    setQuery((current) => ({ ...current, ...update }))
  }, [])

  return (
    <div>
      <PageHeader
        title={t('admin.projectsTitle')}
        description={t('admin.projectsSubtitle')}
        actions={
          <>
            {isReviewer ? (
              <Button
                onClick={() => setCreateOpen(true)}
                icon={<Plus className="h-4 w-4" aria-hidden />}
              >
                {t('admin.newWork')}
              </Button>
            ) : null}
          {isReviewer ? (
            <Button
              variant="secondary"
              onClick={() => setImportOpen(true)}
              icon={<FileUp className="h-4 w-4" aria-hidden />}
            >
              {t('import.open')}
            </Button>
          ) : null}
          <ExportMenu
            params={{
              search,
              district: query.district,
              category: query.category,
              status: query.status || undefined,
              review_status: query.review_status || undefined,
            }}
          />
          </>
        }
      />

      {removeProject.error ? (
        <div className="mb-4">
          <InlineMessage tone="warning">{removeProject.error.message}</InlineMessage>
        </div>
      ) : null}

      <ProjectFilters
        filters={filters.data}
        query={query}
        onChange={patch}
        onClear={() => {
          setQuery(INITIAL)
          setSearchInput('')
        }}
        searchValue={searchInput}
        onSearchChange={(value) => {
          setSearchInput(value)
          patch({ page: 1 })
        }}
        extra={
          <>
            <SelectInput
              label={t('field.reviewStatus')}
              value={query.review_status ?? ''}
              placeholder={t('common.all')}
              options={REVIEW_STATUSES.map((item) => ({ label: item, value: item }))}
              onChange={(event) =>
                patch({ review_status: event.target.value as ReviewStatus | '', page: 1 })
              }
            />
            <SelectInput
              label={t('risk.level')}
              value={query.risk_level ?? ''}
              placeholder={t('common.all')}
              options={RISK_LEVELS.map((item) => ({ label: item, value: item }))}
              onChange={(event) => patch({ risk_level: event.target.value as RiskLevel | '', page: 1 })}
            />
            <div className="flex items-end pb-2">
              <Checkbox
                label={t('admin.overdue')}
                checked={Boolean(query.overdue_only)}
                onChange={(checked) => patch({ overdue_only: checked, page: 1 })}
              />
            </div>
          </>
        }
      />

      <div className="mt-6">
        {projects.loading ? (
          <div className="surface p-4">
            <SkeletonRows rows={8} />
          </div>
        ) : projects.error ? (
          <ErrorState error={projects.error} onRetry={projects.reload} retryLabel={t('common.retry')} />
        ) : (projects.data?.items.length ?? 0) === 0 ? (
          <EmptyState title={t('common.empty')} description={t('common.emptyHint')} />
        ) : (
          <>
            <div className="surface overflow-hidden md:p-0">
              <div className="p-4 md:p-0">
                <AdminProjectTable
                  rows={projects.data?.items ?? []}
                  onDelete={isAdmin ? handleDelete : undefined}
                />
              </div>
            </div>
            <div className="mt-4">
              <Pagination
                page={projects.data?.page ?? 1}
                totalPages={projects.data?.total_pages ?? 1}
                total={projects.data?.total ?? 0}
                pageSize={projects.data?.page_size ?? 20}
                onChange={(page) => {
                  patch({ page })
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                }}
                labels={{
                  previous: t('common.previous'),
                  next: t('common.next'),
                  showing: t('common.showing'),
                  results: t('common.results'),
                  page: t('common.page'),
                  of: t('common.of'),
                }}
              />
            </div>
          </>
        )}
      </div>

      <ProjectFormDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSaved={projects.reload}
      />

      <BulkImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onImported={projects.reload}
      />
    </div>
  )
}

import { useCallback, useMemo, useState } from 'react'
import { projectsApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useDebounce } from '@/hooks/useDebounce'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { ProjectCard } from '@/features/citizen/ProjectCard'
import { ProjectFilters } from '@/features/citizen/ProjectFilters'
import { Pagination } from '@/components/ui/Pagination'
import { SelectInput } from '@/components/ui/Field'
import { SkeletonCards } from '@/components/ui/Spinner'
import { EmptyState, ErrorState } from '@/components/ui/States'
import type { ProjectQuery } from '@/types'

const SORTS = [
  { value: 'updated_at:desc', key: 'projects.sort.updated' },
  { value: 'allocated_amount:desc', key: 'projects.sort.allocationDesc' },
  { value: 'allocated_amount:asc', key: 'projects.sort.allocationAsc' },
  { value: 'progress_percent:desc', key: 'projects.sort.progressDesc' },
  { value: 'progress_percent:asc', key: 'projects.sort.progressAsc' },
  { value: 'sanction_year:desc', key: 'projects.sort.year' },
] as const

const INITIAL: ProjectQuery = { page: 1, page_size: 12, sort_by: 'updated_at', sort_dir: 'desc' }

export function ProjectsPage() {
  const { t } = useI18n()
  const [query, setQuery] = useState<ProjectQuery>(INITIAL)
  const [searchInput, setSearchInput] = useState('')
  const search = useDebounce(searchInput, 400)

  const effectiveQuery = useMemo(() => ({ ...query, search }), [query, search])

  const filters = useApi((signal) => projectsApi.getPublicFilters(signal), [])
  const projects = useApi(
    (signal) => projectsApi.listPublicProjects(effectiveQuery, signal),
    [JSON.stringify(effectiveQuery)],
  )

  const patch = useCallback((update: Partial<ProjectQuery>) => {
    setQuery((current) => ({ ...current, ...update }))
  }, [])

  const clear = useCallback(() => {
    setQuery(INITIAL)
    setSearchInput('')
  }, [])

  const sortValue = `${query.sort_by ?? 'updated_at'}:${query.sort_dir ?? 'desc'}`


  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <PageHeader title={t('projects.title')} description={t('projects.subtitle')} />

      <ProjectFilters
        filters={filters.data}
        query={query}
        onChange={patch}
        onClear={clear}
        searchValue={searchInput}
        onSearchChange={(value) => {
          setSearchInput(value)
          setQuery((current) => ({ ...current, page: 1 }))
        }}
        extra={
          <SelectInput
            label={t('projects.sortBy')}
            value={sortValue}
            options={SORTS.map((sort) => ({ label: t(sort.key), value: sort.value }))}
            onChange={(event) => {
              const [sort_by, sort_dir] = event.target.value.split(':')
              patch({ sort_by, sort_dir: sort_dir as 'asc' | 'desc', page: 1 })
            }}
          />
        }
      />

      <div className="mt-6">
        {projects.loading ? (
          <SkeletonCards count={6} />
        ) : projects.error ? (
          <ErrorState error={projects.error} onRetry={projects.reload} retryLabel={t('common.retry')} />
        ) : (projects.data?.items.length ?? 0) === 0 ? (
          <EmptyState title={t('common.empty')} description={t('common.emptyHint')} />
        ) : (
          <>
            <p className="mb-4 text-sm text-ink-600">
              {t('common.showing')}{' '}
              <span className="font-semibold text-ink-900">
                {(projects.data?.total ?? 0).toLocaleString('en-IN')}
              </span>{' '}
              {t('common.results')}
            </p>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {projects.data?.items.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
            <div className="mt-6">
              <Pagination
                page={projects.data?.page ?? 1}
                totalPages={projects.data?.total_pages ?? 1}
                total={projects.data?.total ?? 0}
                pageSize={projects.data?.page_size ?? 12}
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
    </div>
  )
}

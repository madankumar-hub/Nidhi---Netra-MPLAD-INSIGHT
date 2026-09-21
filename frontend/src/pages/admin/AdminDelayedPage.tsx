import { adminApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardBody } from '@/components/ui/Card'
import { AdminProjectTable } from '@/features/admin/AdminProjectTable'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState } from '@/components/ui/States'

export function AdminDelayedPage() {
  const { t } = useI18n()
  const delayed = useApi((signal) => adminApi.listDelayedProjects(signal), [])

  return (
    <div>
      <PageHeader title={t('admin.delayedTitle')} description={t('admin.delayedSubtitle')} />
      <Card>
        <CardBody>
          {delayed.loading ? (
            <SkeletonRows rows={8} />
          ) : delayed.error ? (
            <ErrorState error={delayed.error} onRetry={delayed.reload} retryLabel={t('common.retry')} />
          ) : (delayed.data?.length ?? 0) === 0 ? (
            <EmptyState title={t('common.empty')} description={t('empty.noDelayed')} />
          ) : (
            <AdminProjectTable rows={delayed.data ?? []} />
          )}
        </CardBody>
      </Card>
    </div>
  )
}

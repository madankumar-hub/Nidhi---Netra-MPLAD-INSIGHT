import { adminApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardBody } from '@/components/ui/Card'
import { SkeletonRows } from '@/components/ui/Spinner'
import { ErrorState } from '@/components/ui/States'
import { ActivityTimeline } from '@/features/admin/ActivityTimeline'

export function AdminActivityPage() {
  const { t } = useI18n()
  const activity = useApi((signal) => adminApi.listRecentActivity(150, signal), [])

  return (
    <div>
      <PageHeader title={t('admin.activityTitle')} description={t('admin.activitySubtitle')} />
      <Card>
        <CardBody>
          {activity.loading ? (
            <SkeletonRows rows={10} />
          ) : activity.error ? (
            <ErrorState error={activity.error} onRetry={activity.reload} retryLabel={t('common.retry')} />
          ) : (
            <ActivityTimeline entries={activity.data ?? []} showProject />
          )}
        </CardBody>
      </Card>
    </div>
  )
}

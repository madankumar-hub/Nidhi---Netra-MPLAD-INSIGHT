import { Link } from 'react-router-dom'
import { ClipboardCheck, ClipboardList } from 'lucide-react'
import { adminApi, workflowApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { ReviewStatusBadge } from '@/components/ui/Badge'
import { AdminProjectTable } from '@/features/admin/AdminProjectTable'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { formatDateTime, truncate } from '@/utils/format'

export function AdminReviewQueuePage() {
  const { t } = useI18n()
  const pending = useApi((signal) => adminApi.listPendingReview(signal), [])
  const recent = useApi((signal) => workflowApi.listRecentReviews(30, signal), [])

  return (
    <div>
      <PageHeader title={t('admin.reviewQueueTitle')} description={t('admin.reviewQueueSubtitle')} />

      <Card>
        <CardHeader
          title={t('admin.awaitingFirstReview')}
          icon={<ClipboardList className="h-4 w-4" aria-hidden />}
        />
        <CardBody>
          {pending.loading ? (
            <SkeletonRows rows={6} />
          ) : pending.error ? (
            <ErrorState error={pending.error} onRetry={pending.reload} retryLabel={t('common.retry')} />
          ) : (pending.data?.length ?? 0) === 0 ? (
            <EmptyState title={t('common.empty')} description={t('empty.noReviewQueue')} />
          ) : (
            <AdminProjectTable rows={pending.data ?? []} />
          )}
        </CardBody>
      </Card>

      <Card className="mt-6">
        <CardHeader
          title={t('admin.latestReviews')}
          icon={<ClipboardCheck className="h-4 w-4" aria-hidden />}
        />
        <CardBody>
          {recent.loading ? (
            <SkeletonRows rows={5} />
          ) : recent.error ? (
            <ErrorState error={recent.error} onRetry={recent.reload} retryLabel={t('common.retry')} />
          ) : (recent.data?.length ?? 0) === 0 ? (
            <EmptyState title={t('review.none')} />
          ) : (
            <ul className="divide-y divide-ink-100">
              {recent.data?.map((review) => (
                <li key={review.id} className="py-3 first:pt-0 last:pb-0">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <ReviewStatusBadge status={review.status} />
                      <Link
                        to={`/admin/scheme/${review.project_id}`}
                        className="text-sm font-medium text-ink-800 hover:underline"
                      >
                        Work #{review.project_id}
                      </Link>
                    </div>
                    <span className="text-xs text-ink-500">{formatDateTime(review.review_date)}</span>
                  </div>
                  <p className="mt-1.5 text-sm text-ink-700">{truncate(review.findings, 200)}</p>
                  <p className="mt-1 text-xs text-ink-500">
                    {review.reviewer_name} ({review.reviewer_role})
                  </p>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>
    </div>
  )
}

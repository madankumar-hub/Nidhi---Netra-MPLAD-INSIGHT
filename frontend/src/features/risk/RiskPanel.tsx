import { useState } from 'react'
import {
  AlertTriangle,
  BrainCircuit,
  Check,
  Cpu,
  Info,
  Network,
  RefreshCw,
  Sigma,
  TriangleAlert,
} from 'lucide-react'
import { riskApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Badge, RiskBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SelectInput } from '@/components/ui/Field'
import { DataGrid, DataRow } from '@/components/ui/Metrics'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { RISK_STATUSES } from '@/utils/constants'
import { formatDateTime, formatPercent } from '@/utils/format'
import type { AnalysisSource, RiskAssessment, RiskFactor, RiskStatus } from '@/types'

const SOURCE_ICON: Record<AnalysisSource, typeof Cpu> = {
  rule_based: Cpu,
  statistical: Sigma,
  machine_learning: Network,
  external_ai: BrainCircuit,
}

function SourceBadge({ source }: { source: AnalysisSource }) {
  // Analysis layers already have dedicated `risk.source.*` keys in both
  // dictionaries, so this one does not go through the enum registry.
  const { t } = useI18n()
  const Icon = SOURCE_ICON[source]
  return (
    <Badge tone="neutral">
      <Icon className="h-3 w-3" aria-hidden />
      {t(`risk.source.${source}` as const)}
    </Badge>
  )
}

function FactorCard({ factor }: { factor: RiskFactor }) {
  const { t, tEnum } = useI18n()
  const tone =
    factor.severity === 'CRITICAL'
      ? 'critical'
      : factor.severity === 'HIGH'
        ? 'danger'
        : factor.severity === 'MEDIUM'
          ? 'warning'
          : 'success'

  return (
    <li className="rounded-lg border border-ink-200 bg-white">
      <div className="flex flex-wrap items-start justify-between gap-2 border-b border-ink-100 px-4 py-3">
        <div className="min-w-0">
          <h4 className="text-sm font-semibold text-ink-900">
            {tEnum('riskFactorTitle', factor.title)}
          </h4>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <Badge tone="neutral">{tEnum('riskCategory', factor.category)}</Badge>
            <Badge tone={tone} dot>
              {tEnum('riskLevel', factor.severity)}
            </Badge>
            <SourceBadge source={factor.source} />
            <span className="font-mono text-[11px] text-ink-400">{factor.code}</span>
          </div>
        </div>
        <div className="text-right">
          <p className="data-label">{t('risk.contribution')}</p>
          <p className="text-sm font-semibold tabular-nums text-ink-900">
            +{factor.contribution.toFixed(1)}
          </p>
        </div>
      </div>

      <dl className="divide-y divide-ink-100 text-sm">
        <div className="px-4 py-2.5">
          <dt className="data-label">{t('risk.whyDetected')}</dt>
          <dd className="mt-1 leading-relaxed text-ink-800">{factor.detected_indicator}</dd>
        </div>
        <div className="px-4 py-2.5">
          <dt className="data-label">{t('risk.whatData')}</dt>
          <dd className="mt-1 leading-relaxed text-ink-700">{factor.evidence}</dd>
          {factor.metric_name ? (
            <dd className="mt-1.5 flex flex-wrap gap-3 text-xs text-ink-500">
              <span>
                {factor.metric_name}:{' '}
                <span className="font-semibold tabular-nums text-ink-700">
                  {factor.metric_value ?? '—'}
                </span>
              </span>
              {factor.threshold_value !== null && factor.threshold_value !== undefined ? (
                <span>
                  threshold:{' '}
                  <span className="font-semibold tabular-nums text-ink-700">
                    {factor.threshold_value}
                  </span>
                </span>
              ) : null}
              {factor.reference_project_code ? (
                <span>
                  compared with:{' '}
                  <span className="font-mono text-ink-700">{factor.reference_project_code}</span>
                </span>
              ) : null}
            </dd>
          ) : null}
        </div>
        <div className="px-4 py-2.5">
          <dt className="data-label">{t('risk.whatIsIt')}</dt>
          <dd className="mt-1 leading-relaxed text-ink-700">{factor.explanation}</dd>
        </div>
        <div className="bg-ink-50/60 px-4 py-2.5">
          <dt className="data-label">{t('risk.whatToDo')}</dt>
          <dd className="mt-1 leading-relaxed text-ink-800">{factor.recommended_action}</dd>
        </div>
      </dl>
    </li>
  )
}

interface RiskPanelProps {
  projectId: number
  canAct: boolean
  onAssessmentChange?: (assessment: RiskAssessment) => void
}

export function RiskPanel({ projectId, canAct, onAssessmentChange }: RiskPanelProps) {
  const { t, tEnum } = useI18n()
  const [refreshKey, setRefreshKey] = useState(0)
  const assessment = useApi(
    (signal) => riskApi.getRiskAssessment(projectId, signal),
    [projectId, refreshKey],
  )
  const engine = useApi((signal) => riskApi.getRiskEngineInfo(signal), [])
  const recompute = useMutation(riskApi.recomputeRisk)
  const setStatus = useMutation(({ status, reason }: { status: RiskStatus; reason?: string }) =>
    riskApi.updateRiskStatus(projectId, status, reason),
  )

  /**
   * Closing out a risk is a decision, so it is recorded like one: the backend
   * writes an activity entry naming the officer and the transition. The panel
   * only offers the transition - it does not decide anything itself.
   */
  const handleStatusChange = async (next: RiskStatus) => {
    const result = await setStatus.run({ status: next })
    if (result) {
      onAssessmentChange?.(result)
      setRefreshKey((value) => value + 1)
    }
  }

  const handleRecompute = async (useAi: boolean) => {
    const result = await recompute.run(projectId, useAi)
    if (result) {
      onAssessmentChange?.(result)
      setRefreshKey((value) => value + 1)
    }
  }

  if (assessment.loading) {
    return (
      <Card>
        <CardBody>
          <SkeletonRows rows={6} />
        </CardBody>
      </Card>
    )
  }

  if (assessment.error) {
    return <ErrorState error={assessment.error} onRetry={assessment.reload} retryLabel={t('common.retry')} />
  }

  const a = assessment.data
  if (!a) {
    return (
      <EmptyState
        title={t('admin.noRiskYet')}
        action={
          canAct ? (
            <Button onClick={() => handleRecompute(false)} loading={recompute.pending}>
              {t('admin.runAssessment')}
            </Button>
          ) : undefined
        }
      />
    )
  }

  const aiAvailable = engine.data?.external_ai_enabled ?? false

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader
          title={t('risk.title')}
          description={a.summary}
          icon={<TriangleAlert className="h-4 w-4" aria-hidden />}
          actions={
            canAct ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  loading={recompute.pending}
                  onClick={() => handleRecompute(false)}
                  icon={<RefreshCw className="h-3.5 w-3.5" aria-hidden />}
                >
                  {t('admin.recompute')}
                </Button>
                {aiAvailable ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    loading={recompute.pending}
                    onClick={() => handleRecompute(true)}
                    icon={<BrainCircuit className="h-3.5 w-3.5" aria-hidden />}
                  >
                    {t('risk.recomputeWithAi')}
                  </Button>
                ) : null}
              </>
            ) : undefined
          }
        />
        <CardBody>
          {recompute.error ? (
            <div className="mb-4">
              <InlineMessage tone="warning">{recompute.error.message}</InlineMessage>
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <RiskBadge level={a.risk_level} score={a.risk_score} />
            <Badge tone="neutral">
              {t('risk.likelihood')}: {tEnum('likelihood', a.likelihood)}
            </Badge>
            <Badge tone="neutral">
              {t('risk.impact')}: {tEnum('impact', a.impact)}
            </Badge>
            <Badge tone="info">
              {t('risk.status')}: {tEnum('riskStatus', a.status)}
            </Badge>
          </div>

          {canAct ? (
            <div className="mt-4 max-w-xs">
              <SelectInput
                label={t('risk.changeStatus')}
                hint={t('risk.changeStatusHint')}
                value={a.status}
                disabled={setStatus.pending}
                options={RISK_STATUSES.map((status) => ({
                  label: tEnum('riskStatus', status),
                  value: status,
                }))}
                onChange={(event) => handleStatusChange(event.target.value as RiskStatus)}
              />
            </div>
          ) : null}

          {setStatus.error ? (
            <div className="mt-3">
              <InlineMessage tone="warning">{setStatus.error.message}</InlineMessage>
            </div>
          ) : null}

          <div className="mt-4">
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-ink-200">
              <div
                className="h-full rounded-full bg-ink-800"
                style={{ width: `${Math.min(a.risk_score, 100)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-ink-500">
              {t('risk.score')}: {a.risk_score.toFixed(1)} / 100
            </p>
          </div>

          <DataGrid columns={4}>
            <DataRow label={t('risk.primaryCategory')}>
              {a.primary_category ? tEnum('riskCategory', a.primary_category) : t('common.notRecorded')}
            </DataRow>
            <DataRow label={t('risk.dataCompleteness')}>
              {formatPercent(a.data_completeness_percent, 0)}
            </DataRow>
            <DataRow label={t('risk.assessedAt')}>{formatDateTime(a.assessed_at)}</DataRow>
            <DataRow label={t('risk.engineVersion')}>
              <span className="font-mono text-xs">{a.engine_version}</span>
            </DataRow>
          </DataGrid>

          <div className="mt-3">
            <p className="data-label">{t('risk.layersUsed')}</p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {a.analysis_sources.map((source) => (
                <SourceBadge key={source} source={source} />
              ))}
            </div>
          </div>

          {a.ai_narrative ? (
            <div className="mt-4 rounded-md border border-ink-200 bg-ink-50 p-3">
              <p className="flex items-center gap-1.5 text-xs font-semibold text-ink-800">
                <BrainCircuit className="h-3.5 w-3.5" aria-hidden />
                {t('risk.aiNarrative')}
                {a.ai_model_used ? (
                  <span className="font-mono font-normal text-ink-500">({a.ai_model_used})</span>
                ) : null}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-ink-700">{a.ai_narrative}</p>
            </div>
          ) : (
            <p className="mt-4 flex items-start gap-2 rounded-md bg-ink-50 px-3 py-2 text-xs leading-relaxed text-ink-600">
              <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
              {t('risk.aiUnavailable')}
            </p>
          )}

          <p className="mt-3 flex items-start gap-2 text-xs leading-relaxed text-ink-500">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            {t('risk.disclaimer')}
          </p>
        </CardBody>
      </Card>

      <div>
        <h3 className="mb-3 text-sm font-semibold text-ink-900">
          {t('risk.factors')}{' '}
          <span className="font-normal text-ink-500">({a.factors.length})</span>
        </h3>
        {a.factors.length === 0 ? (
          <EmptyState
            title={t('risk.noFactors')}
            icon={<Check className="h-8 w-8 text-moss-600" aria-hidden />}
          />
        ) : (
          <ul className="space-y-3">
            {a.factors.map((factor) => (
              <FactorCard key={factor.id} factor={factor} />
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

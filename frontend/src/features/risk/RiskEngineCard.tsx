import { BrainCircuit, Check, Cpu, Minus, Network, Sigma } from 'lucide-react'
import { riskApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Badge } from '@/components/ui/Badge'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SkeletonRows } from '@/components/ui/Spinner'
import { ErrorState } from '@/components/ui/States'
import { formatNumber } from '@/utils/format'

/**
 * Shows exactly which analysis layers are live on this deployment. The point is
 * that the interface never claims a capability the server does not have: if the
 * external-AI layer is unconfigured, this card says so.
 */
export function RiskEngineCard() {
  const { t } = useI18n()
  const engine = useApi((signal) => riskApi.getRiskEngineInfo(signal), [])

  if (engine.loading) {
    return (
      <Card>
        <CardBody>
          <SkeletonRows rows={4} />
        </CardBody>
      </Card>
    )
  }

  if (engine.error || !engine.data) {
    return <ErrorState error={engine.error} onRetry={engine.reload} retryLabel={t('common.retry')} />
  }

  const info = engine.data
  const ml = info.machine_learning

  const layers = [
    {
      icon: <Cpu className="h-4 w-4" aria-hidden />,
      name: t('risk.source.rule_based'),
      active: info.rule_based_enabled,
      detail: '16 deterministic threshold rules over the project record.',
    },
    {
      icon: <Sigma className="h-4 w-4" aria-hidden />,
      name: t('risk.source.statistical'),
      active: info.statistical_enabled,
      detail: `Peer-cohort outliers and near-duplicate detection (${info.duplicate_detection_backend}).`,
    },
    {
      icon: <Network className="h-4 w-4" aria-hidden />,
      name: t('risk.source.machine_learning'),
      active: info.machine_learning_enabled,
      detail: ml
        ? ml.available
          ? `${ml.algorithm}. ${ml.trees} trees over ${ml.features} features, ${t('risk.mlTrainedOn').toLowerCase()} ${formatNumber(ml.trained_on_records)} ${t('risk.mlRecords')}.`
          : t('risk.mlUnavailable')
        : t('risk.mlUnavailable'),
    },
    {
      icon: <BrainCircuit className="h-4 w-4" aria-hidden />,
      name: t('risk.source.external_ai'),
      active: info.external_ai_enabled,
      detail: info.external_ai_enabled
        ? `${info.external_ai_provider} · ${info.external_ai_model}. Writes a narrative over findings already computed.`
        : t('risk.aiUnavailable'),
    },
  ]

  return (
    <Card>
      <CardHeader
        title={t('risk.engine')}
        description={`${t('risk.engineVersion')}: ${info.engine_version}`}
      />
      <CardBody>
        <ul className="space-y-3">
          {layers.map((layer) => (
            <li key={layer.name} className="flex items-start gap-3">
              <span
                className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${
                  layer.active ? 'bg-moss-100 text-moss-700' : 'bg-ink-100 text-ink-400'
                }`}
              >
                {layer.icon}
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-ink-900">{layer.name}</span>
                  <Badge tone={layer.active ? 'success' : 'neutral'}>
                    {layer.active ? (
                      <>
                        <Check className="h-3 w-3" aria-hidden />
                        Active
                      </>
                    ) : (
                      <>
                        <Minus className="h-3 w-3" aria-hidden />
                        Not configured
                      </>
                    )}
                  </Badge>
                </div>
                <p className="mt-0.5 text-xs leading-relaxed text-ink-600">{layer.detail}</p>
              </div>
            </li>
          ))}
        </ul>

        {ml?.available ? (
          <div className="mt-4 rounded-md border border-ink-200 bg-ink-50 p-3">
            <p className="text-xs font-semibold text-ink-800">{t('risk.mlTitle')}</p>
            <p className="mt-1 text-xs leading-relaxed text-ink-600">
              {t('risk.mlUnsupervised')} {ml.notes}
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {ml.feature_names.map((feature) => (
                <span
                  key={feature}
                  className="rounded bg-white px-1.5 py-0.5 font-mono text-[10px] text-ink-600 ring-1 ring-inset ring-ink-200"
                >
                  {feature}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        <p className="mt-3 text-xs leading-relaxed text-ink-500">{info.notes}</p>
      </CardBody>
    </Card>
  )
}

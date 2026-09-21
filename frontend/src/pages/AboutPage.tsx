import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'

export function AboutPage() {
  const { t } = useI18n()

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <PageHeader title={t('nav.about')} description={t('app.subtitle')} />

      <div className="space-y-6">
        <Card>
          <CardHeader title={t('about.whatTitle')} />
          <CardBody className="space-y-3 text-sm leading-relaxed text-ink-700">
            <p>{t('about.whatP1')}</p>
            <p>{t('about.whatP2')}</p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={t('about.howTitle')} />
          <CardBody className="space-y-3 text-sm leading-relaxed text-ink-700">
            <p>{t('about.howP1')}</p>
            <p>{t('about.howP2')}</p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={t('about.dataTitle')} />
          <CardBody className="space-y-3 text-sm leading-relaxed text-ink-700">
            <p>{t('footer.note')}</p>
            <p>{t('about.dataP1')}</p>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

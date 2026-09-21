import type { ReactNode } from 'react'
import { Filter, Search, X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { SelectInput, TextInput } from '@/components/ui/Field'
import { useI18n } from '@/i18n'
import type { EnumFamily } from '@/i18n'
import type { FilterOptions, ProjectQuery } from '@/types'
import { PROJECT_STATUSES } from '@/utils/constants'

interface ProjectFiltersProps {
  filters: FilterOptions | null
  query: ProjectQuery
  onChange: (patch: Partial<ProjectQuery>) => void
  onClear: () => void
  searchValue: string
  onSearchChange: (value: string) => void
  extra?: ReactNode
}

export function ProjectFilters({
  filters,
  query,
  onChange,
  onClear,
  searchValue,
  onSearchChange,
  extra,
}: ProjectFiltersProps) {
  const { t, tEnum } = useI18n()

  // The API returns the English wire value as both label and value. The value
  // must stay English - it goes straight back as a query parameter - so only the
  // label is translated. District, category and agency are controlled
  // vocabularies with Hindi in `i18n/vocabulary.ts`; MP names and years are not,
  // and `family: null` leaves those alone.
  const toOptions = (
    values: { label: string; value: string; count: number }[] | undefined,
    family: EnumFamily | null = null,
  ) =>
    (values ?? []).map((option) => ({
      label: family ? tEnum(family, option.label) : option.label,
      value: option.value,
      count: option.count,
    }))

  const activeCount = [
    query.mp,
    query.district,
    query.category,
    query.year,
    query.status,
    query.agency,
  ].filter(Boolean).length

  return (
    <div className="surface p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-ink-800">
        <Filter className="h-4 w-4 text-ink-500" aria-hidden />
        {t('common.filters')}
        {activeCount > 0 ? (
          <span className="rounded-full bg-ink-100 px-2 py-0.5 text-xs font-semibold text-ink-700">
            {activeCount}
          </span>
        ) : null}
        {activeCount > 0 ? (
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto"
            onClick={onClear}
            icon={<X className="h-3.5 w-3.5" aria-hidden />}
          >
            {t('common.clearFilters')}
          </Button>
        ) : null}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <div className="sm:col-span-2 xl:col-span-2">
          <TextInput
            label={t('common.search')}
            type="search"
            value={searchValue}
            placeholder={t('common.searchPlaceholder')}
            onChange={(event) => onSearchChange(event.target.value)}
          />
        </div>

        <SelectInput
          label={t('field.mp')}
          value={query.mp ?? ''}
          placeholder={t('common.all')}
          options={toOptions(filters?.mps)}
          onChange={(event) => onChange({ mp: event.target.value, page: 1 })}
        />
        <SelectInput
          label={t('field.district')}
          value={query.district ?? ''}
          placeholder={t('common.all')}
          options={toOptions(filters?.districts, 'district')}
          onChange={(event) => onChange({ district: event.target.value, page: 1 })}
        />
        <SelectInput
          label={t('field.category')}
          value={query.category ?? ''}
          placeholder={t('common.all')}
          options={toOptions(filters?.categories, 'category')}
          onChange={(event) => onChange({ category: event.target.value, page: 1 })}
        />
        <SelectInput
          label={t('field.sanctionYear')}
          value={String(query.year ?? '')}
          placeholder={t('common.all')}
          options={toOptions(filters?.years)}
          onChange={(event) => onChange({ year: event.target.value, page: 1 })}
        />
        <SelectInput
          label={t('field.status')}
          value={query.status ?? ''}
          placeholder={t('common.all')}
          options={PROJECT_STATUSES.map((status) => ({
            label: tEnum('projectStatus', status),
            value: status,
          }))}
          onChange={(event) =>
            onChange({ status: event.target.value as ProjectQuery['status'], page: 1 })
          }
        />
        <SelectInput
          label={t('field.agency')}
          value={query.agency ?? ''}
          placeholder={t('common.all')}
          options={toOptions(filters?.agencies, 'agency')}
          onChange={(event) => onChange({ agency: event.target.value, page: 1 })}
        />
        {extra}
      </div>

      <p className="mt-3 flex items-center gap-1.5 text-xs text-ink-500">
        <Search className="h-3.5 w-3.5" aria-hidden />
        {t('common.serverSideNote')}
      </p>
    </div>
  )
}

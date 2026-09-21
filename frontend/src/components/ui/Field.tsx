import type {
  ChangeEvent,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'
import { useId } from 'react'

interface FieldWrapperProps {
  label: string
  hint?: string
  error?: string | null
  required?: boolean
  children: (id: string) => ReactNode
  className?: string
}

export function Field({ label, hint, error, required, children, className = '' }: FieldWrapperProps) {
  const id = useId()
  return (
    <div className={className}>
      <label className="field-label" htmlFor={id}>
        {label}
        {required ? <span className="ml-0.5 text-saffron-700">*</span> : null}
      </label>
      {children(id)}
      {hint && !error ? <p className="mt-1 text-xs text-ink-500">{hint}</p> : null}
      {error ? (
        <p className="mt-1 text-xs font-medium text-[#8f1d1d]" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}

type TextInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  hint?: string
  error?: string | null
  wrapperClassName?: string
}

export function TextInput({
  label,
  hint,
  error,
  required,
  wrapperClassName,
  className = '',
  ...rest
}: TextInputProps) {
  return (
    <Field label={label} hint={hint} error={error} required={required} className={wrapperClassName}>
      {(id) => (
        <input
          {...rest}
          id={id}
          required={required}
          aria-invalid={error ? true : undefined}
          className={`field-control ${className}`}
        />
      )}
    </Field>
  )
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string
  hint?: string
  error?: string | null
  wrapperClassName?: string
  options: { label: string; value: string; count?: number }[]
  placeholder?: string
}

export function SelectInput({
  label,
  hint,
  error,
  required,
  options,
  placeholder,
  wrapperClassName,
  className = '',
  ...rest
}: SelectProps) {
  return (
    <Field label={label} hint={hint} error={error} required={required} className={wrapperClassName}>
      {(id) => (
        <select
          {...rest}
          id={id}
          required={required}
          aria-invalid={error ? true : undefined}
          className={`field-control ${className}`}
        >
          {placeholder !== undefined ? <option value="">{placeholder}</option> : null}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
              {option.count !== undefined ? ` (${option.count})` : ''}
            </option>
          ))}
        </select>
      )}
    </Field>
  )
}

type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string
  hint?: string
  error?: string | null
  wrapperClassName?: string
}

export function TextArea({
  label,
  hint,
  error,
  required,
  wrapperClassName,
  className = '',
  rows = 4,
  ...rest
}: TextAreaProps) {
  return (
    <Field label={label} hint={hint} error={error} required={required} className={wrapperClassName}>
      {(id) => (
        <textarea
          {...rest}
          id={id}
          rows={rows}
          required={required}
          aria-invalid={error ? true : undefined}
          className={`field-control ${className}`}
        />
      )}
    </Field>
  )
}

export function Checkbox({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}) {
  const id = useId()
  return (
    <div className="flex items-center gap-2">
      <input
        id={id}
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.checked)}
        className="h-4 w-4 rounded border-ink-300 text-ink-800 focus:ring-ink-500"
      />
      <label htmlFor={id} className="text-sm text-ink-700">
        {label}
      </label>
    </div>
  )
}

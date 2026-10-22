import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { STEP_FIELDS, toPayload, validate } from '../validation'

const EMPTY = {
  name: '',
  initial_investment: '',
  monthly_running_costs: '',
  selling_price: '',
  cost_per_unit: '',
  units_sold: '',
}

// Sample numbers = the worked example from the scope document (a test case, not real data).
const SAMPLE = {
  name: 'Sample business',
  initial_investment: '100000',
  monthly_running_costs: '30000',
  selling_price: '150',
  cost_per_unit: '50',
  units_sold: '250',
}

const STEPS = [
  {
    title: 'Investment and costs',
    intro: 'What did it take to start, and what does it cost to keep going each month?',
  },
  {
    title: 'Your product',
    intro: 'Think of your main product or service. If you sell several, use a typical one.',
  },
  {
    title: 'Sales',
    intro: 'How many did you sell in the last full month?',
  },
]

function Field({ id, label, help, prefix, suffix, value, error, onChange, inputMode = 'decimal', autoFocus }) {
  const describedBy = [help && `${id}-help`, error && `${id}-error`].filter(Boolean).join(' ')
  return (
    <div className={`field ${error ? 'has-error' : ''}`}>
      <label htmlFor={id}>{label}</label>
      {help && <p id={`${id}-help`} className="help">{help}</p>}
      <div className="input-wrap">
        {prefix && <span className="affix" aria-hidden="true">{prefix}</span>}
        <input
          id={id}
          name={id}
          type="text"
          inputMode={inputMode}
          autoComplete="off"
          value={value}
          onChange={(e) => onChange(id, e.target.value)}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={describedBy || undefined}
          autoFocus={autoFocus}
        />
        {suffix && <span className="affix affix-end" aria-hidden="true">{suffix}</span>}
      </div>
      {error && <p id={`${id}-error`} className="error" role="alert">{error}</p>}
    </div>
  )
}

export default function Wizard() {
  const { id } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [values, setValues] = useState(params.get('example') ? SAMPLE : EMPTY)
  const [errors, setErrors] = useState({})
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')
  const headingRef = useRef(null)

  useEffect(() => {
    if (!isEdit) return
    let alive = true
    api
      .getScenario(id)
      .then((s) => {
        if (!alive) return
        const v = { name: s.name }
        for (const [k, n] of Object.entries(s.inputs)) v[k] = String(n)
        setValues(v)
      })
      .catch((e) => alive && setFormError(e.message))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [id, isEdit])

  useEffect(() => {
    headingRef.current?.focus()
  }, [step])

  const onChange = (field, value) => {
    setValues((v) => ({ ...v, [field]: value }))
    if (errors[field]) setErrors((e) => ({ ...e, [field]: undefined }))
  }

  const next = async (e) => {
    e.preventDefault()
    setFormError('')
    const stepErrors = validate(values, STEP_FIELDS[step])
    if (Object.values(stepErrors).some(Boolean)) {
      setErrors(stepErrors)
      return
    }
    if (step < STEPS.length - 1) {
      setStep(step + 1)
      return
    }
    // Final step: check everything, then save.
    const all = validate(values)
    if (Object.keys(all).length) {
      setErrors(all)
      setStep(STEP_FIELDS.findIndex((fs) => fs.some((f) => all[f])))
      return
    }
    setSaving(true)
    try {
      const payload = toPayload(values)
      const saved = isEdit ? await api.updateScenario(id, payload) : await api.createScenario(payload)
      navigate(`/s/${saved.id}`)
    } catch (err) {
      setFormError(err.message)
      if (err.fields && Object.keys(err.fields).length) {
        setErrors(err.fields)
        const s = STEP_FIELDS.findIndex((fs) => fs.some((f) => err.fields[f]))
        if (s >= 0) setStep(s)
      }
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="muted center">Loading your numbers…</p>

  const last = step === STEPS.length - 1
  const f = (key, props) => (
    <Field id={key} value={values[key] ?? ''} error={errors[key]} onChange={onChange} {...props} />
  )

  return (
    <form className="card" onSubmit={next} noValidate>
      <div className="progress" aria-hidden="true">
        {STEPS.map((_, i) => (
          <span key={i} className={i <= step ? 'on' : ''} />
        ))}
      </div>
      <p className="eyebrow">Step {step + 1} of {STEPS.length}</p>
      <h1 className="title" tabIndex={-1} ref={headingRef}>{STEPS[step].title}</h1>
      <p className="muted">{STEPS[step].intro}</p>

      {step === 0 && (
        <>
          {f('name', {
            label: 'Business name (optional)',
            inputMode: 'text',
            autoFocus: !isEdit,
          })}
          {f('initial_investment', {
            label: 'Initial investment',
            help: 'Everything you spent to get started: equipment, fit-out, first stock.',
            prefix: '$',
          })}
          {f('monthly_running_costs', {
            label: 'Monthly running costs',
            help: 'Costs you pay every month whatever you sell: rent, wages, software, utilities.',
            prefix: '$',
            suffix: '/ month',
          })}
        </>
      )}

      {step === 1 && (
        <>
          {f('selling_price', {
            label: 'Selling price per unit',
            help: 'What a customer pays you for one unit.',
            prefix: '$',
          })}
          {f('cost_per_unit', {
            label: 'Cost per unit',
            help: 'What it costs you to make or buy one unit: materials, packaging, fees.',
            prefix: '$',
          })}
        </>
      )}

      {step === 2 &&
        f('units_sold', {
          label: 'Units sold this month',
          help: 'A whole number. Use 0 if you have not started selling yet.',
          inputMode: 'numeric',
          suffix: 'units',
        })}

      {formError && <p className="banner banner-error" role="alert">{formError}</p>}

      <div className="actions">
        {step > 0 ? (
          <button type="button" className="btn btn-ghost" onClick={() => setStep(step - 1)}>
            Back
          </button>
        ) : (
          <Link className="btn btn-ghost" to={isEdit ? `/s/${id}` : '/'}>Cancel</Link>
        )}
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving…' : last ? (isEdit ? 'Update results' : 'See my results') : 'Next'}
        </button>
      </div>
    </form>
  )
}

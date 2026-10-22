import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { formatMoney, formatNumber } from '../format'

const STATUS = {
  green: { label: 'Healthy', line: 'Comfortably above break-even.' },
  yellow: { label: 'Close call', line: 'Covering costs, with little to spare.' },
  red: { label: 'Losing money', line: 'Sales are not covering your costs yet.' },
}

function headline(d) {
  const gap = d.sales_gap_units
  if (gap > 0) return { big: formatNumber(gap), rest: `more ${gap === 1 ? 'sale' : 'sales'} a month to break even` }
  if (gap === 0) return { big: '0', rest: 'more sales needed — you are exactly at break-even' }
  return { big: formatNumber(-gap), rest: `${-gap === 1 ? 'sale' : 'sales'} above break-even this month` }
}

export default function Dashboard() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    let alive = true
    setData(null)
    setError('')
    api
      .getDashboard(id)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e.status === 404 ? 'We could not find these results. The link may be wrong.' : e.message))
    return () => {
      alive = false
    }
  }, [id])

  const share = async () => {
    const url = window.location.href
    try {
      if (navigator.share) await navigator.share({ title: 'Business Health Tracker', url })
      else {
        await navigator.clipboard.writeText(url)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    } catch {
      /* user cancelled the share sheet */
    }
  }

  if (error)
    return (
      <div className="card">
        <p className="banner banner-error" role="alert">{error}</p>
        <Link className="btn btn-primary btn-block" to="/new">Start again</Link>
      </div>
    )
  if (!data) return <p className="muted center">Working out your numbers…</p>

  const s = STATUS[data.status]
  const h = headline(data)
  const profit = data.monthly_profit

  return (
    <article className="dash">
      <p className="eyebrow">{data.name}</p>

      <section className={`status status-${data.status}`} aria-label={`Status: ${s.label}`}>
        <div className="light" aria-hidden="true">
          <span className="lamp lamp-red" />
          <span className="lamp lamp-yellow" />
          <span className="lamp lamp-green" />
        </div>
        <div>
          <h1 className="status-label">{s.label}</h1>
          <p className="status-line">{s.line}</p>
        </div>
      </section>

      <section className="headline">
        <p>
          <span className="big">{h.big}</span>
          <span className="rest">{h.rest}</span>
        </p>
        <p className="muted small">
          Break-even is {formatNumber(data.break_even_units)} units ({formatMoney(data.break_even_sales)} in
          sales). You sold {formatNumber(data.units_sold)}.
        </p>
      </section>

      <dl className="stats">
        <div>
          <dt>Monthly {profit < 0 ? 'loss' : 'profit'}</dt>
          <dd className={profit < 0 ? 'neg' : 'pos'}>
            {profit < 0 ? '−' : ''}
            {formatMoney(Math.abs(profit))}
          </dd>
        </div>
        <div>
          <dt>Payback period</dt>
          <dd>
            {data.payback_months === null
              ? 'Not reached'
              : data.payback_months === 0
                ? 'Already paid back'
                : `${formatNumber(data.payback_months)} months`}
          </dd>
          {data.payback_months === null && <p className="small muted">Shown once you make a monthly profit.</p>}
        </div>
      </dl>

      {data.suggestion && (
        <section className="suggestion">
          <h2>What to do next</h2>
          <p>{data.suggestion}</p>
          {data.other_suggestions.length > 0 && (
            <details>
              <summary>More ideas ({data.other_suggestions.length})</summary>
              <ul>
                {data.other_suggestions.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </details>
          )}
        </section>
      )}

      <div className="actions actions-stack">
        <Link className="btn btn-primary" to={`/s/${id}/edit`}>Edit my numbers</Link>
        <button type="button" className="btn btn-ghost" onClick={share}>
          {copied ? 'Link copied' : 'Share or save this link'}
        </button>
      </div>
      <p className="small muted center">Anyone with this link can see and edit these numbers.</p>
    </article>
  )
}

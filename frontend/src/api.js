const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, { status, fields } = {}) {
    super(message)
    this.status = status
    this.fields = fields || {}
  }
}

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`${API_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new ApiError(
      'Could not reach the server. Check your connection and try again. ' +
        '(On the free hosting tier the server can take up to a minute to wake up.)',
    )
  }
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new ApiError(body.message || 'Something went wrong.', {
      status: res.status,
      fields: body.fields,
    })
  }
  return body
}

export const api = {
  createScenario: (data) => request('/scenarios', { method: 'POST', body: JSON.stringify(data) }),
  updateScenario: (id, data) =>
    request(`/scenarios/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(data) }),
  getScenario: (id) => request(`/scenarios/${encodeURIComponent(id)}`),
  getDashboard: (id) => request(`/scenarios/${encodeURIComponent(id)}/dashboard`),
}

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { validate } from '../src/validation.js'

const cases = JSON.parse(
  readFileSync(new URL('../../shared/number_format_cases.json', import.meta.url), 'utf8'),
)
const field = 'monthly_running_costs'

for (const [text, expected] of Object.entries(cases.accepted)) {
  test(`accepts ${JSON.stringify(text)}`, () => {
    const errors = validate({ [field]: text }, [field])
    if (expected < 0) assert.match(errors[field], /cannot be negative/)
    else assert.equal(errors[field], undefined)
  })
}

for (const text of cases.rejected) {
  test(`rejects ${JSON.stringify(text)}`, () => {
    assert.match(validate({ [field]: text }, [field])[field], /must be a number/)
  })
}

import { useState } from 'react'

const CATEGORIES = ['coursework', 'marc_lessons', 'build']
const STAKES = ['high', 'ordinary']

const EMPTY_FORM = {
  title: '',
  category: '',
  stakes: '',
  deadline: '',
  effort_minutes: '',
}

function AddCommitmentForm() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState(null)
  const [confirmation, setConfirmation] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)
    setConfirmation(null)
    setSubmitting(true)

    try {
      const res = await fetch('/api/commitments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          commitments: [
            {
              title: form.title,
              category: form.category,
              stakes: form.stakes,
              deadline: form.deadline,
              effort_minutes: Number(form.effort_minutes),
              source: 'manual',
            },
          ],
        }),
      })

      const body = await res.json()

      if (!res.ok) {
        setError(body.error?.message ?? 'Could not add that.')
        return
      }

      setConfirmation(body.commitments[0].title)
      setForm(EMPTY_FORM)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="add-commitment-form">
      <h2>Add a commitment</h2>

      <label>
        Title
        <input
          type="text"
          required
          value={form.title}
          onChange={(e) => updateField('title', e.target.value)}
        />
      </label>

      <label>
        Category
        <select
          required
          value={form.category}
          onChange={(e) => updateField('category', e.target.value)}
        >
          <option value="" disabled>
            Choose one
          </option>
          {CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </label>

      <label>
        Stakes
        <select
          required
          value={form.stakes}
          onChange={(e) => updateField('stakes', e.target.value)}
        >
          <option value="" disabled>
            Choose one
          </option>
          {STAKES.map((stakes) => (
            <option key={stakes} value={stakes}>
              {stakes}
            </option>
          ))}
        </select>
      </label>

      <label>
        Deadline
        <input
          type="date"
          required
          value={form.deadline}
          onChange={(e) => updateField('deadline', e.target.value)}
        />
      </label>

      <label>
        Effort (minutes)
        <input
          type="number"
          min="1"
          step="1"
          required
          value={form.effort_minutes}
          onChange={(e) => updateField('effort_minutes', e.target.value)}
        />
      </label>

      <button type="submit" disabled={submitting}>
        {submitting ? 'Adding…' : 'Add commitment'}
      </button>

      {error && <p className="form-error">{error}</p>}
      {confirmation && <p className="form-confirmation">Added "{confirmation}".</p>}
    </form>
  )
}

export default AddCommitmentForm

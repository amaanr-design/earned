import { useEffect, useState } from 'react'
import { QUIET_REASON_TEXT } from './quietReasons'

// spec/api.md §3-§7 — the week-one card screen: GET /api/card, then Start
// (§4) and Tap A / Done (§7). Precommit (§5) is folded into the Start flow
// since Start's own response carries the prompt and options.

function CardScreen() {
  const [status, setStatus] = useState('loading') // loading | card | quiet | error
  const [card, setCard] = useState(null)
  const [quiet, setQuiet] = useState(null)
  const [precommit, setPrecommit] = useState(null) // { prompt, options_minutes } once Start returns it
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function loadCard() {
    setStatus('loading')
    setError(null)
    setPrecommit(null)
    try {
      const res = await fetch('/api/card')
      const body = await res.json()
      if (!res.ok) {
        setError(body.error?.message ?? 'Could not load the card.')
        setStatus('error')
        return
      }
      if (body.card) {
        setCard(body.card)
        setStatus('card')
      } else {
        setQuiet(body.quiet)
        setStatus('quiet')
      }
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  useEffect(() => {
    loadCard()
  }, [])

  async function postAction(path, payload) {
    const res = await fetch(`/api/cards/${card.id}/${path}`, {
      method: 'POST',
      headers: payload ? { 'Content-Type': 'application/json' } : undefined,
      body: payload ? JSON.stringify(payload) : undefined,
    })
    const body = await res.json()
    if (!res.ok) {
      throw new Error(body.error?.message ?? 'That did not go through.')
    }
    return body
  }

  async function handleStart() {
    setBusy(true)
    setError(null)
    try {
      const result = await postAction('start')
      setCard((prev) => ({ ...prev, state: 'started' }))
      setPrecommit(result.precommit)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handlePrecommit(minutes) {
    setBusy(true)
    setError(null)
    try {
      await postAction('precommit', { minutes })
      setPrecommit(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleDone() {
    setBusy(true)
    setError(null)
    try {
      await postAction('done')
      await loadCard()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (status === 'loading') {
    return <section className="card-screen" aria-busy="true" />
  }

  if (status === 'error') {
    return (
      <section className="card-screen">
        <p className="form-error">{error}</p>
      </section>
    )
  }

  if (status === 'quiet') {
    return (
      <section className="card-screen">
        <p className="quiet-line">{QUIET_REASON_TEXT[quiet.reason]}</p>
      </section>
    )
  }

  return (
    <section className="card-screen">
      <p className="card-copy">{card.copy_text}</p>

      {precommit && (
        <div className="precommit">
          <p>{precommit.prompt}</p>
          <div className="precommit-options">
            {precommit.options_minutes.map((minutes) => (
              <button key={minutes} disabled={busy} onClick={() => handlePrecommit(minutes)}>
                {minutes} min
              </button>
            ))}
          </div>
        </div>
      )}

      {!precommit && (
        <div className="card-actions">
          {card.state === 'offered' && (
            <button disabled={busy} onClick={handleStart}>
              Start
            </button>
          )}
          <button disabled={busy} onClick={handleDone}>
            Done
          </button>
        </div>
      )}

      {error && <p className="form-error">{error}</p>}
    </section>
  )
}

export default CardScreen

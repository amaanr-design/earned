import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <section id="center">
      <div>
        <h1>Earned</h1>
        {health && <p>Backend status: {health.status}</p>}
        {error && <p>Backend unreachable: {error}</p>}
      </div>
    </section>
  )
}

export default App

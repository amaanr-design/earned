import './App.css'
import AddCommitmentForm from './AddCommitmentForm'
import CardScreen from './CardScreen'

function App() {
  return (
    <section id="center">
      <div>
        <h1>Earned</h1>
        <CardScreen />
        <AddCommitmentForm />
      </div>
    </section>
  )
}

export default App

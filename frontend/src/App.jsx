
import { useState } from 'react'
import DriverLogin from './components/DriverLogin'
import ChatInterface from './components/ChatInterface'
import AgentDashboard from './components/AgentDashboard'

function App() {
  const [view, setView] = useState('login') // 'login', 'chat', 'agent'
  const [driverId, setDriverId] = useState(null)

  const handleDriverLogin = (id) => {
    setDriverId(id)
    setView('chat')
  }

  return (
    <>
      {view === 'login' && (
        <>
          <DriverLogin onLogin={handleDriverLogin} />
          <div style={{ position: 'fixed', bottom: '20px', right: '20px' }}>
            <button
              onClick={() => setView('agent')}
              style={{ width: 'auto', fontSize: '0.8em', background: 'rgba(255,255,255,0.1)', padding: '8px 15px' }}
            >
              👮 Agent Portal
            </button>
          </div>
        </>
      )}

      {view === 'chat' && (
        <ChatInterface
          driverId={driverId}
          onLogout={() => { setDriverId(null); setView('login'); }}
        />
      )}

      {view === 'agent' && (
        <AgentDashboard onBack={() => setView('login')} />
      )}
    </>
  )
}

export default App

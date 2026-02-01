import { Routes, Route, Navigate } from 'react-router-dom'
import DriverLogin from './components/DriverLogin'
import PhoneLogin from './components/PhoneLogin'
import ChatInterface from './components/ChatInterface'
import AgentDashboard from './components/AgentDashboard'
import AgentChat from './components/AgentChat'

function App() {
  return (
    <Routes>
      <Route path="/" element={<DriverLogin />} />
      <Route path="/phone" element={<PhoneLogin />} />
      <Route path="/chat" element={<ChatInterface />} />
      <Route path="/agent" element={<AgentDashboard />} />
      <Route path="/agent/chat/:driverId" element={<AgentChat />} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default App

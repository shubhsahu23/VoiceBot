
import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import axios from 'axios'

const AgentDashboard = () => {
    const navigate = useNavigate()
    const [tickets, setTickets] = useState([])
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState('OPEN')

    useEffect(() => {
        fetchTickets()
    }, [activeTab])

    // Auto-refresh every 5 seconds
    useEffect(() => {
        const interval = setInterval(fetchTickets, 5000)
        return () => clearInterval(interval)
    }, [activeTab])

    const fetchTickets = async () => {
        try {
            const response = await axios.get(`${import.meta.env.VITE_API_URL}/agent/escalations?status=${activeTab}`)
            setTickets(response.data)
            setLoading(false)
        } catch (err) {
            console.error("Failed to fetch tickets:", err)
            setLoading(false)
        }
    }

    const handleAccept = async (ticketId, driverId) => {
        try {
            await axios.post(`${import.meta.env.VITE_API_URL}/agent/accept`, { ticket_id: ticketId })
            navigate(`/agent/chat/${driverId}`)
        } catch (err) {
            console.error("Failed to accept ticket:", err)
            alert("Failed to accept ticket")
        }
    }

    return (
        <div className="card" style={{ width: '1000px', maxWidth: '90%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2 style={{ margin: 0, textAlign: 'left' }}>🛡️ Agent Dashboard</h2>
                <button
                    onClick={() => navigate('/')}
                    className="secondary"
                    style={{ width: 'auto' }}
                >
                    Back to App
                </button>
            </div>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '15px' }}>
                <button
                    onClick={() => { setActiveTab('OPEN'); setLoading(true); }}
                    style={{
                        background: activeTab === 'OPEN' ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
                        color: activeTab === 'OPEN' ? '#ef4444' : 'var(--text-secondary)',
                        border: activeTab === 'OPEN' ? '1px solid #ef4444' : '1px solid transparent',
                        width: 'auto',
                        padding: '8px 20px',
                        marginTop: 0,
                        boxShadow: 'none'
                    }}
                >
                    Open Tickets
                </button>
                <button
                    onClick={() => { setActiveTab('RESOLVED'); setLoading(true); }}
                    style={{
                        background: activeTab === 'RESOLVED' ? 'rgba(34, 197, 94, 0.2)' : 'transparent',
                        color: activeTab === 'RESOLVED' ? '#22c55e' : 'var(--text-secondary)',
                        border: activeTab === 'RESOLVED' ? '1px solid #22c55e' : '1px solid transparent',
                        width: 'auto',
                        padding: '8px 20px',
                        marginTop: 0,
                        boxShadow: 'none'
                    }}
                >
                    Resolved History
                </button>
            </div>

            {loading ? (
                <p style={{ textAlign: 'center' }}>Loading escalations...</p>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                    {tickets.length === 0 ? (
                        <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px', opacity: 0.6 }}>
                            <h3>All clear!</h3>
                            <p>No {activeTab.toLowerCase()} escalations.</p>
                        </div>
                    ) : (
                        tickets.map(ticket => (
                            <div key={ticket.id} style={{
                                background: 'rgba(255, 255, 255, 0.05)',
                                padding: '20px',
                                borderRadius: '12px',
                                borderLeft: `4px solid ${activeTab === 'OPEN' ? '#ef4444' : '#22c55e'}`
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                                    <span style={{ fontWeight: 'bold' }}>{ticket.driver_id}</span>
                                    <span style={{ fontSize: '0.8em', opacity: 0.6 }}>{new Date(ticket.created_at).toLocaleTimeString()}</span>
                                </div>
                                <div style={{ marginBottom: '10px' }}>
                                    <span className="intent-badge" style={{ marginLeft: 0, background: activeTab === 'OPEN' ? '#ef4444' : '#22c55e', color: 'white' }}>
                                        {ticket.intent}
                                    </span>
                                    <span style={{ marginLeft: '10px', fontSize: '0.9em', opacity: 0.8 }}>
                                        {Math.round(ticket.confidence * 100)}% Confidence
                                    </span>
                                </div>
                                <p style={{ fontSize: '0.9em', lineHeight: '1.4', opacity: 0.9, maxHeight: '100px', overflowY: 'auto' }}>
                                    "{ticket.summary}"
                                </p>
                                <button
                                    style={{ marginTop: '15px', fontSize: '0.9em', background: activeTab === 'OPEN' ? '' : 'rgba(255,255,255,0.1)' }}
                                    onClick={() => {
                                        if (activeTab === 'OPEN') {
                                            handleAccept(ticket.id, ticket.driver_id)
                                        } else {
                                            navigate(`/agent/chat/${ticket.driver_id}`)
                                        }
                                    }}
                                >
                                    {activeTab === 'OPEN' ? 'Take Action' : 'View Chat'}
                                </button>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    )
}

export default AgentDashboard

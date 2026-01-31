
import { useState, useEffect } from 'react'
import axios from 'axios'

const AgentDashboard = ({ onBack }) => {
    const [tickets, setTickets] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchTickets()
    }, [])

    // Auto-refresh every 5 seconds
    useEffect(() => {
        const interval = setInterval(fetchTickets, 5000)
        return () => clearInterval(interval)
    }, [])

    const fetchTickets = async () => {
        try {
            const response = await axios.get('http://localhost:8000/agent/escalations')
            setTickets(response.data)
            setLoading(false)
        } catch (err) {
            console.error("Failed to fetch tickets:", err)
            setLoading(false)
        }
    }

    return (
        <div className="card" style={{ width: '1000px', maxWidth: '90%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2 style={{ margin: 0 }}>🛡️ Agent Dashboard</h2>
                <button
                    onClick={onBack}
                    style={{ width: 'auto', background: 'rgba(255,255,255,0.1)' }}
                >
                    Back to App
                </button>
            </div>

            {loading ? (
                <p style={{ textAlign: 'center' }}>Loading escalations...</p>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                    {tickets.length === 0 ? (
                        <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px', opacity: 0.6 }}>
                            <h3>All clear!</h3>
                            <p>No pending escalations.</p>
                        </div>
                    ) : (
                        tickets.map(ticket => (
                            <div key={ticket.id} style={{
                                background: 'rgba(255, 255, 255, 0.05)',
                                padding: '20px',
                                borderRadius: '12px',
                                borderLeft: '4px solid #ef4444'
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                                    <span style={{ fontWeight: 'bold' }}>{ticket.driver_id}</span>
                                    <span style={{ fontSize: '0.8em', opacity: 0.6 }}>{new Date(ticket.created_at).toLocaleTimeString()}</span>
                                </div>
                                <div style={{ marginBottom: '10px' }}>
                                    <span className="intent-badge" style={{ marginLeft: 0, background: '#ef4444', color: 'white' }}>
                                        {ticket.intent}
                                    </span>
                                    <span style={{ marginLeft: '10px', fontSize: '0.9em', opacity: 0.8 }}>
                                        {Math.round(ticket.confidence * 100)}% Confidence
                                    </span>
                                </div>
                                <p style={{ fontSize: '0.9em', lineHeight: '1.4', opacity: 0.9, maxHeight: '100px', overflowY: 'auto' }}>
                                    "{ticket.summary}"
                                </p>
                                <button style={{ marginTop: '15px', fontSize: '0.9em' }}>
                                    Take Action
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

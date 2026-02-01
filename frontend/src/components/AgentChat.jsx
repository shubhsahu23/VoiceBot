
import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'

const AgentChat = () => {
    const { driverId } = useParams()
    const navigate = useNavigate()
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const messagesEndRef = useRef(null)

    useEffect(() => {
        fetchHistory()
        const interval = setInterval(fetchHistory, 3000) // Poll every 3 seconds
        return () => clearInterval(interval)
    }, [driverId])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const fetchHistory = async () => {
        try {
            const response = await axios.get(`http://localhost:8000/chat/history/${driverId}`)
            setMessages(response.data)
        } catch (err) {
            console.error("Failed to fetch history:", err)
        }
    }

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!input.trim()) return

        const text = input
        setInput('')

        // Optimistic update
        setMessages(prev => [...prev, { sender: 'agent', text: text, timestamp: new Date().toISOString() }])

        try {
            await axios.post('http://localhost:8000/agent/message', {
                driver_id: driverId,
                message: text
            })
            fetchHistory() // Sync with server
        } catch (err) {
            console.error("Failed to send message:", err)
            // Rollback optimistic update if needed, or show error
        }
    }

    return (
        <div className="card chat-container" style={{ maxWidth: '800px', margin: '20px auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '10px' }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.2em' }}>Live Support</h2>
                    <span style={{ fontSize: '0.8em', opacity: 0.6 }}>Chatting with {driverId}</span>
                </div>
                <button
                    onClick={() => navigate('/agent')}
                    style={{ width: 'auto', padding: '5px 15px', fontSize: '0.9em', background: 'rgba(255,255,255,0.1)', marginRight: '10px' }}
                >
                    Back
                </button>
                <button
                    onClick={async () => {
                        if (confirm("End this chat session?")) {
                            try {
                                await axios.post('http://localhost:8000/agent/resolve', { driver_id: driverId })
                                navigate('/agent')
                            } catch (e) {
                                alert("Failed to end chat")
                            }
                        }
                    }}
                    style={{ width: 'auto', padding: '5px 15px', fontSize: '0.9em', background: '#ef4444', color: 'white', border: 'none' }}
                >
                    End Chat
                </button>
            </div>

            <div className="messages" style={{ height: '400px', overflowY: 'auto' }}>
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.sender === 'agent' ? 'bot-msg' : (msg.sender === 'user' ? 'user-msg' : 'bot-msg')}`}
                        style={{
                            background: msg.sender === 'agent' ? '#0ea5e9' : (msg.sender === 'user' ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.05)'),
                            alignSelf: msg.sender === 'agent' ? 'flex-end' : (msg.sender === 'user' ? 'flex-end' : 'flex-start'),
                            flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row'
                        }}
                    >
                        {/* Adjust styling logic: 
                            User (driver) messages -> Left aligned (standard for support view) or Right?
                            Standard: 
                            - Me (Agent) -> Right
                            - Them (Driver) -> Left
                            - Bot (Auto) -> Center/Left with distinction
                         */}
                    </div>
                ))}
                {/* Re-render messages with correct standard chat logic for Agent View */}
                {messages.map((msg, idx) => {
                    const isMe = msg.sender === 'agent'
                    const isUser = msg.sender === 'user'
                    const isBot = msg.sender === 'bot'

                    return (
                        <div key={idx}
                            style={{
                                display: 'flex',
                                justifyContent: isMe ? 'flex-end' : 'flex-start',
                                marginBottom: '10px'
                            }}
                        >
                            <div style={{
                                maxWidth: '70%',
                                padding: '10px 15px',
                                borderRadius: '12px',
                                background: isMe ? '#0ea5e9' : (isBot ? '#334155' : 'rgba(255,255,255,0.1)'),
                                color: 'white',
                                borderTopRightRadius: isMe ? '2px' : '12px',
                                borderTopLeftRadius: isMe ? '12px' : '2px'
                            }}>
                                <div style={{ fontSize: '0.7em', opacity: 0.7, marginBottom: '4px' }}>
                                    {isMe ? 'You' : (isBot ? 'Bot' : driverId)}
                                </div>
                                {msg.text}
                            </div>
                        </div>
                    )
                })}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={sendMessage} className="input-area" style={{ marginTop: '20px' }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your message..."
                    autoFocus
                />
                <button type="submit" disabled={!input.trim()}>Send</button>
            </form>
        </div>
    )
}

export default AgentChat

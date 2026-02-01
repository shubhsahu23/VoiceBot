
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const ChatInterface = () => {
    const navigate = useNavigate()
    const location = useLocation()
    const driverId = location.state?.driverId

    const [messages, setMessages] = useState([
        { role: 'bot', text: `Hello! I'm your assistant. How can I help you today?` }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [isListening, setIsListening] = useState(false)
    const [startTime] = useState(Date.now())  // Track when this session started locally
    const messagesEndRef = useRef(null)

    if (!driverId) {
        return <Navigate to="/" />
    }

    const startListening = () => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
            const recognition = new SpeechRecognition()
            recognition.continuous = false
            recognition.lang = 'en-US'

            recognition.onstart = () => setIsListening(true)
            recognition.onend = () => setIsListening(false)

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript
                setInput(transcript)
            }

            recognition.start()
        } else {
            alert("Your browser does not support voice input.")
        }
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!input.trim()) return

        const userMsg = input
        setMessages(prev => [...prev, { role: 'user', text: userMsg }])
        setInput('')
        setLoading(true)

        try {
            const response = await axios.post(`${import.meta.env.VITE_API_URL}/chat`, {
                message: userMsg,
                driver_id: driverId
            })

            const data = response.data

            // Only add bot response if it exists (live chat might not return immediate response)
            if (data.response) {
                setMessages(prev => [...prev, {
                    role: 'bot',
                    text: data.response,
                    intent: data.intent,
                    escalate: data.escalate
                }])
            }

            // Play Audio if available
            if (data.audio) {
                try {
                    const audio = new Audio(`data:audio/mp3;base64,${data.audio}`)
                    audio.play()
                } catch (audioErr) {
                    console.error("Failed to play audio:", audioErr)
                }
            }

            // Handoff Simulation (Only if strictly escalated by AI, not live chat)
            if (data.escalate && !data.live_mode) {
                setTimeout(() => {
                    setMessages(prev => [...prev, {
                        role: 'bot',
                        text: "⚠️ Escalation triggered. Connecting you to a human agent... Please wait.",
                        intent: "system"
                    }])
                }, 1500)
            }

        } catch (err) {
            setMessages(prev => [...prev, { role: 'bot', text: "Sorry, I'm having trouble connecting to the server." }])
        } finally {
            setLoading(false)
        }
    }

    // Polling and History logic
    useEffect(() => {
        if (!driverId) return;

        const fetchHistory = async () => {
            try {
                const response = await axios.get(`https://voicebot-0khz.onrender.com/chat/history/${driverId}`)

                // Check if the chat was ended by agent
                const lastMsg = response.data[response.data.length - 1]
                if (lastMsg && lastMsg.text === "Chat ended by agent." && lastMsg.sender === 'system') {
                    // Force a local update to include this message then stop
                    // Filter one last time to make sure we show the relevant history
                    const history = response.data
                        .filter(msg => !msg.timestamp || new Date(msg.timestamp).getTime() > startTime)
                        .map(msg => ({
                            role: msg.sender === 'user' ? 'user' : (msg.sender === 'system' ? 'system' : 'bot'),
                            text: msg.text,
                            sender: msg.sender
                        }))

                    if (history.length > 0) setMessages(history)
                    return
                }

                // Normal Flow: Filter history based on local session start time
                // (Assumes backend messages have valid timestamps)
                const history = response.data
                    .filter(msg => !msg.timestamp || new Date(msg.timestamp).getTime() > startTime)
                    .map(msg => ({
                        role: msg.sender === 'user' ? 'user' : 'bot',
                        text: msg.text,
                        sender: msg.sender
                    }))

                if (history.length > 0) {
                    // If purely new session, we might want to keep the initial greeting visible if history is empty
                    // But if history exists, we show history.
                    setMessages(history.length > 0 ? history : messages)
                }

            } catch (err) {
                console.error("Failed to fetch history:", err)
            }
        }

        fetchHistory()
        const interval = setInterval(fetchHistory, 3000)
        return () => clearInterval(interval)
    }, [driverId, startTime])


    return (
        <div className="card chat-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '10px' }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.2em' }}>Support Chat</h2>
                    <span style={{ fontSize: '0.8em', opacity: 0.6 }}>Logged in as {driverId}</span>
                </div>
                <button
                    onClick={() => navigate('/')}
                    style={{ width: 'auto', padding: '5px 10px', fontSize: '0.8em', background: 'rgba(255,255,255,0.1)', color: 'white' }}
                >
                    Logout
                </button>
            </div>

            <div className="messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role === 'user' ? 'user-msg' : (msg.role === 'system' ? 'system-msg' : 'bot-msg')}`}
                        style={msg.role === 'system' ? { alignSelf: 'center', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid #ef4444' } : {}}
                    >
                        <span>{msg.text}</span>
                        {msg.intent && (
                            <span className="intent-badge">
                                {msg.intent} {msg.escalate ? '⚠️' : ''}
                            </span>
                        )}
                        {msg.sender === 'agent' && <div style={{ fontSize: '0.7em', marginTop: '4px', opacity: 0.7 }}>Agent</div>}
                    </div>
                ))}

                {loading && <div className="message bot-msg">Thinking...</div>}

                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={sendMessage} className="input-area" style={{ opacity: 1, pointerEvents: 'auto' }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your question..."
                    disabled={loading}
                />
                <button type="button" onClick={startListening} disabled={loading} style={{ background: isListening ? '#ef4444' : '' }}>
                    {isListening ? '🛑' : '🎤'}
                </button>
                <button type="submit" disabled={loading}>Send</button>
            </form>
        </div>
    )
}

export default ChatInterface

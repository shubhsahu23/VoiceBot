
import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const ChatInterface = ({ driverId, onLogout }) => {
    const [messages, setMessages] = useState([
        { role: 'bot', text: `Hello! I'm your assistant. How can I help you today?` }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [isListening, setIsListening] = useState(false)
    const messagesEndRef = useRef(null)

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
            const response = await axios.post('http://localhost:8000/chat', {
                message: userMsg,
                driver_id: driverId
            })

            const data = response.data
            setMessages(prev => [...prev, {
                role: 'bot',
                text: data.response,
                intent: data.intent,
                escalate: data.escalate
            }])

            // Play Audio if available
            if (data.audio) {
                try {
                    const audio = new Audio(`data:audio/mp3;base64,${data.audio}`)
                    audio.play()
                } catch (audioErr) {
                    console.error("Failed to play audio:", audioErr)
                }
            }

            // Handoff Simulation
            if (data.escalate) {
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

    return (
        <div className="card chat-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '10px' }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.2em' }}>Support Chat</h2>
                    <span style={{ fontSize: '0.8em', opacity: 0.6 }}>Logged in as {driverId}</span>
                </div>
                <button
                    onClick={onLogout}
                    style={{ width: 'auto', padding: '5px 10px', fontSize: '0.8em', background: 'rgba(255,255,255,0.1)', color: 'white' }}
                >
                    Logout
                </button>
            </div>

            <div className="messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role === 'user' ? 'user-msg' : 'bot-msg'}`}>
                        <span>{msg.text}</span>
                        {msg.intent && (
                            <span className="intent-badge">
                                {msg.intent} {msg.escalate ? '⚠️' : ''}
                            </span>
                        )}
                    </div>
                ))}
                {loading && <div className="message bot-msg">Thinking...</div>}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={sendMessage} className="input-area">
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

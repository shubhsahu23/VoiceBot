import { useNavigate } from 'react-router-dom'
import { useState, useRef } from 'react'
import axios from 'axios'
import { Car, Mic, MicOff } from 'lucide-react'

const DriverLogin = () => {
  const navigate = useNavigate()
  const [inputId, setInputId] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [lang] = useState('en-US') // defaulting to en-US for simplicity in UI, can expand later

  const recognitionRef = useRef(null)

  const speak = (text) => {
    if (!('speechSynthesis' in window)) return
    try {
      window.speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(text)
      window.speechSynthesis.speak(u)
    } catch (e) {
      // ignore
    }
  }

  const startListening = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      const recognition = new SpeechRecognition()
      recognitionRef.current = recognition
      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = lang

      recognition.onstart = () => setIsListening(true)
      recognition.onend = () => setIsListening(false)

      recognition.onresult = (event) => {
        const raw = event.results[0][0].transcript || ''
        const candidate = raw.replace(/[^\p{L}0-9\s]/gu, '').toUpperCase().replace(/\s+/g, '')
        if (candidate) {
          setInputId(candidate)
          handleSubmit(candidate)
        }
      }

      recognition.start()
    } else {
      alert('Voice input not supported.')
    }
  }

  const handleSubmit = async (driverId) => {
    const id = (driverId || inputId || '').trim()
    if (!id) {
      setError('Please enter a Driver ID')
      return
    }

    setError('')
    setLoading(true)

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/validate-driver`,
        { driver_id: id }
      )

      if (response.data.valid) {
        navigate('/chat', { state: { driverId: id } })
      }
    } catch (err) {
      const msg = err.response?.data?.detail?.message || 'Verification failed.'
      setError(msg)
      speak(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ width: '100%' }}>
      <div className="card">
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <div style={{
            width: '50px',
            height: '50px',
            background: 'rgba(34, 197, 94, 0.1)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 15px auto',
            color: 'var(--primary-color)'
          }}>
            <Car size={24} />
          </div>
          <h2>Driver Login</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9em', marginTop: '5px' }}>
            Get instant voice support for your EV
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <label>Driver ID</label>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              placeholder="Enter Driver ID (e.g. DRV003)"
              value={inputId}
              onChange={(e) => setInputId(e.target.value.toUpperCase())}
              disabled={loading}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit(inputId)}
              style={{ paddingRight: '50px' }} // Space for mic icon
            />
            <button
              onClick={startListening}
              style={{
                position: 'absolute',
                right: '5px',
                top: '12px', // Adjusted alignment
                width: 'auto',
                background: 'transparent',
                border: 'none',
                boxShadow: 'none',
                color: isListening ? '#ef4444' : 'var(--text-secondary)',
                padding: '10px',
                margin: 0
              }}
              title="Speak ID"
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
          </div>

          {error && <div style={{ color: '#ef4444', fontSize: '0.9em', marginTop: '5px' }}>{error}</div>}

          <button
            onClick={() => handleSubmit(inputId)}
            disabled={loading}
            style={{ marginTop: '20px' }}
          >
            {loading ? 'Verifying...' : 'Sign In'}
          </button>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
          </div>
        </div>
      </div>

      <div style={{ position: 'fixed', bottom: '20px', right: '20px' }}>
        <button
          onClick={() => navigate('/agent')}
          className="secondary"
          style={{ width: 'auto', fontSize: '0.8em', padding: '8px 15px' }}
        >
          👮 Agent Portal
        </button>
      </div>
    </div>
  )
}

export default DriverLogin

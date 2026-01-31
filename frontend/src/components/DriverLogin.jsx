import { useState } from 'react'
import axios from 'axios'

const DriverLogin = ({ onLogin }) => {
  const [inputId, setInputId] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)

  const startListening = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition
      const recognition = new SpeechRecognition()

      recognition.continuous = false
      recognition.lang = 'en-US'

      recognition.onstart = () => setIsListening(true)
      recognition.onend = () => setIsListening(false)

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript
          .replace(/\s+/g, '')
          .toUpperCase()
        setInputId(transcript)
      }

      recognition.start()
    } else {
      alert('Your browser does not support voice input.')
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await axios.post(
        'http://localhost:8000/validate-driver',
        { driver_id: inputId }
      )

      if (response.data.valid) {
        onLogin(inputId)
      }
    } catch (err) {
      setError(
        err.response?.data?.detail?.message ||
          'Verification failed. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a, #020617)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'Inter, system-ui, sans-serif'
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '420px',
          background: '#020617',
          borderRadius: '18px',
          padding: '32px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
          border: '1px solid #1e293b'
        }}
      >
        <h1
          style={{
            textAlign: 'center',
            color: '#38bdf8',
            fontSize: '26px',
            marginBottom: '6px'
          }}
        >
          ⚡ PowerSwap
        </h1>

        <p
          style={{
            textAlign: 'center',
            color: '#94a3b8',
            fontSize: '14px',
            marginBottom: '28px'
          }}
        >
          Driver Verification Portal
        </p>

        <form onSubmit={handleLogin}>
          <label
            style={{
              display: 'block',
              color: '#e5e7eb',
              fontSize: '14px',
              marginBottom: '8px'
            }}
          >
            Driver ID
          </label>

          <input
            type="text"
            value={inputId}
            onChange={(e) => setInputId(e.target.value.toUpperCase())}
            placeholder="e.g. DRV003"
            autoFocus
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: '10px',
              border: '1px solid #334155',
              background: '#020617',
              color: '#e5e7eb',
              fontSize: '15px',
              outline: 'none',
              marginBottom: '10px'
            }}
          />

          <button
            type="button"
            onClick={startListening}
            style={{
              width: '100%',
              padding: '12px',
              borderRadius: '10px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              background: isListening ? '#dc2626' : '#1f2933',
              color: '#e5e7eb',
              marginBottom: '16px',
              transition: '0.2s ease'
            }}
          >
            {isListening ? '🛑 Listening...' : '🎤 Speak Driver ID'}
          </button>

          {error && (
            <div
              style={{
                background: '#7f1d1d',
                color: '#fecaca',
                padding: '10px',
                borderRadius: '8px',
                fontSize: '13px',
                textAlign: 'center',
                marginBottom: '16px'
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !inputId}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: '12px',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '15px',
              fontWeight: 600,
              background: loading ? '#334155' : '#38bdf8',
              color: '#020617',
              transition: '0.2s ease'
            }}
          >
            {loading ? 'Verifying...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default DriverLogin

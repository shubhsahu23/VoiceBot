import { useNavigate } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const DriverLogin = () => {
  const navigate = useNavigate()
  const [inputId, setInputId] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [lang, setLang] = useState('en-US') // en-US, hi-IN, mr-IN
  const [lastTranscript, setLastTranscript] = useState('')
  const recognitionRef = useRef(null)

  const speak = (text, voiceLang = lang) => {
    if (!('speechSynthesis' in window)) return
    try {
      window.speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(text)
      u.lang = voiceLang
      window.speechSynthesis.speak(u)
    } catch (e) {
      // ignore
    }
  }

  // Localized UI and prompt strings
  const TRANSLATIONS = {
    'en-US': {
      listenPrompt: 'Please say your driver ID after the beep.',
      capturedId: (id) => `Captured ID ${id}. Say login to continue or press Continue.`,
      submitMsg: 'Submitting your ID now.',
      noId: 'No ID detected. Please say your ID or type it.',
      voiceFailed: 'Voice recognition failed. Please try again or type manually.',
      speakButton: '🎤 Speak Driver ID',
      playPrompt: 'Play Prompt',
      lastHeard: 'Last heard:',
      placeholder: 'e.g. DRV003',
      continue: 'Continue',
      verifying: 'Verifying...',
      verified: 'Driver verified.',
      listening: 'Listening...',
      verifyFailed: 'Verification failed. Please try again.'
    },
    'hi-IN': {
      listenPrompt: 'कृपया अपना ड्राइवर आईडी बोलें।',
      capturedId: (id) => `आईडी ${id} सुन ली गई। लॉगिन कहें या Continue दबाएँ।`,
      submitMsg: 'सबमिट कर रहा हूँ, कृपया प्रतीक्षा करें।',
      noId: 'कोई आईडी नहीं मिली। कृपया बोलें या टाइप करें।',
      voiceFailed: 'वॉइस पहचान विफल रही। कृपया पुनः प्रयास करें या टाइप करें।',
      speakButton: '🎤 बोलकर आईडी कहें',
      playPrompt: 'प्रॉम्प्ट चलाएँ',
      lastHeard: 'आखिरी सुना गया:',
      placeholder: 'उदा. DRV003',
      continue: 'जारी रखें',
      verifying: 'जाँच हो रही है...',
      verified: 'ड्राइवर सत्यापित।',
      listening: 'सुन रहे हैं...',
      verifyFailed: 'सत्यापन विफल। कृपया पुनः प्रयास करें।'
    },
    'mr-IN': {
      listenPrompt: 'कृपया आपला ड्रायव्हर आयडी बोला.',
      capturedId: (id) => `आयडी ${id} नोंदवली. लॉगिन म्हणा किंवा Continue दाबा.`,
      submitMsg: 'सबमिट करत आहे, थांबा.',
      noId: 'कोणतीही ID सापडली नाही. कृपया बोला किंवा टाइप करा.',
      voiceFailed: 'वॉइस ओळख अयशस्वी. कृपया पुन्हा प्रयत्न करा किंवा टाइप करा.',
      speakButton: '🎤 आयडी बोला',
      playPrompt: 'प्रॉम्प्ट चालवा',
      lastHeard: 'शेवटचे ऐकले:',
      placeholder: 'उदा. DRV003',
      continue: 'सुरू ठेवा',
      verifying: 'जाचणी चालू आहे...',
      verified: 'ड्रायव्हर सत्यापित झाला.',
      listening: 'ऐकत आहे...',
      verifyFailed: 'सत्यापन अयशस्वी. कृपया पुन्हा प्रयत्न करा.'
    }
  }

  const t = (key, ...args) => {
    const L = TRANSLATIONS[lang] || TRANSLATIONS['en-US']
    const val = L[key]
    if (typeof val === 'function') return val(...args)
    return val
  }

  const startListening = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition
      const recognition = new SpeechRecognition()
      recognitionRef.current = recognition

      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = lang

      recognition.onstart = () => {
        setIsListening(true)
        speak(t('listenPrompt'), lang)
      }

      recognition.onend = () => setIsListening(false)

      recognition.onresult = (event) => {
        const raw = event.results[0][0].transcript || ''
        setLastTranscript(raw)

        // Normalize transcript: remove non-alphanumeric except Devanagari letters and spaces
        const transcript = raw.replace(/[^\p{L}0-9\s]/gu, '').toUpperCase()
        const candidate = transcript.replace(/\s+/g, '')

        // If it looks like an ID (letters/digits, reasonable length) auto-fill
        if (/^[A-Z0-9]{2,10}$/.test(candidate)) {
          setInputId(candidate)
          speak(t('capturedId', candidate), lang)
        }

        // Detect submit words in English or Devanagari (लॉगिन/सबमिट/जमा)
        if (/\b(LOGIN|SUBMIT|CONTINUE|ENTER)\b/i.test(raw) || /लॉगिन|सबमिट|जमा|प्रवेश|पाठवा|सबमिट/i.test(raw)) {
          // submit using candidate if present, otherwise current input
          const idToUse = candidate || inputId
          if (!idToUse) {
            const msg = t('noId')
            setError(msg)
            speak(msg, lang)
            return
          }
          speak(t('submitMsg'), lang)
          handleSubmit(idToUse)
        }
      }

      recognition.onerror = (e) => {
        const msg = t('voiceFailed')
        setError(msg)
        speak(msg, lang)
        setIsListening(false)
      }

      recognition.start()
    } else {
      alert('Your browser does not support voice input.')
    }
  }

  const handleSubmit = async (driverId) => {
    const id = (driverId || inputId || '').trim()
    if (!id) {
      const msg = lang === 'hi-IN' ? 'कोई आईडी नहीं मिली।' : (lang === 'mr-IN' ? 'ID मिळाली नाही.' : 'No Driver ID provided.')
      setError(msg)
      speak(msg, lang)
      return
    }

    setError('')
    setLoading(true)

    try {
      const response = await axios.post(
        'http://localhost:8000/validate-driver',
        { driver_id: id }
      )

      if (response.data.valid) {
        speak(t('verified'), lang)
        navigate('/chat', { state: { driverId: id } })
      }
    } catch (err) {
      const msg = err.response?.data?.detail?.message || t('verifyFailed')
      setError(msg)
      speak(msg, lang)
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = (e) => {
    e.preventDefault()
    handleSubmit(inputId)
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
            Driver
          </label>

          <input
            type="text"
            value={inputId}
            onChange={(e) => setInputId(e.target.value.toUpperCase())}
            placeholder={t('placeholder')}
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

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px' }}>


            <button type="button" onClick={startListening} style={{ flex: 1, padding: '12px', borderRadius: '10px', border: 'none', cursor: 'pointer', fontSize: '14px', fontWeight: 500, background: isListening ? '#dc2626' : '#1f2933', color: '#e5e7eb', transition: '0.2s ease' }}>{isListening ? `🛑 ${t('listening')}` : t('speakButton')}</button>

          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', color: '#94a3b8', fontSize: '12px' }}>

          </div>

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
              padding: '12px',
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
            {loading ? t('verifying') : t('continue')}
          </button>
        </form>
        <div style={{ textAlign: 'center', marginTop: '12px' }}>
          <button type="button" onClick={() => navigate('/phone')} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', textDecoration: 'underline' }}>Login Using Mobile No.</button>
        </div>
      </div>
      <div style={{ position: 'fixed', bottom: '20px', right: '20px' }}>
        <button
          onClick={() => navigate('/agent')}
          style={{ width: 'auto', fontSize: '0.8em', background: 'rgba(255,255,255,0.1)', padding: '8px 15px', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          👮 Agent Portal
        </button>
      </div>
      <div style={{ position: 'fixed', bottom: '10px', width: '100%', textAlign: 'center', color: '#64748b', fontSize: '12px', pointerEvents: 'none' }}>
        All rights reserved by Team Neutals
      </div>
    </div>
  )
}

export default DriverLogin

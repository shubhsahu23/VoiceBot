import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import axios from 'axios'

const PhoneLogin = () => {
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e && e.preventDefault()
    const p = (phone || '').trim()
    if (!p) {
      setError('Please enter a phone number.')
      return
    }

    setError('')
    setLoading(true)
    try {
      // Backend endpoint for phone validation (add server-side if not present)
      const resp = await axios.post('http://localhost:8000/validate-phone', { phone: p })
      if (resp.data && resp.data.valid) {
        // If backend returns a driver id for the phone, use it; otherwise pass phone
        const id = resp.data.driver_id || p
        navigate('/chat', { state: { driverId: id } })
      } else {
        setError(resp.data?.message || 'Phone not registered.')
      }
    } catch (err) {
      // Friendly fallback message; if endpoint is not available, show instructive message
      const msg = err.response?.data?.detail?.message || err.response?.data?.message || 'Phone login not available. Please use driver ID.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a, #020617)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '100%', maxWidth: '420px', background: '#020617', borderRadius: '18px', padding: '32px', boxShadow: '0 20px 40px rgba(0,0,0,0.6)', border: '1px solid #1e293b' }}>
        <h2 style={{ color: '#38bdf8', textAlign: 'center' }}>📱 Mobile Login</h2>
        <p style={{ color: '#94a3b8', textAlign: 'center' }}>Enter your phone number to receive an OTP or login directly if already linked.</p>

        <form onSubmit={handleSubmit}>
          <label style={{ display: 'block', color: '#e5e7eb', marginBottom: '8px' }}>Phone Number</label>
          <input
            type="tel"
            inputMode="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="e.g. +91 98765 43210"
            style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #334155', background: '#020617', color: '#e5e7eb' }}
          />

          {error && <div style={{ background: '#7f1d1d', color: '#fecaca', padding: '10px', borderRadius: '8px', marginTop: '12px' }}>{error}</div>}

          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button type="submit" disabled={loading} style={{ flex: 1, padding: '10px', borderRadius: '10px', border: 'none', background: '#38bdf8', color: '#020617', fontWeight: 600 }}>{loading ? 'Please wait...' : 'Login'}</button>
          </div>
          <button type="button" onClick={() => navigate('/')} style={{ padding: '10px', borderRadius: '10px', border: '1px solid #334155', background: 'transparent', color: '#94a3b8' }}>Back</button>

        </form>
      </div>
    </div>
  )
}

export default PhoneLogin

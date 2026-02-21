import { useState } from 'react'
import useAuthStore from '../stores/authStore'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isLogin) {
        await login(username, password)
      } else {
        await register(username, password)
      }
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    }
    setLoading(false)
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-title">
            <i className="fa-solid fa-gamepad"></i> Mini Games
          </h1>
          <p className="login-subtitle">Play classic and strategy games with friends online</p>
        </div>

        <div className="glass-card login-card">
          <div className="tab-bar">
            <button className={`tab-btn ${isLogin ? 'active' : ''}`} onClick={() => setIsLogin(true)}>Sign In</button>
            <button className={`tab-btn ${!isLogin ? 'active' : ''}`} onClick={() => setIsLogin(false)}>Register</button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input
                className="form-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                className="form-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>

            {error && <div className="form-error">{error}</div>}

            <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
              {loading ? '...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

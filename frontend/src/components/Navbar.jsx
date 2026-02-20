import { Link, useLocation, useNavigate } from 'react-router-dom'
import useAuthStore from '../stores/authStore'

export default function Navbar() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/')

  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand">🎮 Mini Games</Link>
      <div className="nav-links">
        <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>Home</Link>
        <Link to="/leaderboard" className={`nav-link ${isActive('/leaderboard') ? 'active' : ''}`}>🏆 Leaderboard</Link>
        <Link to="/social-empires" className={`nav-link ${isActive('/social-empires') ? 'active' : ''}`}>⚔️ Social Empires</Link>
      </div>
      <div className="nav-user">
        <span className="nav-username">👤 {user?.username}</span>
        <button className="btn btn-sm btn-ghost" onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  )
}

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
      <Link to="/" className="nav-brand">
        <i className="fa-solid fa-gamepad"></i> Mini Games
      </Link>
      <div className="nav-links">
        <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>Home</Link>
        <Link to="/leaderboard" className={`nav-link ${isActive('/leaderboard') ? 'active' : ''}`}>
          <i className="fa-solid fa-trophy"></i> Leaderboard
        </Link>
        <Link to="/social-empires" className={`nav-link ${isActive('/social-empires') ? 'active' : ''}`}>
          <i className="fa-solid fa-shield-halved"></i> Social Empires
        </Link>
      </div>
      <div className="nav-user">
        <span className="nav-username">
          <i className="fa-solid fa-user"></i> {user?.username}
        </span>
        <button className="btn btn-sm btn-ghost" onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  )
}

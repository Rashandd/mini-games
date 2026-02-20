import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { getSocket } from '../socket'
import useAuthStore from '../stores/authStore'

export default function HomePage() {
  const [games, setGames] = useState([])
  const [onlineCount, setOnlineCount] = useState(0)
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)

  useEffect(() => {
    api.get('/games').then((r) => setGames(r.data)).catch(() => {})
    const s = getSocket()
    if (s) {
      s.on('online_count', (data) => setOnlineCount(data.count))
    }
    return () => {
      if (s) s.off('online_count')
    }
  }, [])

  const handlePlay = (slug) => {
    if (slug === 'social-empires') {
      navigate('/social-empires')
    } else if (slug === 'wave-drifter') {
      navigate('/wave-drifter')
    } else {
      navigate(`/game/${slug}`)
    }
  }

  return (
    <div className="page-content">
      <div className="home-header">
        <h1>🎮 Game Lobby</h1>
        <div className="online-pill">
          <span className="online-dot"></span>
          {onlineCount} Online
        </div>
      </div>

      <div className="game-grid">
        {games.map((g) => (
          <div key={g.id} className="glass-card game-card" onClick={() => handlePlay(g.slug)}>
            <div className="game-card-icon">{g.icon}</div>
            <h3 className="game-card-title">{g.name}</h3>
            <p className="game-card-desc">{g.description}</p>
            <div className="game-card-meta">
              <span>{g.min_players}-{g.max_players} players</span>
            </div>
            <button className="btn btn-primary btn-sm">Play</button>
          </div>
        ))}
      </div>
    </div>
  )
}

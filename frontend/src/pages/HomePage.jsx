import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { getSocket } from '../socket'
import useAuthStore from '../stores/authStore'

// Map game slugs to FA icon classes (used when game icon comes from DB as emoji legacy)
const GAME_FA_ICONS = {
  'tic-tac-toe': 'fa-xmark',
  'checkers':    'fa-flag-checkered',
  'backgammon':  'fa-dice',
  'social-empires': 'fa-shield-halved',
  'wave-drifter': 'fa-skull-crossbones',
}

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
        <h1><i className="fa-solid fa-gamepad"></i> Game Lobby</h1>
        <div className="online-pill">
          <span className="online-dot"></span>
          {onlineCount} Online
        </div>
      </div>

      <div className="game-grid">
        {games.map((g) => (
          <div key={g.id} className="glass-card game-card" onClick={() => handlePlay(g.slug)}>
            <div className="game-card-icon">
              <i className={`fa-solid ${GAME_FA_ICONS[g.slug] || 'fa-gamepad'}`}></i>
            </div>
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

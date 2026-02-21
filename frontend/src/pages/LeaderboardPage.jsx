import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api'

// Rank medal icons for top 3
function RankCell({ rank }) {
  if (rank === 1) return <i className="fa-solid fa-medal" style={{ color: '#FFD700' }} title="Gold"></i>
  if (rank === 2) return <i className="fa-solid fa-medal" style={{ color: '#C0C0C0' }} title="Silver"></i>
  if (rank === 3) return <i className="fa-solid fa-medal" style={{ color: '#CD7F32' }} title="Bronze"></i>
  return rank
}

export default function LeaderboardPage() {
  const { slug } = useParams()
  const [entries, setEntries] = useState([])
  const [tab, setTab] = useState(slug || 'global')
  const [games, setGames] = useState([])

  useEffect(() => {
    api.get('/games').then((r) => setGames(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    const url = tab === 'global' ? '/leaderboard' : `/leaderboard/${tab}`
    api.get(url).then((r) => setEntries(r.data)).catch(() => {})
  }, [tab])

  return (
    <div className="page-content">
      <h1><i className="fa-solid fa-trophy"></i> Leaderboard</h1>

      <div className="tab-bar">
        <button className={`tab-btn ${tab === 'global' ? 'active' : ''}`} onClick={() => setTab('global')}>
          <i className="fa-solid fa-globe"></i> Global
        </button>
        {games.filter(g => g.slug !== 'social-empires').map((g) => (
          <button key={g.id} className={`tab-btn ${tab === g.slug ? 'active' : ''}`} onClick={() => setTab(g.slug)}>
            {g.name}
          </button>
        ))}
      </div>

      <div className="glass-card">
        <table className="leaderboard-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Player</th>
              <th>Rating</th>
              <th>W</th>
              <th>L</th>
              <th>D</th>
              <th>Win%</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr><td colSpan="7" className="center muted">No entries yet</td></tr>
            ) : entries.map((e) => (
              <tr key={e.user_id}>
                <td className="rank"><RankCell rank={e.rank} /></td>
                <td>{e.username}</td>
                <td><strong>{tab === 'global' ? e.avg_rating || e.total_score : e.rating}</strong></td>
                <td className="win">{tab === 'global' ? e.total_wins : e.wins}</td>
                <td className="loss">{tab === 'global' ? e.total_losses : e.losses}</td>
                <td>{tab === 'global' ? e.total_draws : e.draws}</td>
                <td>{tab === 'global' ? '-' : `${e.win_rate}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function VillageSelectPage() {
  const [villages, setVillages] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/se/villages').then((r) => {
      setVillages(r.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const createVillage = async () => {
    const { data } = await api.post('/se/villages/new')
    navigate(`/social-empires/play/${data.userid}`)
  }

  return (
    <div className="page-content">
      <h1>⚔️ Social Empires</h1>
      <p className="subtitle">Select a village to play or create a new one.</p>

      <div className="village-grid">
        {villages.map((v) => (
          <div key={v.userid} className="glass-card village-card" onClick={() => navigate(`/social-empires/play/${v.userid}`)}>
            <div className="village-icon">🏰</div>
            <h3>{v.name}</h3>
            <div className="village-meta">
              <span>Level {v.level}</span>
              <span>XP: {v.xp}</span>
            </div>
            <button className="btn btn-primary btn-sm">Play</button>
          </div>
        ))}

        <div className="glass-card village-card new-village" onClick={createVillage}>
          <div className="village-icon">➕</div>
          <h3>New Empire</h3>
          <p className="muted">Start a new adventure</p>
        </div>
      </div>

      {loading && <div className="spinner center-spinner"></div>}
    </div>
  )
}

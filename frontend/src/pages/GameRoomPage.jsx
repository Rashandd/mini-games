import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api'
import useGameStore from '../stores/gameStore'
import useAuthStore from '../stores/authStore'
import TicTacToeBoard from '../components/boards/TicTacToeBoard'
import ChessBoard from '../components/boards/ChessBoard'
import CheckersBoard from '../components/boards/CheckersBoard'
import BackgammonBoard from '../components/boards/BackgammonBoard'

export default function GameRoomPage() {
  const { slug } = useParams()
  const user = useAuthStore((s) => s.user)
  const game = useGameStore()
  const [lobbies, setLobbies] = useState([])
  const [showPrivateForm, setShowPrivateForm] = useState(false)
  const [privatePassword, setPrivatePassword] = useState('')
  const [joinPassword, setJoinPassword] = useState('')
  const [joinRoomCode, setJoinRoomCode] = useState(null)
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('newest')
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')

  const loadLobbies = useCallback(() => {
    api.get(`/lobbies/${slug}`).then((r) => setLobbies(r.data)).catch(() => {})
  }, [slug])

  useEffect(() => {
    game.setupListeners()
    loadLobbies()
    const iv = setInterval(loadLobbies, 5000)
    return () => {
      clearInterval(iv)
      game.cleanupListeners()
    }
  }, [slug])

  const createPublicGame = () => game.createGame(slug)
  const createPrivateGame = () => {
    game.createGame(slug, true, privatePassword)
    setPrivatePassword('')
    setShowPrivateForm(false)
  }

  const joinLobby = (lobby) => {
    if (lobby.is_private) {
      setJoinRoomCode(lobby.room_code)
    } else {
      game.joinGame(lobby.room_code)
    }
  }

  const submitJoinPassword = () => {
    game.joinGame(joinRoomCode, joinPassword)
    setJoinRoomCode(null)
    setJoinPassword('')
  }

  const filtered = lobbies
    .filter((l) => l.host.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => sort === 'newest' ? 0 : -1)

  const renderBoard = () => {
    if (!game.state || !game.gameSlug) return null
    const props = { state: game.state, yourPlayer: game.yourPlayer, onMove: game.makeMove, gameOver: game.gameOver }
    switch (game.gameSlug) {
      case 'tic-tac-toe': return <TicTacToeBoard {...props} />
      case 'chess': return <ChessBoard {...props} />
      case 'checkers': return <CheckersBoard {...props} />
      case 'backgammon': return <BackgammonBoard {...props} />
      default: return <div className="glass-card"><p>No board renderer for {game.gameSlug}</p></div>
    }
  }

  // In-game view
  if (game.roomCode && game.status) {
    return (
      <div className="page-content game-active">
        <div className="game-info-bar">
          <h2>{game.gameName || slug}</h2>
          <span className="room-code">Room: {game.roomCode}</span>
          <span className="status-badge">{game.status}</span>
        </div>

        <div className="game-layout">
          <div className="game-players">
            <div className={`player-tag ${game.yourPlayer === 1 ? 'you' : ''}`}>
              👤 {game.player1 || '?'} {game.yourPlayer === 1 && '(You)'}
            </div>
            <span className="vs-badge">VS</span>
            <div className={`player-tag ${game.yourPlayer === 2 ? 'you' : ''}`}>
              👤 {game.player2 || 'Waiting...'} {game.yourPlayer === 2 && '(You)'}
            </div>
          </div>

          {game.status === 'waiting' && (
            <div className="glass-card waiting-card">
              <div className="spinner"></div>
              <p>Waiting for opponent to join...</p>
              <p className="muted">Share room code: <strong>{game.roomCode}</strong></p>
            </div>
          )}

          {game.status === 'playing' && renderBoard()}

          {game.gameOver && (
            <div className="glass-card game-over-card">
              <h2>🏆 Game Over!</h2>
              <p className="winner-text">
                {game.resigned
                  ? `${game.resigned} resigned. ${game.winnerName} wins!`
                  : game.winnerName === 'Draw'
                    ? "It's a draw!"
                    : `${game.winnerName} wins!`
                }
              </p>
              <button className="btn btn-primary" onClick={() => game.reset()}>Back to Lobby</button>
            </div>
          )}

          {game.status === 'playing' && !game.gameOver && (
            <button className="btn btn-danger btn-sm" onClick={game.resignGame}>🏳️ Resign</button>
          )}
        </div>
      </div>
    )
  }

  // Lobby view
  return (
    <div className="page-content">
      <div className="lobby-header">
        <h2>{slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} Lobby</h2>
        <button className="btn btn-accent btn-sm" onClick={() => game.findMatch(slug)}>⚡ Quick Match</button>
      </div>

      <div className="glass-card">
        <h3>Create Game</h3>
        <div className="create-buttons">
          <button className="btn btn-primary btn-sm" onClick={createPublicGame}>🌍 Public Game</button>
          <button className="btn btn-gold btn-sm" onClick={() => setShowPrivateForm(!showPrivateForm)}>🔒 Private Game</button>
        </div>
        {showPrivateForm && (
          <div className="private-form">
            <input
              className="form-input"
              type="password"
              placeholder="Set password..."
              value={privatePassword}
              onChange={(e) => setPrivatePassword(e.target.value)}
            />
            <button className="btn btn-primary btn-sm" onClick={createPrivateGame}>Create</button>
          </div>
        )}
      </div>

      <div className="glass-card">
        <div className="divider">open games</div>
        <div className="filter-bar">
          <input className="form-input" placeholder="Search by host..." value={search} onChange={(e) => setSearch(e.target.value)} />
          <select className="form-select" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
          </select>
        </div>
        <div className="lobby-list">
          {filtered.length === 0 ? (
            <p className="muted center">No open games. Create one!</p>
          ) : filtered.map((l) => (
            <div key={l.room_code} className="lobby-item" onClick={() => joinLobby(l)}>
              <span className="lobby-host">{l.is_private ? '🔒' : '🌍'} {l.host}</span>
              <span className="lobby-age">{l.age}</span>
              <button className="btn btn-sm btn-primary">Join</button>
            </div>
          ))}
        </div>
      </div>

      {/* Password modal */}
      {joinRoomCode && (
        <div className="modal-overlay" onClick={() => setJoinRoomCode(null)}>
          <div className="glass-card modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>🔒 Private Game</h3>
            <p className="muted">Enter the password to join.</p>
            <input
              className="form-input"
              type="password"
              placeholder="Password..."
              value={joinPassword}
              onChange={(e) => setJoinPassword(e.target.value)}
            />
            <div className="modal-actions">
              <button className="btn btn-primary btn-sm" onClick={submitJoinPassword}>Join</button>
              <button className="btn btn-secondary btn-sm" onClick={() => setJoinRoomCode(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api'
import useGameStore from '../stores/gameStore'
import useAuthStore from '../stores/authStore'
import TicTacToeBoard from '../components/boards/TicTacToeBoard'
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
  const [stats, setStats] = useState({ waiting: 0, playing: 0 })

  const loadLobbies = useCallback(() => {
    api.get(`/lobbies/${slug}`).then((r) => setLobbies(r.data)).catch(() => {})
    api.get(`/game-stats/${slug}`).then((r) => setStats(r.data)).catch(() => {})
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
      case 'checkers': return <CheckersBoard {...props} />
      case 'backgammon': return <BackgammonBoard {...props} />
      default: return <div className="glass-card"><p>No board renderer for {game.gameSlug}</p></div>
    }
  }

  const gameName = slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

  // Determine whose turn it is
  const currentTurn = game.state?.current_player
  const isYourTurn = currentTurn === game.yourPlayer

  // In-game view
  if (game.roomCode && game.status) {
    return (
      <div className="page-content game-active" style={{ maxWidth: 700, margin: '0 auto' }}>
        {/* Game header bar */}
        <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 20px', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{game.gameName || gameName}</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: 'var(--card-bg)', padding: '2px 8px', borderRadius: 8, fontFamily: 'monospace' }}>{game.roomCode}</span>
          </div>
          <span style={{
            padding: '3px 10px', borderRadius: 12, fontSize: '0.75rem', fontWeight: 600,
            background: game.status === 'playing' ? 'var(--accent-green)' : game.status === 'waiting' ? 'var(--accent)' : '#666',
            color: '#000',
          }}>
            {game.status === 'playing' ? '🟢 Playing' : game.status === 'waiting' ? '⏳ Waiting' : '🏁 Finished'}
          </span>
        </div>

        {/* Player cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <div className="glass-card" style={{
            padding: '10px 16px', textAlign: 'center',
            border: game.status === 'playing' && currentTurn === 1 ? '2px solid var(--accent-green)' : '2px solid transparent',
            opacity: game.status === 'playing' && currentTurn === 2 ? 0.6 : 1,
            transition: 'all 0.3s ease',
          }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 2 }}>
              {game.yourPlayer === 1 ? '👤 YOU' : '👤 OPPONENT'}
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>
              {game.player1 || '?'} {game.gameSlug === 'tic-tac-toe' && <span style={{ color: 'var(--accent)' }}>✕</span>}
            </div>
            {game.status === 'playing' && currentTurn === 1 && (
              <div style={{ fontSize: '0.65rem', color: 'var(--accent-green)', marginTop: 2, fontWeight: 600 }}>▶ TURN</div>
            )}
          </div>

          <span style={{ fontWeight: 800, fontSize: '0.85rem', color: 'var(--text-muted)' }}>VS</span>

          <div className="glass-card" style={{
            padding: '10px 16px', textAlign: 'center',
            border: game.status === 'playing' && currentTurn === 2 ? '2px solid var(--accent-green)' : '2px solid transparent',
            opacity: game.status === 'playing' && currentTurn === 1 ? 0.6 : 1,
            transition: 'all 0.3s ease',
          }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 2 }}>
              {game.yourPlayer === 2 ? '👤 YOU' : '👤 OPPONENT'}
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>
              {game.player2 || '...'} {game.gameSlug === 'tic-tac-toe' && <span style={{ color: '#4fc3f7' }}>○</span>}
            </div>
            {game.status === 'playing' && currentTurn === 2 && (
              <div style={{ fontSize: '0.65rem', color: 'var(--accent-green)', marginTop: 2, fontWeight: 600 }}>▶ TURN</div>
            )}
          </div>
        </div>

        {/* Turn banner */}
        {game.status === 'playing' && !game.gameOver && (
          <div style={{
            textAlign: 'center', padding: '8px 16px', borderRadius: 10, marginBottom: 16, fontWeight: 600, fontSize: '0.85rem',
            background: isYourTurn ? 'rgba(76, 175, 80, 0.15)' : 'rgba(255, 167, 38, 0.15)',
            color: isYourTurn ? 'var(--accent-green)' : '#ffa726',
            border: `1px solid ${isYourTurn ? 'rgba(76, 175, 80, 0.3)' : 'rgba(255, 167, 38, 0.3)'}`,
          }}>
            {isYourTurn ? '🟢 Your turn — make a move!' : "🟡 Opponent's turn — waiting..."}
          </div>
        )}

        {/* Waiting screen */}
        {game.status === 'waiting' && (
          <div className="glass-card" style={{ textAlign: 'center', padding: '32px 24px' }}>
            <div className="spinner" style={{ marginBottom: 16 }}></div>
            <p style={{ fontWeight: 600, marginBottom: 4 }}>Waiting for opponent...</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 16 }}>
              Share code: <strong style={{ fontFamily: 'monospace', letterSpacing: 1 }}>{game.roomCode}</strong>
            </p>
            <button
              className="btn btn-sm"
              onClick={() => game.deleteGame(game.roomCode)}
              style={{ background: 'rgba(244,67,54,0.15)', color: '#ef5350', border: '1px solid rgba(244,67,54,0.3)', fontWeight: 600 }}
            >
              ✕ Cancel Room
            </button>
          </div>
        )}

        {/* Board */}
        {game.status === 'playing' && (
          <div style={{ marginBottom: 16 }}>
            {renderBoard()}
          </div>
        )}

        {/* Game Over */}
        {game.gameOver && (
          <div className="glass-card" style={{ textAlign: 'center', padding: '24px' }}>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '1.3rem' }}>🏆 Game Over!</h2>
            <p style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16 }}>
              {game.resigned
                ? `${game.resigned} resigned. ${game.winnerName} wins!`
                : game.winnerName === 'Draw'
                  ? "It's a draw! 🤝"
                  : `${game.winnerName} wins! 🎉`
              }
            </p>
            <button className="btn btn-primary" onClick={() => game.reset()}>← Back to Lobby</button>
          </div>
        )}

        {/* Resign button */}
        {game.status === 'playing' && !game.gameOver && (
          <div style={{ textAlign: 'center', marginTop: 8 }}>
            <button
              onClick={game.resignGame}
              style={{
                background: 'transparent', border: '1px solid rgba(244,67,54,0.4)', color: '#ef5350',
                padding: '6px 18px', borderRadius: 8, fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseOver={(e) => { e.target.style.background = 'rgba(244,67,54,0.1)' }}
              onMouseOut={(e) => { e.target.style.background = 'transparent' }}
            >
              🏳️ Resign Game
            </button>
          </div>
        )}
      </div>
    )
  }

  // Lobby view
  return (
    <div className="page-content">
      <div className="lobby-header">
        <h2>{gameName} Lobby</h2>
        <div className="lobby-stats" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span className="stat-pill" style={{ background: 'var(--accent-green)', color: '#000', padding: '4px 12px', borderRadius: 20, fontSize: '0.8rem', fontWeight: 600 }}>
            🟢 {stats.playing} Playing
          </span>
          <span className="stat-pill" style={{ background: 'var(--accent)', color: '#000', padding: '4px 12px', borderRadius: 20, fontSize: '0.8rem', fontWeight: 600 }}>
            ⏳ {stats.waiting} Waiting
          </span>
          <button className="btn btn-accent btn-sm" onClick={() => game.findMatch(slug)}>⚡ Quick Match</button>
        </div>
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

      {/* Game Tutorial */}
      <div className="game-tutorial">
        <h3>📖 How to Play {gameName}</h3>
        <div className="tutorial-steps">
          {slug === 'tic-tac-toe' && (
            <>
              <div className="tutorial-step">
                <span className="step-num">1</span>
                <div>
                  <strong>Take Turns</strong>
                  <p>Player 1 is ✕, Player 2 is ○. Click any empty cell on the 3×3 grid to place your mark.</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">2</span>
                <div>
                  <strong>Get Three in a Row</strong>
                  <p>Line up three of your marks horizontally, vertically, or diagonally to win the game.</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">3</span>
                <div>
                  <strong>Block Your Opponent</strong>
                  <p>Watch for your opponent getting two in a row — block them before they complete three!</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">4</span>
                <div>
                  <strong>Draw</strong>
                  <p>If all 9 cells are filled and no one has three in a row, the game ends in a draw.</p>
                </div>
              </div>
            </>
          )}
          {slug === 'checkers' && (
            <>
              <div className="tutorial-step">
                <span className="step-num">1</span>
                <div>
                  <strong>Move Diagonally</strong>
                  <p>Click a piece, then click a diagonal square to move. Regular pieces can only move forward.</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">2</span>
                <div>
                  <strong>Jump to Capture</strong>
                  <p>Jump over an opponent's piece diagonally to capture it. Multi-jumps are possible in one turn!</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">3</span>
                <div>
                  <strong>Get Kinged</strong>
                  <p>Reach the opposite end of the board to become a <em>King</em> — kings can move and jump in both directions.</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">4</span>
                <div>
                  <strong>Win the Game</strong>
                  <p>Capture all of your opponent's pieces or block them so they can't make any moves.</p>
                </div>
              </div>
            </>
          )}
          {slug === 'backgammon' && (
            <>
              <div className="tutorial-step">
                <span className="step-num">1</span>
                <div>
                  <strong>Roll the Dice</strong>
                  <p>Each turn, two dice are rolled. Move your checkers forward by the number shown on each die.</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">2</span>
                <div>
                  <strong>Move Your Checkers</strong>
                  <p>Click a point with your checkers, then click the destination. You can only land on open points or points you already occupy.</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">3</span>
                <div>
                  <strong>Hit & Enter from Bar</strong>
                  <p>Land on a point with a single opponent checker to send it to the bar. They must re-enter before making other moves.</p>
                </div>
              </div>
              <div className="tutorial-step">
                <span className="step-num">4</span>
                <div>
                  <strong>Bear Off to Win</strong>
                  <p>Once all 15 of your checkers are in your home board (last 6 points), start bearing them off. First to bear off all checkers wins!</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

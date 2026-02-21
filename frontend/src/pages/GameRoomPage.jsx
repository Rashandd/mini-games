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
    const statusClass = game.status === 'playing' ? 'status-pill--playing' : game.status === 'waiting' ? 'status-pill--waiting' : 'status-pill--finished'
    const statusLabel = game.status === 'playing' ? '🟢 Playing' : game.status === 'waiting' ? '⏳ Waiting' : '🏁 Finished'

    return (
      <div className="page-content game-active">
        {/* Game header bar */}
        <div className="glass-card game-header-bar">
          <div className="game-header-left">
            <h2 className="game-header-title">{game.gameName || gameName}</h2>
            <span className="room-code-badge">{game.roomCode}</span>
          </div>
          <span className={`status-pill ${statusClass}`}>{statusLabel}</span>
        </div>

        {/* Player cards */}
        <div className="players-grid">
          <div className={`glass-card player-card ${game.status === 'playing' && currentTurn === 1 ? 'player-card--active' : ''} ${game.status === 'playing' && currentTurn === 2 ? 'player-card--inactive' : ''}`}>
            <div className="player-label">
              {game.yourPlayer === 1 ? '👤 YOU' : '👤 OPPONENT'}
            </div>
            <div className="player-name">
              {game.player1 || '?'} {game.gameSlug === 'tic-tac-toe' && <span className="mark-x">✕</span>}
            </div>
            {game.status === 'playing' && currentTurn === 1 && (
              <div className="turn-badge">▶ TURN</div>
            )}
          </div>

          <span className="vs-text">VS</span>

          <div className={`glass-card player-card ${game.status === 'playing' && currentTurn === 2 ? 'player-card--active' : ''} ${game.status === 'playing' && currentTurn === 1 ? 'player-card--inactive' : ''}`}>
            <div className="player-label">
              {game.yourPlayer === 2 ? '👤 YOU' : '👤 OPPONENT'}
            </div>
            <div className="player-name">
              {game.player2 || '...'} {game.gameSlug === 'tic-tac-toe' && <span className="mark-o">○</span>}
            </div>
            {game.status === 'playing' && currentTurn === 2 && (
              <div className="turn-badge">▶ TURN</div>
            )}
          </div>
        </div>

        {/* Turn banner */}
        {game.status === 'playing' && !game.gameOver && (
          <div className={`turn-banner ${isYourTurn ? 'turn-banner--yours' : 'turn-banner--theirs'}`}>
            {isYourTurn ? '🟢 Your turn — make a move!' : "🟡 Opponent's turn — waiting..."}
          </div>
        )}

        {/* Waiting screen */}
        {game.status === 'waiting' && (
          <div className="glass-card waiting-card">
            <div className="spinner"></div>
            <p className="waiting-title">Waiting for opponent...</p>
            <p className="waiting-subtitle">
              Share code: <strong className="share-code">{game.roomCode}</strong>
            </p>
            <button
              className="btn btn-sm cancel-room-btn"
              onClick={() => game.deleteGame(game.roomCode)}
            >
              ✕ Cancel Room
            </button>
          </div>
        )}

        {/* Board */}
        {game.status === 'playing' && (
          <div className="board-wrapper">
            {renderBoard()}
          </div>
        )}

        {/* Game Over */}
        {game.gameOver && (
          <div className="glass-card gameover-card">
            <h2 className="gameover-title">🏆 Game Over!</h2>
            <p className="gameover-result">
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
          <div className="resign-wrapper">
            <button className="resign-btn" onClick={game.resignGame}>
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
        <div className="lobby-stats">
          <span className="stat-pill stat-pill--playing">
            🟢 {stats.playing} Playing
          </span>
          <span className="stat-pill stat-pill--waiting">
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

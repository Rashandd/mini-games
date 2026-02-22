import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api'
import useGameStore from '../stores/gameStore'
import useAuthStore from '../stores/authStore'
import TicTacToeBoard from '../components/boards/TicTacToeBoard'
import CheckersBoard from '../components/boards/CheckersBoard'
import BackgammonBoard from '../components/boards/BackgammonBoard'

export default function GameRoomPage() {
  const { slug, roomCode: urlRoomCode } = useParams()
  const user = useAuthStore((s) => s.user)
  const game = useGameStore()
  const [lobbies, setLobbies] = useState([])
  const [activeGames, setActiveGames] = useState([])
  const [showPrivateForm, setShowPrivateForm] = useState(false)
  const [privatePassword, setPrivatePassword] = useState('')
  const [joinPassword, setJoinPassword] = useState('')
  const [joinRoomCode, setJoinRoomCode] = useState(null)
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('newest')
  const [stats, setStats] = useState({ waiting: 0, playing: 0 })
  const [linkCopied, setLinkCopied] = useState(false)
  const [joinError, setJoinError] = useState('')
  const [manualRoomCode, setManualRoomCode] = useState('')

  const loadLobbies = useCallback(() => {
    api.get(`/lobbies/${slug}`).then((r) => setLobbies(r.data)).catch(() => {})
    api.get(`/game-stats/${slug}`).then((r) => setStats(r.data)).catch(() => {})
    api.get(`/active-games/${slug}`).then((r) => setActiveGames(r.data)).catch(() => {})
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

  // Handle URL-based join (private game invite link)
  useEffect(() => {
    if (urlRoomCode && !game.roomCode) {
      // Check if the game is private — try joining directly first
      // If password is needed, the server will return an error and we show the modal
      import('../socket').then(({ getSocket: gs }) => {
        const socket = gs()
        if (!socket) return

        const handleError = (data) => {
          if (data?.message === 'Wrong password') {
            setJoinRoomCode(urlRoomCode)
            setJoinError('')
          } else if (data?.message) {
            setJoinError(data.message)
          }
          socket.off('error', handleError)
        }

        socket.on('error', handleError)
        // Try joining without password — if it's public, this succeeds
        // If it's private, we get 'Wrong password' and show the modal
        game.joinGame(urlRoomCode)

        // Clean up listener after a timeout
        setTimeout(() => socket.off('error', handleError), 5000)
      })
    }
  }, [urlRoomCode])

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

  const handleManualJoin = () => {
    const code = manualRoomCode.trim()
    if (!code) return
    setJoinError('')
    import('../socket').then(({ getSocket: gs }) => {
      const socket = gs()
      if (!socket) return

      const handleError = (data) => {
        if (data?.message === 'Wrong password') {
          setJoinRoomCode(code)
          setJoinError('')
        } else if (data?.message) {
          setJoinError(data.message)
        }
        socket.off('error', handleError)
      }

      socket.on('error', handleError)
      game.joinGame(code)
      setTimeout(() => socket.off('error', handleError), 5000)
    })
    setManualRoomCode('')
  }

  const spectate = (roomCode) => {
    game.spectateGame(roomCode)
  }

  const copyShareLink = () => {
    const url = `${window.location.origin}/game/${slug}/join/${game.roomCode}`
    navigator.clipboard.writeText(url).then(() => {
      setLinkCopied(true)
      setTimeout(() => setLinkCopied(false), 2000)
    })
  }

  const filtered = lobbies
    .filter((l) => l.host.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => sort === 'newest' ? 0 : -1)

  const renderBoard = () => {
    if (!game.state || !game.gameSlug) return null
    const props = {
      state: game.state,
      yourPlayer: game.isSpectator ? null : game.yourPlayer,
      onMove: game.isSpectator ? () => {} : game.makeMove,
      gameOver: game.gameOver
    }
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
  const isYourTurn = !game.isSpectator && currentTurn === game.yourPlayer

  // In-game view (playing, waiting, spectating, or finished)
  if (game.roomCode && game.status) {
    const statusIcon = game.isSpectator ? 'fa-eye' : game.status === 'playing' ? 'fa-circle-play' : game.status === 'waiting' ? 'fa-hourglass-half' : 'fa-flag-checkered'
    const statusLabel = game.isSpectator ? 'Spectating' : game.status === 'playing' ? 'Playing' : game.status === 'waiting' ? 'Waiting' : 'Finished'

    return (
      <div className="page-content game-active">
        {/* Game header bar */}
        <div className="glass-card game-header-bar">
          <div className="game-header-left">
            <h2 className="game-header-title">{game.gameName || gameName}</h2>
            <span className="room-code-badge">{game.roomCode}</span>
          </div>
          <span className={`status-pill ${game.isSpectator ? 'status-pill--spectating' : game.status === 'playing' ? 'status-pill--playing' : game.status === 'waiting' ? 'status-pill--waiting' : 'status-pill--finished'}`}>
            <i className={`fa-solid ${statusIcon}`}></i> {statusLabel}
          </span>
        </div>

        {/* Spectator banner */}
        {game.isSpectator && (
          <div className="spectator-banner">
            <i className="fa-solid fa-eye"></i> You are watching this game as a spectator
          </div>
        )}

        {/* Player cards */}
        <div className="players-grid">
          <div className={`glass-card player-card ${game.status === 'playing' && currentTurn === 1 ? 'player-card--active' : ''} ${game.status === 'playing' && currentTurn === 2 ? 'player-card--inactive' : ''}`}>
            <div className="player-label">
              <i className="fa-solid fa-user"></i> {game.yourPlayer === 1 ? 'YOU' : game.isSpectator ? 'PLAYER 1' : 'OPPONENT'}
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
              <i className="fa-solid fa-user"></i> {game.yourPlayer === 2 ? 'YOU' : game.isSpectator ? 'PLAYER 2' : 'OPPONENT'}
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
        {game.status === 'playing' && !game.gameOver && !game.isSpectator && (
          <div className={`turn-banner ${isYourTurn ? 'turn-banner--yours' : 'turn-banner--theirs'}`}>
            {isYourTurn
              ? <><i className="fa-solid fa-circle" style={{ color: 'var(--accent-green)' }}></i> Your turn — make a move!</>
              : <><i className="fa-solid fa-circle" style={{ color: '#ffa726' }}></i> Opponent's turn — waiting...</>
            }
          </div>
        )}

        {/* Waiting screen */}
        {game.status === 'waiting' && (
          <div className="glass-card waiting-card">
            <div className="spinner"></div>
            <p className="waiting-title">Waiting for opponent...</p>
            {game.isPrivate ? (
              <div className="share-link-section">
                <p className="waiting-subtitle">Share this link with your opponent:</p>
                <div className="share-link-row">
                  <input
                    className="form-input share-link-input"
                    readOnly
                    value={`${window.location.origin}/game/${slug}/join/${game.roomCode}`}
                    onClick={(e) => e.target.select()}
                  />
                  <button className="btn btn-primary btn-sm" onClick={copyShareLink}>
                    <i className={`fa-solid ${linkCopied ? 'fa-check' : 'fa-copy'}`}></i>
                    {linkCopied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <p className="muted center" style={{ marginTop: '8px' }}>
                  <i className="fa-solid fa-lock"></i> They will need the password to join
                </p>
              </div>
            ) : (
              <p className="waiting-subtitle">
                Share code: <strong className="share-code">{game.roomCode}</strong>
              </p>
            )}
            <button
              className="btn btn-sm cancel-room-btn"
              onClick={() => game.deleteGame(game.roomCode)}
            >
              <i className="fa-solid fa-xmark"></i> Cancel Room
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
            <h2 className="gameover-title"><i className="fa-solid fa-trophy"></i> Game Over!</h2>
            <p className="gameover-result">
              {game.resigned
                ? `${game.resigned} resigned. ${game.winnerName} wins!`
                : game.winnerName === 'Draw'
                  ? "It's a draw!"
                  : `${game.winnerName} wins!`
              }
            </p>
            <button className="btn btn-primary" onClick={() => game.reset()}>← Back to Lobby</button>
          </div>
        )}

        {/* Resign button (not for spectators) */}
        {game.status === 'playing' && !game.gameOver && !game.isSpectator && (
          <div className="resign-wrapper">
            <button className="resign-btn" onClick={game.resignGame}>
              <i className="fa-solid fa-flag"></i> Resign Game
            </button>
          </div>
        )}

        {/* Spectator: back to lobby button */}
        {game.isSpectator && (
          <div className="resign-wrapper">
            <button className="btn btn-secondary btn-sm" onClick={() => game.reset()}>
              <i className="fa-solid fa-arrow-left"></i> Back to Lobby
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
            <i className="fa-solid fa-circle" style={{ color: '#000' }}></i> {stats.playing} Playing
          </span>
          <span className="stat-pill stat-pill--waiting">
            <i className="fa-solid fa-hourglass-half"></i> {stats.waiting} Waiting
          </span>
          <button className="btn btn-accent btn-sm" onClick={() => game.findMatch(slug)}>
            <i className="fa-solid fa-bolt"></i> Quick Match
          </button>
        </div>
      </div>

      {/* URL join error */}
      {joinError && (
        <div className="form-error" style={{ marginBottom: '16px' }}>
          <i className="fa-solid fa-circle-exclamation"></i> {joinError}
        </div>
      )}

      <div className="glass-card">
        <h3>Create Game</h3>
        <div className="create-buttons">
          <button className="btn btn-primary btn-sm" onClick={createPublicGame}>
            <i className="fa-solid fa-globe"></i> Public Game
          </button>
          <button className="btn btn-gold btn-sm" onClick={() => setShowPrivateForm(!showPrivateForm)}>
            <i className="fa-solid fa-lock"></i> Private Game
          </button>
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

      {/* Join by Room Code */}
      <div className="glass-card">
        <h3><i className="fa-solid fa-right-to-bracket"></i> Join by Room Code</h3>
        <div className="private-form">
          <input
            className="form-input"
            type="text"
            placeholder="Enter room code..."
            value={manualRoomCode}
            onChange={(e) => setManualRoomCode(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleManualJoin()}
          />
          <button className="btn btn-primary btn-sm" onClick={handleManualJoin}>Join</button>
        </div>
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
              <span className="lobby-host">
                <i className={`fa-solid ${l.is_private ? 'fa-lock' : 'fa-globe'}`}></i> {l.host}
              </span>
              <span className="lobby-age">{l.age}</span>
              <button className="btn btn-sm btn-primary">Join</button>
            </div>
          ))}
        </div>
      </div>

      {/* Active Games — Spectator Section */}
      <div className="glass-card">
        <div className="divider">active games — watch live</div>
        <div className="lobby-list">
          {activeGames.length === 0 ? (
            <p className="muted center">No active games right now.</p>
          ) : activeGames.map((g) => (
            <div key={g.room_code} className="lobby-item active-game-item">
              <div className="active-game-players">
                <span className="active-game-name">{g.player1}</span>
                <span className="active-game-vs">vs</span>
                <span className="active-game-name">{g.player2}</span>
              </div>
              <span className="lobby-age">{g.age}</span>
              <button className="btn btn-sm btn-secondary" onClick={() => spectate(g.room_code)}>
                <i className="fa-solid fa-eye"></i> Watch
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Password modal */}
      {joinRoomCode && (
        <div className="modal-overlay" onClick={() => setJoinRoomCode(null)}>
          <div className="glass-card modal-card" onClick={(e) => e.stopPropagation()}>
            <h3><i className="fa-solid fa-lock"></i> Private Game</h3>
            <p className="muted">Enter the password to join.</p>
            <input
              className="form-input"
              type="password"
              placeholder="Password..."
              value={joinPassword}
              onChange={(e) => setJoinPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submitJoinPassword()}
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
        <h3><i className="fa-solid fa-book-open"></i> How to Play {gameName}</h3>
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

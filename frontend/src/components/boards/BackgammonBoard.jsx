export default function BackgammonBoard({ state, yourPlayer, onMove, gameOver }) {
  const board = state?.board || []
  const currentPlayer = state?.current_player || 1
  const dice = state?.dice || []
  const barPieces = state?.bar || { 1: 0, 2: 0 }

  return (
    <div className="board-container backgammon-board-container">
      <div className="turn-indicator">
        {gameOver ? '' : currentPlayer === yourPlayer ? '🟢 Your Turn' : '🔴 Opponent\'s Turn'}
      </div>
      <div className="glass-card">
        <div className="backgammon-info">
          <div>Dice: {dice.length > 0 ? dice.join(', ') : 'Roll needed'}</div>
          <div>Bar — You: {barPieces[yourPlayer] || 0} | Opp: {barPieces[yourPlayer === 1 ? 2 : 1] || 0}</div>
        </div>
        <div className="backgammon-points">
          {board.map((point, i) => (
            <div
              key={i}
              className={`bg-point ${i < 12 ? 'top' : 'bottom'} ${point?.player === yourPlayer ? 'yours' : ''}`}
              onClick={() => !gameOver && currentPlayer === yourPlayer && onMove({ from_point: i })}
            >
              <span className="bg-point-num">{i + 1}</span>
              <div className="bg-checkers">
                {point && Array(Math.min(point.count || 0, 5)).fill(0).map((_, j) => (
                  <span key={j} className={`bg-checker p${point.player}`}>●</span>
                ))}
                {point && (point.count || 0) > 5 && <span className="bg-overflow">+{point.count - 5}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

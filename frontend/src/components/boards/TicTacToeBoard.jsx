export default function TicTacToeBoard({ state, yourPlayer, onMove, gameOver }) {
  const board = state?.board || Array(9).fill(null)
  const currentPlayer = state?.current_player || 1

  const handleClick = (i) => {
    if (gameOver || board[i] || currentPlayer !== yourPlayer) return
    onMove({ position: i })
  }

  const getSymbol = (cell) => {
    if (cell === 1) return '✕'
    if (cell === 2) return '○'
    return ''
  }

  return (
    <div className="board-container ttt-board">
      <div className="turn-indicator">
        {gameOver ? '' : currentPlayer === yourPlayer ? '🟢 Your Turn' : '🔴 Opponent\'s Turn'}
      </div>
      <div className="ttt-grid">
        {board.map((cell, i) => (
          <button
            key={i}
            className={`ttt-cell ${cell ? 'filled' : ''} ${cell === 1 ? 'x' : ''} ${cell === 2 ? 'o' : ''}`}
            onClick={() => handleClick(i)}
            disabled={gameOver || !!cell || currentPlayer !== yourPlayer}
          >
            {getSymbol(cell)}
          </button>
        ))}
      </div>
    </div>
  )
}

import { useState } from 'react'

const PIECES = {
  K: '♔', Q: '♕', R: '♖', B: '♗', N: '♘', P: '♙',
  k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟',
}

export default function ChessBoard({ state, yourPlayer, onMove, gameOver }) {
  const board = state?.board || []
  const currentPlayer = state?.current_player || 1
  const [selected, setSelected] = useState(null)

  const isFlipped = yourPlayer === 2

  const handleClick = (row, col) => {
    if (gameOver || currentPlayer !== yourPlayer) return

    if (selected) {
      onMove({
        from_row: selected.row,
        from_col: selected.col,
        to_row: row,
        to_col: col,
      })
      setSelected(null)
    } else {
      const piece = board[row]?.[col]
      if (piece) setSelected({ row, col })
    }
  }

  const renderBoard = () => {
    const rows = isFlipped ? [...Array(8).keys()].reverse() : [...Array(8).keys()]
    const cols = isFlipped ? [...Array(8).keys()].reverse() : [...Array(8).keys()]

    return rows.map((r) => (
      <div key={r} className="chess-row">
        <span className="chess-rank">{8 - r}</span>
        {cols.map((c) => {
          const piece = board[r]?.[c]
          const isLight = (r + c) % 2 === 0
          const isSelected = selected?.row === r && selected?.col === c
          return (
            <button
              key={c}
              className={`chess-cell ${isLight ? 'light' : 'dark'} ${isSelected ? 'selected' : ''}`}
              onClick={() => handleClick(r, c)}
            >
              {piece ? PIECES[piece] || piece : ''}
            </button>
          )
        })}
      </div>
    ))
  }

  return (
    <div className="board-container chess-board-container">
      <div className="turn-indicator">
        {gameOver ? '' : currentPlayer === yourPlayer ? '🟢 Your Turn' : '🔴 Opponent\'s Turn'}
      </div>
      <div className="chess-grid">{renderBoard()}</div>
      <div className="chess-files">
        <span></span>
        {(isFlipped ? 'hgfedcba' : 'abcdefgh').split('').map((f) => (
          <span key={f} className="chess-file">{f}</span>
        ))}
      </div>
    </div>
  )
}

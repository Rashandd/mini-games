import { useState } from 'react'

const PIECE_DISPLAY = {
  1: '⬤', 2: '⬤', '1k': '♛', '2k': '♛'
}

export default function CheckersBoard({ state, yourPlayer, onMove, gameOver }) {
  const board = state?.board || []
  const currentPlayer = state?.current_player || 1
  const [selected, setSelected] = useState(null)

  const isFlipped = yourPlayer === 2

  const handleClick = (row, col) => {
    if (gameOver || currentPlayer !== yourPlayer) return

    if (selected) {
      onMove({ from_row: selected.row, from_col: selected.col, to_row: row, to_col: col })
      setSelected(null)
    } else {
      const cell = board[row]?.[col]
      if (cell) setSelected({ row, col })
    }
  }

  const renderBoard = () => {
    const rows = isFlipped ? [...Array(8).keys()].reverse() : [...Array(8).keys()]
    const cols = isFlipped ? [...Array(8).keys()].reverse() : [...Array(8).keys()]

    return rows.map((r) => (
      <div key={r} className="checkers-row">
        {cols.map((c) => {
          const cell = board[r]?.[c]
          const isPlayable = (r + c) % 2 === 1
          const isSelected = selected?.row === r && selected?.col === c
          return (
            <button
              key={c}
              className={`checkers-cell ${isPlayable ? 'playable' : 'non-playable'} ${isSelected ? 'selected' : ''}`}
              onClick={() => isPlayable && handleClick(r, c)}
            >
              {cell ? (
                <span className={`checker-piece player-${typeof cell === 'object' ? cell.player : cell} ${(typeof cell === 'object' && cell.king) ? 'king' : ''}`}>
                  {typeof cell === 'object' && cell.king ? '♛' : '⬤'}
                </span>
              ) : ''}
            </button>
          )
        })}
      </div>
    ))
  }

  return (
    <div className="board-container checkers-board-container">
      <div className="turn-indicator">
        {gameOver ? '' : currentPlayer === yourPlayer
          ? <><i className="fa-solid fa-circle" style={{ color: 'var(--accent-green)' }}></i> Your Turn</>
          : <><i className="fa-solid fa-circle" style={{ color: '#ef5350' }}></i> Opponent's Turn</>
        }
      </div>
      <div className="checkers-grid">{renderBoard()}</div>
    </div>
  )
}

import { create } from 'zustand'
import { getSocket } from '../socket'

const useGameStore = create((set, get) => ({
  roomCode: null,
  gameSlug: null,
  gameName: null,
  status: null,
  state: null,
  player1: null,
  player2: null,
  yourPlayer: null,
  gameOver: false,
  winner: null,
  winnerName: null,
  resigned: null,
  isPrivate: false,
  isSpectator: false,

  reset: () => set({
    roomCode: null, gameSlug: null, gameName: null, status: null,
    state: null, player1: null, player2: null, yourPlayer: null,
    gameOver: false, winner: null, winnerName: null, resigned: null,
    isPrivate: false, isSpectator: false,
  }),

  createGame: (gameSlug, isPrivate = false, password = '') => {
    const s = getSocket()
    if (!s) return
    const data = { game_slug: gameSlug }
    if (isPrivate) { data.is_private = true; data.password = password }
    s.emit('create_game', data)
  },

  joinGame: (roomCode, password = '') => {
    const s = getSocket()
    if (!s) return
    s.emit('join_game', { room_code: roomCode, password })
  },

  spectateGame: (roomCode) => {
    const s = getSocket()
    if (!s) return
    s.emit('spectate_game', { room_code: roomCode })
  },

  makeMove: (move) => {
    const s = getSocket()
    const { roomCode } = get()
    if (!s || !roomCode) return
    s.emit('make_move', { room_code: roomCode, move })
  },

  resignGame: () => {
    const s = getSocket()
    const { roomCode } = get()
    if (!s || !roomCode) return
    s.emit('resign', { room_code: roomCode })
  },

  findMatch: (gameSlug) => {
    const s = getSocket()
    if (!s) return
    s.emit('find_match', { game_slug: gameSlug })
  },

  deleteGame: (roomCode) => {
    const s = getSocket()
    if (!s) return
    s.emit('delete_game', { room_code: roomCode })
  },

  setupListeners: () => {
    const s = getSocket()
    if (!s) return

    s.on('game_created', (data) => {
      set({
        roomCode: data.room_code,
        gameSlug: data.game_slug,
        gameName: data.game_name,
        player1: data.player1,
        yourPlayer: 1,
        status: 'waiting',
        state: null,
        gameOver: false,
        isPrivate: !!data.is_private,
        isSpectator: false,
      })
    })

    s.on('game_joined', (data) => {
      // Player 2 receives this — set everything
      set({
        roomCode: data.room_code,
        gameSlug: data.game_slug,
        gameName: data.game_name,
        status: data.status,
        state: data.state,
        player1: data.player1,
        player2: data.player2,
        yourPlayer: data.your_player,
        gameOver: false,
        isSpectator: false,
      })
    })

    // Player 1 receives this when Player 2 joins
    // Only update what changed — preserve yourPlayer=1
    s.on('game_started', (data) => {
      const update = {
        status: data.status,
        state: data.state,
        player2: data.player2,
        gameOver: false,
      }
      if (data.game_slug) update.gameSlug = data.game_slug
      if (data.game_name) update.gameName = data.game_name
      if (data.player1) update.player1 = data.player1
      set(update)
    })

    // Spectator receives this when joining a game
    s.on('spectate_joined', (data) => {
      set({
        roomCode: data.room_code,
        gameSlug: data.game_slug,
        gameName: data.game_name,
        status: data.status,
        state: data.state,
        player1: data.player1,
        player2: data.player2,
        yourPlayer: null,
        gameOver: false,
        isSpectator: true,
      })
    })

    s.on('move_error', (data) => {
      console.warn('Move error:', data?.message)
    })

    s.on('game_update', (data) => {
      const update = { state: data.state }
      if (data.game_over) {
        update.gameOver = true
        update.winner = data.winner
        update.winnerName = data.winner_name
        update.status = 'finished'
        if (data.resigned) update.resigned = data.resigned
      }
      set(update)
    })

    s.on('room_deleted', () => {
      get().reset()
    })

    s.on('error', (data) => {
      console.warn('Game error:', data?.message)
    })
  },

  cleanupListeners: () => {
    const s = getSocket()
    if (!s) return
    s.off('game_created')
    s.off('game_joined')
    s.off('game_started')
    s.off('game_update')
    s.off('move_error')
    s.off('room_deleted')
    s.off('spectate_joined')
    s.off('error')
  },
}))

export default useGameStore

import { io } from 'socket.io-client'

let socket = null

export function getSocket() {
  if (socket) return socket
  const token = localStorage.getItem('token')
  if (!token) return null
  socket = io('/', {
    auth: { token },
    transports: ['websocket', 'polling'],
  })
  socket.on('connect', () => console.log('[Socket] Connected'))
  socket.on('disconnect', () => console.log('[Socket] Disconnected'))
  socket.on('connect_error', (err) => console.error('[Socket] Error:', err.message))
  return socket
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

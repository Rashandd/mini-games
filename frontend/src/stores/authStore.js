import { create } from 'zustand'
import api from '../api'
import { getSocket, disconnectSocket } from '../socket'

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  loading: true,

  init: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      set({ loading: false })
      return
    }
    try {
      const { data } = await api.get('/auth/me')
      set({ user: data, token, loading: false })
      getSocket()
    } catch {
      localStorage.removeItem('token')
      set({ user: null, token: null, loading: false })
    }
  },

  login: async (username, password) => {
    const { data } = await api.post('/auth/login', { username, password })
    localStorage.setItem('token', data.access_token)
    set({ user: { id: data.user_id, username: data.username }, token: data.access_token })
    getSocket()
    return data
  },

  register: async (username, password) => {
    const { data } = await api.post('/auth/register', { username, password })
    localStorage.setItem('token', data.access_token)
    set({ user: { id: data.user_id, username: data.username }, token: data.access_token })
    getSocket()
    return data
  },

  logout: () => {
    localStorage.removeItem('token')
    disconnectSocket()
    set({ user: null, token: null })
  },
}))

export default useAuthStore

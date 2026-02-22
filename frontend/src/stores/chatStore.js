import { create } from 'zustand'
import { getSocket } from '../socket'

const useChatStore = create((set, get) => ({
  rooms: [],
  activeRoomId: null,
  messages: [],
  unreadCount: 0,

  setActiveRoom: (roomId) => {
    set({ activeRoomId: roomId, messages: [], unreadCount: 0 })
    const s = getSocket()
    if (!s) return
    s.emit('join_chat', { room_id: roomId })
    s.emit('load_messages', { room_id: roomId })
  },

  clearUnread: () => set({ unreadCount: 0 }),

  fetchRooms: () => {
    const s = getSocket()
    if (!s) return
    s.emit('list_rooms')
  },

  createDM: (targetUserId) => {
    const s = getSocket()
    if (!s) return
    s.emit('create_dm', { target_user_id: targetUserId })
  },

  createGroup: (name) => {
    const s = getSocket()
    if (!s) return
    s.emit('create_group', { name })
  },

  sendMessage: (content) => {
    const s = getSocket()
    const { activeRoomId } = get()
    if (!s || !activeRoomId || !content.trim()) return
    s.emit('send_message', { room_id: activeRoomId, content })
  },

  muteUser: (mutedUserId) => {
    const s = getSocket()
    const { activeRoomId } = get()
    if (!s) return
    s.emit('chat_mute', { muted_user_id: mutedUserId, room_id: activeRoomId })
  },

  reportUser: (reportedUserId, reason) => {
    const s = getSocket()
    const { activeRoomId } = get()
    if (!s) return
    s.emit('chat_report', { reported_user_id: reportedUserId, room_id: activeRoomId, reason })
  },

  leaveRoom: (roomId) => {
    const s = getSocket()
    if (!s) return
    s.emit('chat_leave', { room_id: roomId })
    const { rooms, activeRoomId } = get()
    set({ rooms: rooms.filter((r) => r.id !== roomId) })
    if (activeRoomId === roomId) set({ activeRoomId: null, messages: [] })
  },

  setupListeners: () => {
    const s = getSocket()
    if (!s) return

    s.on('room_list', (data) => set({ rooms: data.rooms }))
    s.on('message_history', (data) => {
      if (data.room_id === get().activeRoomId) {
        set({ messages: data.messages })
      }
    })
    s.on('new_message', (msg) => {
      const { activeRoomId, unreadCount } = get()
      if (msg.room_id === activeRoomId) {
        set({ messages: [...get().messages, msg] })
      } else {
        // Message for a room we're not viewing — increment unread
        set({ unreadCount: unreadCount + 1 })
      }
    })
    s.on('dm_created', (data) => {
      get().fetchRooms()
      // Use setActiveRoom so we emit join_chat + load_messages
      setTimeout(() => get().setActiveRoom(data.room_id), 300)
    })
    s.on('group_created', (data) => {
      get().fetchRooms()
      setTimeout(() => get().setActiveRoom(data.room_id), 300)
    })
    // When another user creates a DM with us, refresh our room list
    s.on('room_list_updated', () => {
      get().fetchRooms()
    })
  },

  cleanupListeners: () => {
    const s = getSocket()
    if (!s) return
    s.off('room_list')
    s.off('message_history')
    s.off('new_message')
    s.off('dm_created')
    s.off('group_created')
    s.off('room_list_updated')
  },
}))

export default useChatStore

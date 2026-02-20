import { useEffect, useRef, useState } from 'react'
import useChatStore from '../stores/chatStore'
import useAuthStore from '../stores/authStore'
import api from '../api'

export default function ChatSidebar() {
  const [open, setOpen] = useState(false)
  const [msgInput, setMsgInput] = useState('')
  const [searchUser, setSearchUser] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showNewGroup, setShowNewGroup] = useState(false)
  const [groupName, setGroupName] = useState('')
  const messagesEndRef = useRef(null)

  const chat = useChatStore()
  const user = useAuthStore((s) => s.user)

  useEffect(() => {
    chat.setupListeners()
    chat.fetchRooms()
    return () => chat.cleanupListeners()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat.messages])

  const handleSend = (e) => {
    e.preventDefault()
    if (!msgInput.trim()) return
    chat.sendMessage(msgInput)
    setMsgInput('')
  }

  const handleSearchUser = async (q) => {
    setSearchUser(q)
    if (q.length < 2) { setSearchResults([]); return }
    try {
      const { data } = await api.get(`/users/search?q=${q}`)
      setSearchResults(data.filter((u) => u.id !== user?.id))
    } catch { setSearchResults([]) }
  }

  const startDM = (targetId) => {
    chat.createDM(targetId)
    setSearchUser('')
    setSearchResults([])
  }

  const createGroup = () => {
    if (!groupName.trim()) return
    chat.createGroup(groupName)
    setGroupName('')
    setShowNewGroup(false)
  }

  return (
    <>
      <button className="chat-toggle-btn" onClick={() => setOpen(!open)}>
        💬
      </button>

      <div className={`chat-sidebar ${open ? 'open' : ''}`}>
        <div className="chat-sidebar-header">
          <h3>Chat</h3>
          <button className="btn btn-sm btn-ghost" onClick={() => setOpen(false)}>✕</button>
        </div>

        {!chat.activeRoomId ? (
          <div className="chat-room-list">
            {/* Search for DM */}
            <div className="chat-search">
              <input
                className="form-input form-input-sm"
                placeholder="Search user for DM..."
                value={searchUser}
                onChange={(e) => handleSearchUser(e.target.value)}
              />
              {searchResults.length > 0 && (
                <div className="search-results">
                  {searchResults.map((u) => (
                    <div key={u.id} className="search-result-item" onClick={() => startDM(u.id)}>
                      👤 {u.username}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button className="btn btn-sm btn-accent btn-full" onClick={() => setShowNewGroup(!showNewGroup)}>
              + New Group
            </button>
            {showNewGroup && (
              <div className="new-group-form">
                <input className="form-input form-input-sm" placeholder="Group name..." value={groupName} onChange={(e) => setGroupName(e.target.value)} />
                <button className="btn btn-sm btn-primary" onClick={createGroup}>Create</button>
              </div>
            )}

            <div className="room-items">
              {chat.rooms.map((r) => (
                <div key={r.id} className="room-item" onClick={() => chat.setActiveRoom(r.id)}>
                  <span className="room-icon">{r.type === 'dm' ? '👤' : '👥'}</span>
                  <span className="room-name">{r.name}</span>
                </div>
              ))}
              {chat.rooms.length === 0 && <p className="muted center">No chats yet</p>}
            </div>
          </div>
        ) : (
          <div className="chat-messages-view">
            <div className="chat-messages-header">
              <button className="btn btn-sm btn-ghost" onClick={() => useChatStore.setState({ activeRoomId: null, messages: [] })}>← Back</button>
              <span className="chat-room-name">{chat.rooms.find((r) => r.id === chat.activeRoomId)?.name || 'Chat'}</span>
            </div>

            <div className="chat-messages">
              {chat.messages.map((m, i) => (
                <div key={m.id || i} className={`chat-msg ${m.user_id === user?.id ? 'mine' : ''}`}>
                  <span className="chat-msg-user">{m.username}</span>
                  <span className="chat-msg-text">{m.content}</span>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <form className="chat-input-bar" onSubmit={handleSend}>
              <input
                className="form-input form-input-sm"
                placeholder="Type a message..."
                value={msgInput}
                onChange={(e) => setMsgInput(e.target.value)}
              />
              <button className="btn btn-sm btn-primary" type="submit">Send</button>
            </form>
          </div>
        )}
      </div>
    </>
  )
}

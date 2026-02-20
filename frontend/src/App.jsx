import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import useAuthStore from './stores/authStore'
import Navbar from './components/Navbar'
import ChatSidebar from './components/ChatSidebar'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import GameRoomPage from './pages/GameRoomPage'
import LeaderboardPage from './pages/LeaderboardPage'
import VillageSelectPage from './pages/VillageSelectPage'
import SEPlayPage from './pages/SEPlayPage'

function ProtectedRoute({ children }) {
  const user = useAuthStore((s) => s.user)
  const loading = useAuthStore((s) => s.loading)
  if (loading) return <div className="page-loading"><div className="spinner"></div></div>
  if (!user) return <Navigate to="/login" />
  return children
}

export default function App() {
  const init = useAuthStore((s) => s.init)

  useEffect(() => { init() }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <div className="app-layout">
              <Navbar />
              <main className="app-main">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/game/:slug" element={<GameRoomPage />} />
                  <Route path="/leaderboard" element={<LeaderboardPage />} />
                  <Route path="/leaderboard/:slug" element={<LeaderboardPage />} />
                  <Route path="/social-empires" element={<VillageSelectPage />} />
                  <Route path="/social-empires/play/:userid" element={<SEPlayPage />} />
                </Routes>
              </main>
              <ChatSidebar />
            </div>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}

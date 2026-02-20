import { useParams } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import api from '../api'

const GAME_VERSION = 'SocialEmpires0926bsec.swf'

export default function SEPlayPage() {
  const { userid } = useParams()
  const ruffleRef = useRef(null)
  const [status, setStatus] = useState('Loading...')

  useEffect(() => {
    let cancelled = false

    async function init() {
      // Fetch server time and friends info
      let serverTime = Math.floor(Date.now() / 1000)
      let friendsInfo = '[]'
      try {
        const [timeRes, friendsRes] = await Promise.all([
          api.get('/se/server_time'),
          api.get(`/se/fb_friends?USERID=${userid}`),
        ])
        serverTime = timeRes.data.serverTime || serverTime
        friendsInfo = typeof friendsRes.data === 'string'
          ? friendsRes.data
          : JSON.stringify(friendsRes.data)
      } catch (e) {
        console.warn('Failed to fetch SE metadata:', e)
      }

      if (cancelled) return
      setStatus('Loading Ruffle...')

      // Load Ruffle — use a script tag outside React's DOM tree
      if (!window.RufflePlayer) {
        await new Promise((resolve, reject) => {
          const script = document.createElement('script')
          script.src = 'https://unpkg.com/@ruffle-rs/ruffle'
          script.onload = resolve
          script.onerror = reject
          document.head.appendChild(script)
        })
      }

      if (cancelled || !window.RufflePlayer || !ruffleRef.current) return
      setStatus('Loading SWF...')

      const ruffle = window.RufflePlayer.newest()
      const player = ruffle.createPlayer()
      player.style.width = '760px'
      player.style.height = '625px'
      player.style.display = 'block'

      // Append to the raw DOM ref (React won't touch this div's children)
      ruffleRef.current.appendChild(player)

      player.load({
        url: `/default01.static.socialpointgames.com/static/socialempires/flash/SELoader.swf?swftoload=/default01.static.socialpointgames.com/static/socialempires/flash/${GAME_VERSION}`,
        backgroundColor: '#669C2C',
        allowScriptAccess: false,
        autoplay: true,
        parameters: [
          'spdebug=notnull&brk=0',
          `staticUrl=/default01.static.socialpointgames.com/static/socialempires/&brk=0`,
          `dynamicUrl=/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/&brk=0`,
          'skiphash12341=notnull&brk=0',
          `fb_sig_user=${userid}&brk=0`,
          'user_key=123456789&brk=0',
          'language=en&brk=0',
          'accessToken=AAABbZAm0wdMUBALsOrR0Ho68CLjaOT8SV3vftKg9mbo1zZColaW5FljRVaLxPGxXXnm1M98mTZCAttcQ4GHwvSyXfsyxYmvKMH8Hmn5iliSPnjvIsZA6&brk=0',
          'sex=m&brk=0',
          'lastLoggedIn=1349266517&brk=0',
          'dailyBonus=0&brk=0',
          `friendsInfo=${friendsInfo}&brk=0`,
          `serverTime=${serverTime}&brk=0`,
          'forceSyncError=1&brk=0',
          'forceAttackReload=0&brk=0',
          'forceQuestReload=0&brk=0',
        ].join('&'),
      })

      setStatus('')
    }

    init()

    return () => {
      cancelled = true
      // Clean up Ruffle player on unmount — use raw DOM, not React
      if (ruffleRef.current) {
        ruffleRef.current.innerHTML = ''
      }
    }
  }, [userid])

  return (
    <div className="se-play-page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <span style={{ fontSize: '1.5rem' }}>⚔️</span>
        <span style={{ fontWeight: 700 }}>Social Empires</span>
      </div>

      {/* Status message — outside the Ruffle container so React doesn't conflict */}
      {status && (
        <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>
          <div className="spinner center-spinner" style={{ marginBottom: 12 }}></div>
          <p>{status}</p>
        </div>
      )}

      {/* Ruffle mounts here — React never touches children of this div */}
      <div
        ref={ruffleRef}
        style={{ width: 760, height: 625, margin: '0 auto', background: '#669C2C', borderRadius: 8 }}
      />

      <div style={{ textAlign: 'center', marginTop: 12, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        Powered by <a href="https://ruffle.rs/" target="_blank" rel="noreferrer">Ruffle</a> Flash Emulator
      </div>
    </div>
  )
}

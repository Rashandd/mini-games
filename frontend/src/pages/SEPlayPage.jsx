import { useParams } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import api from '../api'

const GAME_VERSION = 'SocialEmpires0926bsec.swf'

export default function SEPlayPage() {
  const { userid } = useParams()
  const ruffleRef = useRef(null)
  const playerRef = useRef(null)
  const [status, setStatus] = useState('Loading...')
  const [volume, setVolume] = useState(50)

  const handleVolume = (val) => {
    setVolume(val)
    if (playerRef.current && typeof playerRef.current.volume !== 'undefined') {
      playerRef.current.volume = val / 100
    }
  }

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
      playerRef.current = player

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
          'forceSyncError=0&brk=0',
          'forceAttackReload=0&brk=0',
          'forceQuestReload=0&brk=0',
        ].join('&'),
      })

      // Apply initial volume
      if (typeof player.volume !== 'undefined') {
        player.volume = volume / 100
      }

      setStatus('')
    }

    init()

    return () => {
      cancelled = true
      playerRef.current = null
      // Clean up Ruffle player on unmount — use raw DOM, not React
      if (ruffleRef.current) {
        ruffleRef.current.innerHTML = ''
      }
    }
  }, [userid])

  return (
    <div className="se-play-page">
      {/* Status message — outside the Ruffle container so React doesn't conflict */}
      {status && (
        <div className="game-loading">
          <div className="spinner center-spinner"></div>
          <p>{status}</p>
        </div>
      )}

      {/* Ruffle mounts here — React never touches children of this div */}
      <div ref={ruffleRef} className="se-ruffle-container" />

      {/* Volume control */}
      <div className="game-controls-bar">
        <div className="volume-control">
          <span className="volume-icon" onClick={() => handleVolume(volume > 0 ? 0 : 50)}>
            {volume === 0 ? '🔇' : volume < 40 ? '🔉' : '🔊'}
          </span>
          <input
            type="range"
            min="0"
            max="100"
            value={volume}
            onChange={(e) => handleVolume(Number(e.target.value))}
            className="volume-slider"
          />
          <span className="volume-value">{volume}%</span>
        </div>
        <div className="game-credits">
          Powered by <a href="https://ruffle.rs/" target="_blank" rel="noreferrer">Ruffle</a> Flash Emulator
        </div>
      </div>

      {/* Game title bar — positioned below controls */}
      <div className="game-title-bar">
        <span className="game-title-icon">⚔️</span>
        <span className="game-title-name">Social Empires</span>
      </div>

      {/* Tutorial */}
      <div className="game-tutorial">
        <h3>📖 How to Play Social Empires</h3>
        <div className="tutorial-steps">
          <div className="tutorial-step">
            <span className="step-num">1</span>
            <div>
              <strong>Build Your Empire</strong>
              <p>Place buildings from the <em>BUILD</em> menu (bottom-right). Start with houses to increase population and mills to produce gold.</p>
            </div>
          </div>
          <div className="tutorial-step">
            <span className="step-num">2</span>
            <div>
              <strong>Train Your Army</strong>
              <p>Build barracks and training camps. Click them to recruit soldiers — you'll need warriors, archers, and cavalry to defend your empire.</p>
            </div>
          </div>
          <div className="tutorial-step">
            <span className="step-num">3</span>
            <div>
              <strong>Collect Resources</strong>
              <p>Click on buildings when they show a coin/resource icon to collect gold, food, wood, and stone. Use these to expand.</p>
            </div>
          </div>
          <div className="tutorial-step">
            <span className="step-num">4</span>
            <div>
              <strong>Complete Quests</strong>
              <p>Follow Arthur's tutorial quests for rewards. Check the quest panel on the left side for objectives and XP bonuses.</p>
            </div>
          </div>
          <div className="tutorial-step">
            <span className="step-num">5</span>
            <div>
              <strong>Battle Enemies</strong>
              <p>Drag your troops to attack enemy units and bosses that appear on your map. Winning battles earns experience and rare items.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

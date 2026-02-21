import { useState } from 'react'

export default function WaveDrifterPage() {
  const [loading, setLoading] = useState(true)
  const [volume, setVolume] = useState(50)

  return (
    <div className="se-play-page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <span style={{ fontSize: '1.5rem' }}>🏴‍☠️</span>
        <span style={{ fontWeight: 700 }}>Wave Drifter</span>
      </div>

      {/* Loading indicator */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>
          <div className="spinner center-spinner" style={{ marginBottom: 12 }}></div>
          <p>Loading Wave Drifter...</p>
        </div>
      )}

      {/* Game iframe — self-hosted Godot HTML5 export */}
      <iframe
        src="/wave-drifter-assets/index.html"
        title="Wave Drifter"
        onLoad={() => setLoading(false)}
        style={{
          width: '100%',
          maxWidth: 960,
          height: 640,
          border: 'none',
          borderRadius: 8,
          display: loading ? 'none' : 'block',
          margin: '0 auto',
          background: '#1a1a2e',
        }}
        allowFullScreen
      />

      {/* Volume control */}
      <div className="game-controls-bar">
        <div className="volume-control">
          <span className="volume-icon" onClick={() => setVolume(volume > 0 ? 0 : 50)}>
            {volume === 0 ? '🔇' : volume < 40 ? '🔉' : '🔊'}
          </span>
          <input
            type="range"
            min="0"
            max="100"
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            className="volume-slider"
          />
          <span className="volume-value">{volume}%</span>
        </div>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          Built with <a href="https://godotengine.org/" target="_blank" rel="noreferrer">Godot Engine</a>
          {' · '}
          <a href="https://github.com/Yolo-Arts/Wave-Drifter" target="_blank" rel="noreferrer">Source on GitHub</a>
        </div>
      </div>

      {/* Tutorial */}
      <div className="game-tutorial">
        <h3>📖 How to Play Wave Drifter</h3>
        <div className="tutorial-steps">
          <div className="tutorial-step">
            <span className="step-num">1</span>
            <div>
              <strong>Steer Your Ship</strong>
              <p>Use <em>WASD</em> or <em>Arrow Keys</em> to navigate your pirate ship through the waters. Your ship is isometric — up moves top-right!</p>
            </div>
          </div>
          <div className="tutorial-step">
            <span className="step-num">2</span>
            <div>
              <strong>Dodge the Royal Navy</strong>
              <p>Enemy ships patrol the waters. Avoid their cannon fire and ramming attacks to stay alive as long as possible.</p>
            </div>
          </div>
          <div className="tutorial-step">
            <span className="step-num">3</span>
            <div>
              <strong>Fire Your Cannons</strong>
              <p>Press <em>Space</em> or <em>Click</em> to fire at enemy ships. Destroy them before they destroy you!</p>
            </div>
          </div>
          <div className="tutorial-step">
            <span className="step-num">4</span>
            <div>
              <strong>Collect Power-ups</strong>
              <p>Pick up floating crates and items to repair your ship, boost speed, or upgrade your cannons.</p>
            </div>
          </div>
          <div className="tutorial-step">
            <span className="step-num">5</span>
            <div>
              <strong>Survive & Score</strong>
              <p>The longer you survive and the more enemies you destroy, the higher your score. Try to beat your personal best!</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


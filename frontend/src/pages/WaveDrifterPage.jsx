import { useState } from 'react'

export default function WaveDrifterPage() {
  const [loading, setLoading] = useState(true)
  const [volume, setVolume] = useState(50)

  const getVolumeIcon = () => {
    if (volume === 0) return 'fa-volume-xmark'
    if (volume < 40) return 'fa-volume-low'
    return 'fa-volume-high'
  }

  return (
    <div className="se-play-page">
      {loading && (
        <div className="game-loading">
          <div className="spinner center-spinner"></div>
          <p>Loading Wave Drifter...</p>
        </div>
      )}

      <iframe
        src="/wave-drifter-assets/index.html"
        title="Wave Drifter"
        onLoad={() => setLoading(false)}
        className="wd-iframe"
        style={{ display: loading ? 'none' : 'block' }}
        allowFullScreen
      />

      {/* Volume control */}
      <div className="game-controls-bar">
        <div className="volume-control">
          <span className="volume-icon" onClick={() => setVolume(volume > 0 ? 0 : 50)}>
            <i className={`fa-solid ${getVolumeIcon()}`}></i>
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
        <div className="game-credits">
          Built with <a href="https://godotengine.org/" target="_blank" rel="noreferrer">Godot Engine</a>
          {' · '}
          <a href="https://github.com/Yolo-Arts/Wave-Drifter" target="_blank" rel="noreferrer">Source on GitHub</a>
        </div>
      </div>

      {/* Game title bar — positioned below controls */}
      <div className="game-title-bar">
        <span className="game-title-icon">
          <i className="fa-solid fa-skull-crossbones"></i>
        </span>
        <span className="game-title-name">Wave Drifter</span>
      </div>

      {/* Tutorial */}
      <div className="game-tutorial">
        <h3><i className="fa-solid fa-book-open"></i> How to Play Wave Drifter</h3>
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
              <strong>Survive &amp; Score</strong>
              <p>The longer you survive and the more enemies you destroy, the higher your score. Try to beat your personal best!</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

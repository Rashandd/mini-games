import { useState } from 'react'

export default function WaveDrifterPage() {
  const [loading, setLoading] = useState(true)

  return (
    <div className="se-play-page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
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

      <div style={{ textAlign: 'center', marginTop: 12, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        Built with <a href="https://godotengine.org/" target="_blank" rel="noreferrer">Godot Engine</a>
        {' · '}
        <a href="https://github.com/Yolo-Arts/Wave-Drifter" target="_blank" rel="noreferrer">Source on GitHub</a>
      </div>
    </div>
  )
}

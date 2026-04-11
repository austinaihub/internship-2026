import { useState } from 'react'
import { startCampaign } from '../api'

export default function StartPage({ onStart }) {
  const [keywords, setKeywords] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleStart = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await startCampaign(keywords)
      onStart(data.session_id, data.state)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="page-center">
      <div style={{ maxWidth: 480, width: '100%' }}>
        <div className="fade-in">
          <h1 className="hero-title mb-sm">Agent-9</h1>
          <p className="text-muted mb-xl" style={{ fontSize: 'var(--font-size-heading)' }}>
            Human Trafficking<br />Awareness Campaign
          </p>
        </div>

        <div className="fade-in fade-in-delay-1">
          <label className="input-label" htmlFor="keywords">
            🔍 Search Keywords
          </label>
          <input
            id="keywords"
            className="input"
            type="text"
            placeholder="e.g. 'forced labor supply chain', 'trafficking conviction'"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleStart()}
            disabled={loading}
          />
          <p className="input-help">
            Leave blank to use automated trend discovery
          </p>
        </div>

        <div className="fade-in fade-in-delay-2 mt-lg">
          <button
            className="btn btn-primary btn-lg"
            onClick={handleStart}
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'Starting...' : '▶ Start Campaign'}
          </button>
        </div>

        {error && (
          <div className="alert alert-error mt-md fade-in">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  )
}

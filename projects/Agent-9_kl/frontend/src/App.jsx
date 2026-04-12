import { useState, useEffect, useCallback } from 'react'
import { getState, startCampaign } from './api'
import Sidebar from './components/Sidebar'
import TrendReview from './pages/TrendReview'
import ImageReview from './pages/ImageReview'
import DonePage from './pages/DonePage'

const PAUSE_STATES = ['approving_trend', 'approving_image', 'done', 'error']

// ── Start Section (full-screen, no sidebar) ─────────────────────────────────
function StartSection({ onStart }) {
  const [keywords, setKeywords] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleStart = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await startCampaign(keywords)
      onStart(data.session_id, data.state, keywords)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="page-center">
      <div className="start-container fade-in">
        <h1 className="hero-title">Agent-9</h1>
        <p className="caption">Human Trafficking Awareness Campaign Generator</p>

        <div style={{ textAlign: 'left', width: '100%' }}>
          <label className="input-label" htmlFor="keywords">
            Search Keywords (optional)
          </label>
          <input
            id="keywords"
            className="input"
            type="text"
            placeholder="e.g. 'forced labor', 'trafficking conviction' — blank for auto"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleStart()}
            disabled={loading}
          />
          <p className="input-help mb-lg">
            Leave blank to use automated trend discovery with diverse queries.
          </p>

          <button
            className="btn btn-primary btn-lg"
            onClick={handleStart}
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'Starting...' : 'Start Campaign'}
          </button>
        </div>

        {error && <div className="alert alert-error mt-sm">{error}</div>}
      </div>
    </div>
  )
}

// ── Processing View ─────────────────────────────────────────────────────────
function ProcessingView({ label }) {
  return (
    <div className="processing-view fade-in">
      <div className="spinner" />
      <span className="processing-label">{label}</span>
    </div>
  )
}

// ── Main App ────────────────────────────────────────────────────────────────
export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [campaignState, setCampaignState] = useState(null)
  const [inputHistory, setInputHistory] = useState([])

  const recordInput = useCallback((entry) => {
    setInputHistory(prev => [...prev, { ...entry, timestamp: Date.now() }])
  }, [])

  // Poll during intermediate pipeline stages
  useEffect(() => {
    if (!sessionId || !campaignState) return
    const status = campaignState.status
    if (PAUSE_STATES.includes(status)) return

    const interval = setInterval(async () => {
      try {
        const data = await getState(sessionId)
        setCampaignState(data.state)
        if (!data.has_next || PAUSE_STATES.includes(data.state.status)) {
          clearInterval(interval)
        }
      } catch (err) {
        console.error('Poll error:', err)
        clearInterval(interval)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [sessionId, campaignState?.status])

  const handleStart = useCallback((newSessionId, state, keywords) => {
    setSessionId(newSessionId)
    setCampaignState(state)
    setInputHistory([{
      step: 'start',
      timestamp: Date.now(),
      action: 'start',
      keywords: keywords || 'Auto discovery',
    }])
  }, [])

  const handleUpdate = useCallback((state, newSessionId) => {
    if (newSessionId) setSessionId(newSessionId)
    setCampaignState(state)
  }, [])

  const handleNewCampaign = useCallback(() => {
    setSessionId(null)
    setCampaignState(null)
    setInputHistory([])
  }, [])

  // ── Pre-campaign: show full-screen start page ──────────────────────────
  if (!sessionId) {
    return <StartSection onStart={handleStart} />
  }

  // ── Campaign active: sidebar layout ────────────────────────────────────
  const status = campaignState?.status
  const cs = campaignState

  // Determine processing label for intermediate states
  const processingLabels = {
    starting: 'Searching for news...',
    approved_trend: 'Analyzing audience...',
    audience_approved: 'Writing post...',
    audience_selected: 'Analyzing audience...',
    approved_text: 'Generating image...',
  }
  const isProcessing = status && !PAUSE_STATES.includes(status)

  return (
    <div className="app-shell">
      <Sidebar state={cs} status={status} inputHistory={inputHistory} />

      <main className="main-content">
        <div className="main-inner">

          {/* Trend Review HITL */}
          {status === 'approving_trend' && (
            <div className="fade-in">
              <h1 className="main-title">Review News Topic</h1>
              <TrendReview
                state={cs}
                sessionId={sessionId}
                onUpdate={handleUpdate}
                recordInput={recordInput}
              />
            </div>
          )}

          {/* Image + Text Review HITL */}
          {status === 'approving_image' && (
            <div className="fade-in">
              <h1 className="main-title">Review Generated Content</h1>
              <ImageReview
                state={cs}
                sessionId={sessionId}
                onUpdate={handleUpdate}
                recordInput={recordInput}
              />
            </div>
          )}

          {/* Done */}
          {status === 'done' && (
            <div className="fade-in">
              <h1 className="main-title">Campaign Published</h1>
              <DonePage
                state={cs}
                sessionId={sessionId}
                onUpdate={handleUpdate}
                onNewCampaign={handleNewCampaign}
                recordInput={recordInput}
              />
            </div>
          )}

          {/* Error */}
          {status === 'error' && (
            <div className="fade-in">
              <h1 className="main-title">Error</h1>
              <div className="alert alert-error mb-lg">
                {cs?.feedback || 'An error occurred during processing.'}
              </div>
              <button className="btn btn-secondary" onClick={handleNewCampaign}>
                Start New Campaign
              </button>
            </div>
          )}

          {/* Pipeline intermediate stages → processing indicator */}
          {isProcessing && (
            <ProcessingView
              label={processingLabels[status] || 'Processing...'}
            />
          )}

        </div>
      </main>
    </div>
  )
}

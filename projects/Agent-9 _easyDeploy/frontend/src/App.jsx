import { useState, useEffect, useCallback } from 'react'
import { getState } from './api'
import Sidebar from './components/Sidebar'
import WorkflowStepper from './components/WorkflowStepper'
import LoadingScreen from './components/LoadingScreen'
import StartPage from './pages/StartPage'
import TrendReview from './pages/TrendReview'
import AudienceReview from './pages/AudienceReview'
import ImageReview from './pages/ImageReview'
import DonePage from './pages/DonePage'

const PAUSE_STATES = ['approving_trend', 'approving_audience', 'approving_image', 'done', 'error']

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

  // ── Unified layout: always render app-shell + Sidebar + main ──────────
  const status = sessionId ? campaignState?.status : 'pre_start'
  const cs = campaignState
  const isProcessing = sessionId && status && !PAUSE_STATES.includes(status)

  return (
    <div className="app-shell">
      <Sidebar state={cs} status={status} inputHistory={inputHistory} />

      <main className="main-content main-content--with-footer">
        <div className="main-inner">

          {/* Pre-campaign: Start page (owns its own hero) */}
          {!sessionId && <StartPage onStart={handleStart} />}

          {/* Trend Review HITL */}
          {sessionId && status === 'approving_trend' && (
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

          {/* Audience Review HITL */}
          {sessionId && status === 'approving_audience' && (
            <div className="fade-in">
              <h1 className="main-title">Review Audience Strategy</h1>
              <AudienceReview
                state={cs}
                sessionId={sessionId}
                onUpdate={handleUpdate}
                recordInput={recordInput}
              />
            </div>
          )}

          {/* Image + Text Review HITL */}
          {sessionId && status === 'approving_image' && (
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
          {sessionId && status === 'done' && (
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
          {sessionId && status === 'error' && (
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

          {/* Pipeline intermediate stages → loading screen with rotating taglines */}
          {isProcessing && <LoadingScreen status={status} />}

        </div>

        {/* Sticky workflow progress bar — always visible at bottom of main area */}
        <div className="main-footer-workflow">
          <WorkflowStepper state={cs} status={status} variant="horizontal" />
        </div>
      </main>
    </div>
  )
}

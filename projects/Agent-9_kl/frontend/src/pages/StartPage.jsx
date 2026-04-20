import { useState } from 'react'
import { Sparkles, ArrowRight, Newspaper, Zap, Bot, Search } from 'lucide-react'
import { startCampaign } from '../api'

const EXAMPLE_CHIPS = [
  'FIFA trafficking',
  'Modern Slavery Act',
  'Supply chain audit',
  'Forced labor',
  'Survivor recovery',
]

const STATS = [
  { icon: Bot, label: '6 AI agents', sub: 'Multi-agent pipeline' },
  { icon: Newspaper, label: '13 news sources', sub: 'Reuters, AP, BBC, UN…' },
  { icon: Zap, label: '15–30 seconds', sub: 'End-to-end generation' },
]

export default function StartPage({ onStart }) {
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

  const handleChipClick = (text) => {
    setKeywords(text)
  }

  return (
    <div className="start-hero fade-in">
      <div className="start-brand">
        <span className="start-brand-mark">
          <Sparkles size={14} strokeWidth={2.2} />
        </span>
        <span className="start-brand-text">
          Campaign <strong>Agent</strong>
        </span>
      </div>

      <h1 className="start-headline">
        Generate awareness campaigns
        <br />
        <span className="start-headline-accent">that end human trafficking.</span>
      </h1>

      <p className="start-subtitle">
        Multi-agent AI drafts researched, audience-targeted social posts in under 30 seconds.
        Edit anything, keep what works.
      </p>

      <div className={`start-composer ${loading ? 'is-loading' : ''}`}>
        <Search size={18} strokeWidth={2} className="start-composer-icon" />
        <input
          className="start-composer-input"
          type="text"
          placeholder="A topic to research — or leave blank for auto-discovery"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !loading && handleStart()}
          disabled={loading}
          autoFocus
        />
        <button
          className="start-composer-btn"
          onClick={handleStart}
          disabled={loading}
          aria-label="Start campaign"
        >
          {loading ? (
            <span className="start-composer-spinner" />
          ) : (
            <ArrowRight size={18} strokeWidth={2.4} />
          )}
        </button>
      </div>

      <div className="start-chips">
        <span className="start-chips-label">Try:</span>
        {EXAMPLE_CHIPS.map((text) => (
          <button
            key={text}
            className="start-chip"
            onClick={() => handleChipClick(text)}
            disabled={loading}
            type="button"
          >
            {text}
          </button>
        ))}
      </div>

      {error && <div className="alert alert-error start-error">{error}</div>}

      <div className="start-stats">
        {STATS.map((s, i) => {
          const Icon = s.icon
          return (
            <div key={i} className="start-stat">
              <span className="start-stat-icon"><Icon size={16} strokeWidth={1.8} /></span>
              <div>
                <div className="start-stat-label">{s.label}</div>
                <div className="start-stat-sub">{s.sub}</div>
              </div>
            </div>
          )
        })}
      </div>

      <p className="start-footer-note">
        Built at the University of Texas at Austin · iSchool Capstone 2026
      </p>
    </div>
  )
}

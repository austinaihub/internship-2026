import { useState } from 'react'
import { approveTrend } from '../api'

export default function TrendReview({ state, sessionId, onUpdate, recordInput }) {
  const [selectedOption, setSelectedOption] = useState('ai')
  const [customTopic, setCustomTopic] = useState('')
  const [guidance, setGuidance] = useState('')
  const [loading, setLoading] = useState(false)
  const [linksOpen, setLinksOpen] = useState(false)

  const allNews = state.all_retrieved_news || []

  const handleApprove = async () => {
    setLoading(true)
    try {
      const payload = { action: 'approve' }

      if (customTopic.trim()) {
        payload.customTopic = customTopic.trim()
      } else if (selectedOption !== 'ai') {
        const article = allNews.find(a => a.title === selectedOption)
        if (article) payload.selectedArticleTitle = article.title
      }

      // Pass guidance if provided
      if (guidance.trim()) {
        payload.guidance = guidance.trim()
      }

      const data = await approveTrend(sessionId, payload)
      recordInput({
        step: 'trend_review',
        action: 'approve',
        customTopic: customTopic.trim() || null,
        guidance: guidance.trim() || null,
        selectedArticle: selectedOption !== 'ai' ? selectedOption : null,
      })
      onUpdate(data.state)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleResearch = async () => {
    setLoading(true)
    try {
      const data = await approveTrend(sessionId, { action: 're-search' })
      recordInput({ step: 'trend_review', action: 're-search' })
      onUpdate(data.state)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fade-in">

      {/* AI Recommendation */}
      <div className="card mb-lg">
        <p className="caption mb-xs">AI Recommended Topic</p>
        <h2 className="page-title mb-sm">{state.trend_topic || 'N/A'}</h2>
        <p style={{ color: 'var(--text-secondary)' }}>{state.trend_context || ''}</p>
      </div>

      {/* Article Selection */}
      {allNews.length > 0 && (
        <div className="mb-lg">
          <p className="section-title">Select a different source article</p>
          <div className="scroll-box">
            <div className="radio-group">
              <label
                className={`radio-option ${selectedOption === 'ai' ? 'selected' : ''}`}
                onClick={() => setSelectedOption('ai')}
              >
                <input
                  type="radio"
                  name="article"
                  checked={selectedOption === 'ai'}
                  onChange={() => setSelectedOption('ai')}
                />
                <div>
                  <div className="radio-option-label">Use AI Recommendation</div>
                  <div className="radio-option-subtitle">Keep the topic selected above</div>
                </div>
              </label>

              {allNews.map((article, i) => (
                <label
                  key={i}
                  className={`radio-option ${selectedOption === article.title ? 'selected' : ''}`}
                  onClick={() => setSelectedOption(article.title)}
                >
                  <input
                    type="radio"
                    name="article"
                    checked={selectedOption === article.title}
                    onChange={() => setSelectedOption(article.title)}
                  />
                  <div>
                    <div className="radio-option-label">{article.title || 'Untitled'}</div>
                    <div className="radio-option-subtitle">{article.source || 'Unknown source'}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <button
            className="collapsible-toggle mt-sm"
            onClick={() => setLinksOpen(!linksOpen)}
          >
            {linksOpen ? '▾' : '▸'} View article links
          </button>
          {linksOpen && (
            <div className="mt-xs" style={{ paddingLeft: 'var(--space-md)' }}>
              {allNews.map((a, i) => (
                <div key={i} className="mb-xs">
                  <a href={a.url} target="_blank" rel="noreferrer" className="article-link">
                    {a.title}
                  </a>
                  <span className="text-small text-muted"> — {a.source}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Custom Override */}
      <div className="mb-lg">
        <label className="input-label">Or type your own topic</label>
        <input
          className="input"
          type="text"
          placeholder="e.g. 'Focus on the UK Modern Slavery Act enforcement gaps'"
          value={customTopic}
          onChange={(e) => setCustomTopic(e.target.value)}
          disabled={loading}
        />
        <p className="input-help">Takes priority over radio selection if filled</p>
      </div>

      {/* Creative Guidance */}
      <div className="mb-lg">
        <label className="input-label">Creative guidance for content generation (optional)</label>
        <textarea
          className="textarea"
          placeholder="e.g. 'Focus on the victim's perspective', 'Emphasize legal consequences for businesses', 'Use a hopeful tone rather than alarming'"
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
          disabled={loading}
          rows={3}
        />
        <p className="input-help">
          This guidance will influence audience targeting, text writing, and image generation
        </p>
      </div>

      {/* Actions */}
      <div className="btn-row">
        <button
          className="btn btn-primary"
          onClick={handleApprove}
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Approve & Continue'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleResearch}
          disabled={loading}
        >
          Re-search
        </button>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { ChevronDown, ChevronRight, Check, RefreshCw, ExternalLink, Newspaper } from 'lucide-react'
import { approveTrend } from '../api'
import PageHeader from '../components/PageHeader'
import DecisionHero from '../components/DecisionHero'

export default function TrendReview({ state, sessionId, onUpdate, recordInput }) {
  const [selectedOption, setSelectedOption] = useState('ai')
  const [customTopic, setCustomTopic] = useState('')
  const [guidance, setGuidance] = useState('')
  const [loading, setLoading] = useState(false)
  const [linksOpen, setLinksOpen] = useState(false)

  const allNews = [...(state.all_retrieved_news || [])]
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))

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
      if (guidance.trim()) payload.guidance = guidance.trim()

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
    <div className="fade-in review-page">
      <PageHeader
        stepKey="topic"
        title="Review the news topic"
        subtitle="Approve the AI pick, choose a different article, or write your own angle."
        icon={Newspaper}
      />

      <DecisionHero
        label="Recommended topic"
        title={state.trend_topic || 'N/A'}
        description={state.trend_context || ''}
      />

      {allNews.length > 0 && (
        <section className="review-section">
          <h3 className="review-section-title">
            <span className="review-section-num">1</span>
            Pick a source article
            <span className="review-section-sub">{allNews.length} options</span>
          </h3>

          <div className="radio-card-list">
            <label
              className={`radio-card ${selectedOption === 'ai' ? 'selected' : ''}`}
              onClick={() => setSelectedOption('ai')}
            >
              <input
                type="radio"
                name="article"
                checked={selectedOption === 'ai'}
                onChange={() => setSelectedOption('ai')}
              />
              <span className="radio-card-indicator">
                {selectedOption === 'ai' && <Check size={12} strokeWidth={3} />}
              </span>
              <div className="radio-card-body">
                <div className="radio-card-title">
                  Use AI Recommendation
                  <span className="radio-card-chip">Default</span>
                </div>
                <div className="radio-card-subtitle">Keep the topic above</div>
              </div>
            </label>

            {allNews.map((article, i) => {
              const isSel = selectedOption === article.title
              const scorePct = typeof article.score === 'number' ? Math.round(article.score * 100) : null
              return (
                <label
                  key={i}
                  className={`radio-card ${isSel ? 'selected' : ''}`}
                  onClick={() => setSelectedOption(article.title)}
                >
                  <input
                    type="radio"
                    name="article"
                    checked={isSel}
                    onChange={() => setSelectedOption(article.title)}
                  />
                  <span className="radio-card-indicator">
                    {isSel && <Check size={12} strokeWidth={3} />}
                  </span>
                  <div className="radio-card-body">
                    <div className="radio-card-title">{article.title || 'Untitled'}</div>
                    <div className="radio-card-subtitle">
                      {article.source || 'Unknown source'}
                      {scorePct !== null && (
                        <span className="radio-card-score" title="Relevance">
                          <span className="radio-card-score-bar">
                            <span
                              className="radio-card-score-fill"
                              style={{ width: `${Math.min(100, scorePct)}%` }}
                            />
                          </span>
                          {scorePct}%
                        </span>
                      )}
                    </div>
                  </div>
                </label>
              )
            })}
          </div>

          <button
            className="collapsible-toggle mt-sm"
            onClick={() => setLinksOpen(!linksOpen)}
          >
            {linksOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            View all article links
          </button>
          {linksOpen && (
            <div className="link-list">
              {allNews.map((a, i) => (
                <a key={i} href={a.url} target="_blank" rel="noreferrer" className="link-list-item">
                  <ExternalLink size={12} strokeWidth={2} />
                  <span className="link-list-title">{a.title}</span>
                  <span className="link-list-source">{a.source}</span>
                </a>
              ))}
            </div>
          )}
        </section>
      )}

      <section className="review-section">
        <h3 className="review-section-title">
          <span className="review-section-num">2</span>
          Or type your own topic
        </h3>
        <input
          className="input"
          type="text"
          placeholder="e.g. 'Focus on the UK Modern Slavery Act enforcement gaps'"
          value={customTopic}
          onChange={(e) => setCustomTopic(e.target.value)}
          disabled={loading}
        />
        <p className="input-help">Takes priority over article selection if filled</p>
      </section>

      <section className="review-section">
        <h3 className="review-section-title">
          <span className="review-section-num">3</span>
          Creative guidance
          <span className="review-section-sub">Optional</span>
        </h3>
        <textarea
          className="textarea"
          placeholder="e.g. 'Focus on the victim's perspective', 'Use a hopeful tone', 'Emphasize legal consequences'"
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
          disabled={loading}
          rows={3}
        />
        <p className="input-help">Flows into audience targeting, copy, and image generation</p>
      </section>

      <div className="review-actions">
        <button
          className="btn btn-primary btn-lg-elevated"
          onClick={handleApprove}
          disabled={loading}
        >
          {loading ? 'Processing…' : 'Approve & Continue'}
          {!loading && <ChevronRight size={16} strokeWidth={2.4} />}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleResearch}
          disabled={loading}
        >
          <RefreshCw size={14} strokeWidth={2} />
          Re-search
        </button>
      </div>
    </div>
  )
}

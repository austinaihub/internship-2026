import { useState } from 'react'
import { refineCampaign, getImageUrl } from '../api'

const REFINE_OPTIONS = [
  { value: 'text_only', label: 'Text only', desc: 'Rewrite the post' },
  { value: 'image_only', label: 'Image only', desc: 'Regenerate the visual' },
  { value: 'both', label: 'Both', desc: 'Rewrite text & image' },
  { value: 'audience', label: 'Audience', desc: 'Change targeting' },
]

export default function DonePage({ state, sessionId, onUpdate, onNewCampaign }) {
  const [refineTarget, setRefineTarget] = useState('text_only')
  const [feedback, setFeedback] = useState('')
  const [loading, setLoading] = useState(false)

  const imageUrl = getImageUrl(state.image_path)

  const handleRefine = async () => {
    if (!feedback.trim()) {
      alert('Please describe what you want changed.')
      return
    }
    setLoading(true)
    try {
      const data = await refineCampaign(sessionId, {
        target: refineTarget,
        feedback: feedback.trim(),
      })
      onUpdate(data.state, data.session_id)
    } catch (err) {
      alert(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="fade-in">

      {/* Result Display */}
      <div className="card mb-lg">
        <h3 className="section-title" style={{ marginBottom: 'var(--space-md)' }}>
          Final Social Media Post
        </h3>
        <div className="result-grid">
          <div>
            {imageUrl && (
              <div className="image-preview">
                <img src={imageUrl} alt="Campaign visual" />
              </div>
            )}
          </div>
          <div style={{ whiteSpace: 'pre-wrap', fontSize: 'var(--font-size-caption)' }}>
            {state.post_text || 'No text available'}
          </div>
        </div>
      </div>

      {/* Refinement Panel */}
      <hr className="divider" />
      <h3 className="section-title">Refine This Campaign</h3>
      <p className="caption mb-md">
        Not satisfied? Choose what to improve — the system will only re-run the necessary agents.
      </p>

      {/* Refine Target Radio */}
      <div className="radio-group-horizontal mb-lg">
        {REFINE_OPTIONS.map((opt) => (
          <label
            key={opt.value}
            className={`radio-option ${refineTarget === opt.value ? 'selected' : ''}`}
            onClick={() => setRefineTarget(opt.value)}
          >
            <input
              type="radio"
              name="refine"
              checked={refineTarget === opt.value}
              onChange={() => setRefineTarget(opt.value)}
            />
            <div className="radio-option-label">{opt.label}</div>
            <div className="radio-option-subtitle">{opt.desc}</div>
          </label>
        ))}
      </div>

      {/* Feedback */}
      <div className="mb-lg">
        <label className="input-label">Describe what you want changed</label>
        <textarea
          className="textarea"
          placeholder="e.g. 'Make the tone more urgent', 'Use warmer colors', 'Target educators instead'"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          disabled={loading}
        />
      </div>

      {/* Actions */}
      <div className="btn-row">
        <button
          className="btn btn-primary"
          onClick={handleRefine}
          disabled={loading}
        >
          {loading ? 'Refining...' : 'Apply Refinement'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={onNewCampaign}
          disabled={loading}
        >
          New Campaign
        </button>
      </div>
    </div>
  )
}

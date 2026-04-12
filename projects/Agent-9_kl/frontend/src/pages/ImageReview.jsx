import { useState } from 'react'
import { approveImage, getImageUrl } from '../api'

export default function ImageReview({ state, sessionId, onUpdate, recordInput }) {
  const [feedback, setFeedback] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingAction, setLoadingAction] = useState(null)

  const imageUrl = getImageUrl(state.image_path)

  const handleAction = async (action) => {
    setLoading(true)
    setLoadingAction(action)
    try {
      const data = await approveImage(sessionId, {
        action,
        feedback: feedback.trim(),
      })
      recordInput({
        step: 'image_review',
        action,
        feedback: feedback.trim() || null,
      })
      onUpdate(data.state)
    } catch (err) {
      alert(err.message)
      setLoading(false)
      setLoadingAction(null)
    }
  }

  const btnLabel = (action, label) => {
    if (loadingAction === action) return 'Processing...'
    return label
  }

  return (
    <div className="fade-in">

      {/* Content Preview: Image + Text side by side */}
      <div className="card mb-lg">
        <h3 className="section-title" style={{ marginBottom: 'var(--space-md)' }}>
          Generated Content Preview
        </h3>
        <div className="result-grid">
          <div>
            {imageUrl && (
              <div className="image-preview">
                <img src={imageUrl} alt="Generated campaign visual" />
              </div>
            )}
          </div>
          <div style={{ whiteSpace: 'pre-wrap', fontSize: 'var(--font-size-caption)', color: 'var(--text-secondary)' }}>
            {state.post_text || 'No text available'}
          </div>
        </div>
      </div>

      {/* Feedback Input */}
      <div className="mb-lg">
        <label className="input-label">Feedback for regeneration (optional)</label>
        <textarea
          className="textarea"
          placeholder="e.g. 'Use warmer colors', 'Make the tone more urgent', 'Focus on the survivor's strength'"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          disabled={loading}
          rows={3}
        />
      </div>

      {/* Actions — 3 buttons */}
      <div className="btn-row">
        <button
          className="btn btn-primary"
          onClick={() => handleAction('approve')}
          disabled={loading}
        >
          {btnLabel('approve', 'Approve & Publish')}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => handleAction('regen_image')}
          disabled={loading}
        >
          {btnLabel('regen_image', 'Regenerate Image')}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => handleAction('regen_text_and_image')}
          disabled={loading}
        >
          {btnLabel('regen_text_and_image', 'Regenerate All')}
        </button>
      </div>
    </div>
  )
}

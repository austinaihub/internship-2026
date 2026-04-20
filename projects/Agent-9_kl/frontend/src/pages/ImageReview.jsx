import { useState } from 'react'
import { Download, Image as ImageIcon, RefreshCw, CheckCircle2, Layers } from 'lucide-react'
import { approveImage, getImageUrl } from '../api'
import PageHeader from '../components/PageHeader'

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
    } finally {
      setLoading(false)
      setLoadingAction(null)
    }
  }

  const handleDownload = async () => {
    const res = await fetch(imageUrl)
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = imageUrl.split('/').pop() || 'campaign-image.png'
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const isLoading = (action) => loadingAction === action

  return (
    <div className="fade-in review-page">
      <PageHeader
        stepKey="visual"
        title="Review the generated content"
        subtitle="Approve to publish, or regenerate with your feedback."
        icon={ImageIcon}
      />

      <div className="preview-stage">
        <div className="preview-stage-image">
          {imageUrl ? (
            <>
              <img src={imageUrl} alt="Generated campaign visual" />
              <button
                className="btn-image-download"
                onClick={handleDownload}
                title="Save image"
              >
                <Download size={14} strokeWidth={2} />
                Save
              </button>
            </>
          ) : (
            <div className="preview-stage-placeholder">No image generated</div>
          )}
        </div>
        <div className="preview-stage-text">
          <div className="preview-stage-kicker">
            <Layers size={12} strokeWidth={2} />
            Post copy
          </div>
          <div className="preview-stage-body">
            {state.post_text || 'No text available'}
          </div>
        </div>
      </div>

      <section className="review-section">
        <h3 className="review-section-title">
          <span className="review-section-num">1</span>
          Feedback for regeneration
          <span className="review-section-sub">Optional</span>
        </h3>
        <textarea
          className="textarea"
          placeholder="e.g. 'Use warmer colors', 'Make the tone more urgent', 'Focus on the survivor's strength'"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          disabled={loading}
          rows={3}
        />
      </section>

      <div className="review-actions review-actions-stack">
        <button
          className="btn btn-primary btn-lg-elevated"
          onClick={() => handleAction('approve')}
          disabled={loading}
        >
          {isLoading('approve') ? 'Publishing…' : (
            <>
              <CheckCircle2 size={16} strokeWidth={2.2} />
              Approve & Publish
            </>
          )}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => handleAction('regen_image')}
          disabled={loading}
        >
          <RefreshCw size={14} strokeWidth={2} />
          {isLoading('regen_image') ? 'Regenerating…' : 'Regenerate Image'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => handleAction('regen_text_and_image')}
          disabled={loading}
        >
          <RefreshCw size={14} strokeWidth={2} />
          {isLoading('regen_text_and_image') ? 'Regenerating…' : 'Regenerate All'}
        </button>
      </div>
    </div>
  )
}

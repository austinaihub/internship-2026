import { useState } from 'react'
import { CheckCircle2, Download, Layers, Sparkles, Plus, ChevronRight } from 'lucide-react'
import { refineCampaign, getImageUrl } from '../api'
import PageHeader from '../components/PageHeader'

const REFINE_OPTIONS = [
  { value: 'text_only', label: 'Text only', desc: 'Rewrite the post' },
  { value: 'image_only', label: 'Image only', desc: 'Regenerate the visual' },
  { value: 'both', label: 'Both', desc: 'Rewrite text & image' },
  { value: 'audience', label: 'Audience', desc: 'Change targeting' },
]

export default function DonePage({ state, sessionId, onUpdate, onNewCampaign, recordInput }) {
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
      recordInput({
        step: 'done_refine',
        action: 'refine',
        refineTarget,
        feedback: feedback.trim() || null,
      })
      onUpdate(data.state, data.session_id)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
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

  return (
    <div className="fade-in review-page">
      <div className="done-celebration">
        <span className="done-celebration-dot" />
        Campaign published
      </div>

      <PageHeader
        stepKey="done"
        title="Your campaign is ready"
        subtitle="Download the final asset, share the post, or refine it below."
        icon={CheckCircle2}
      />

      <div className="preview-stage">
        <div className="preview-stage-image">
          {imageUrl ? (
            <>
              <img src={imageUrl} alt="Final campaign visual" />
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
            <div className="preview-stage-placeholder">No image available</div>
          )}
        </div>
        <div className="preview-stage-text">
          <div className="preview-stage-kicker">
            <Layers size={12} strokeWidth={2} />
            Final post copy
          </div>
          <div className="preview-stage-body">
            {state.post_text || 'No text available'}
          </div>
        </div>
      </div>

      <section className="review-section">
        <h3 className="review-section-title">
          <span className="review-section-num">
            <Sparkles size={11} strokeWidth={2.4} />
          </span>
          Refine this campaign
          <span className="review-section-sub">Optional</span>
        </h3>
        <p className="input-help" style={{ marginTop: '-4px' }}>
          Choose what to improve — the system only re-runs the necessary agents.
        </p>

        <div className="refine-option-grid mt-sm">
          {REFINE_OPTIONS.map((opt) => {
            const isSel = refineTarget === opt.value
            return (
              <label
                key={opt.value}
                className={`refine-option ${isSel ? 'selected' : ''}`}
                onClick={() => setRefineTarget(opt.value)}
              >
                <input
                  type="radio"
                  name="refine"
                  checked={isSel}
                  onChange={() => setRefineTarget(opt.value)}
                />
                <div className="refine-option-label">{opt.label}</div>
                <div className="refine-option-desc">{opt.desc}</div>
              </label>
            )
          })}
        </div>

        <textarea
          className="textarea mt-sm"
          placeholder="e.g. 'Make the tone more urgent', 'Use warmer colors', 'Target educators instead'"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          disabled={loading}
          rows={3}
        />
      </section>

      <div className="review-actions">
        <button
          className="btn btn-primary btn-lg-elevated"
          onClick={handleRefine}
          disabled={loading}
        >
          {loading ? 'Refining…' : (
            <>
              Apply Refinement
              <ChevronRight size={16} strokeWidth={2.4} />
            </>
          )}
        </button>
        <button
          className="btn btn-secondary"
          onClick={onNewCampaign}
          disabled={loading}
        >
          <Plus size={14} strokeWidth={2.2} />
          New Campaign
        </button>
      </div>
    </div>
  )
}

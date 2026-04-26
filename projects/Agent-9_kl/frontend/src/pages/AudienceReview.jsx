import { useState } from 'react'
import { ChevronRight, Edit3, X, Users, Check } from 'lucide-react'
import { approveAudience } from '../api'
import PageHeader from '../components/PageHeader'
import DecisionHero from '../components/DecisionHero'

const STYLE_PRESETS = [
  {
    value: 'rembrandt',
    label: 'Rembrandt Studio',
    desc: 'Dark studio backdrop, dramatic 45° key light, sculptural shadows',
    mood: 'Classical, dramatic',
    image: '/style-demos/rembrandt.png',
  },
  {
    value: 'editorial_flat',
    label: 'Editorial Flat',
    desc: 'Overhead angle, solid-color surface, shadowless diffused light',
    mood: 'Clean, graphic, modern',
    image: '/style-demos/editorial_flat.png',
  },
  {
    value: 'fog_silence',
    label: 'Fog & Silence',
    desc: 'Mist-filled frame, tiny distant subject, near-monochrome',
    mood: 'Poetic, ethereal',
    image: '/style-demos/fog_silence.png',
  },
  {
    value: 'cinematic_depth',
    label: 'Cinematic Depth',
    desc: 'Shallow DOF, bokeh background, dramatic chiaroscuro',
    mood: 'Magazine-cover intensity',
    image: '/style-demos/cinematic_depth.png',
  },
]

export default function AudienceReview({ state, sessionId, onUpdate, recordInput }) {
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(false)

  const [targetAudience, setTargetAudience] = useState(state.target_audience || '')
  const [audienceBrief, setAudienceBrief] = useState(state.audience_brief || '')
  const [visualStylePreset, setVisualStylePreset] = useState(state.visual_style_preset || 'cinematic_depth')
  const [visualStyle, setVisualStyle] = useState(state.visual_style || '')
  const [visualElements, setVisualElements] = useState(state.visual_elements || '')
  const [guidance, setGuidance] = useState('')

  const handleApprove = async () => {
    setLoading(true)
    try {
      const payload = { action: 'approve', visualStylePreset }
      if (guidance.trim()) payload.guidance = guidance.trim()
      const data = await approveAudience(sessionId, payload)
      recordInput({
        step: 'audience_review',
        action: 'approve',
        stylePreset: visualStylePreset,
        guidance: guidance.trim() || null,
      })
      onUpdate(data.state)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = async () => {
    setLoading(true)
    try {
      const payload = {
        action: 'edit',
        targetAudience: targetAudience.trim(),
        audienceBrief: audienceBrief.trim(),
        visualStylePreset,
        visualStyle: visualStyle.trim(),
        visualElements: visualElements.trim(),
      }
      if (guidance.trim()) payload.guidance = guidance.trim()
      const data = await approveAudience(sessionId, payload)
      recordInput({
        step: 'audience_review',
        action: 'edit',
        targetAudience: targetAudience.trim(),
        stylePreset: visualStylePreset,
        guidance: guidance.trim() || null,
      })
      onUpdate(data.state)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const recommendedPreset = state.visual_style_preset || 'cinematic_depth'
  const audienceLabel = (state.target_audience || 'N/A').replace(/_/g, ' ')

  return (
    <div className="fade-in review-page">
      <PageHeader
        stepKey="audience"
        title="Review the audience strategy"
        subtitle="Confirm who this campaign targets and how the visual should feel."
        icon={Users}
      />

      <DecisionHero
        label="Target audience"
        title={<span className="decision-hero-tag">{audienceLabel}</span>}
        description={state.audience_brief || null}
      />

      <section className="review-section">
        <h3 className="review-section-title">
          <span className="review-section-num">1</span>
          Photography style
          <span className="review-section-sub">
            AI suggested: <strong>{recommendedPreset.replace(/_/g, ' ')}</strong>
          </span>
        </h3>
        <div className="preset-grid">
          {STYLE_PRESETS.map((preset) => {
            const isSel = visualStylePreset === preset.value
            return (
              <label
                key={preset.value}
                className={`preset-card ${isSel ? 'selected' : ''}`}
                onClick={() => setVisualStylePreset(preset.value)}
              >
                <input
                  type="radio"
                  name="stylePreset"
                  checked={isSel}
                  onChange={() => setVisualStylePreset(preset.value)}
                />
                <div className="preset-swatch">
                  <img
                    src={preset.image}
                    alt={preset.label}
                    className="preset-swatch-img"
                    loading="lazy"
                  />
                  {isSel && (
                    <span className="preset-swatch-check">
                      <Check size={14} strokeWidth={3} />
                    </span>
                  )}
                </div>
                <div className="preset-body">
                  <div className="preset-name">{preset.label}</div>
                  <div className="preset-desc">{preset.desc}</div>
                  <div className="preset-mood">{preset.mood}</div>
                </div>
              </label>
            )
          })}
        </div>
      </section>

      <section className="review-section">
        <h3 className="review-section-title">
          <span className="review-section-num">2</span>
          Audience brief
          {!editing && (
            <button className="review-section-edit" onClick={() => setEditing(true)}>
              <Edit3 size={12} strokeWidth={2} /> Edit fields
            </button>
          )}
          {editing && (
            <button className="review-section-edit" onClick={() => setEditing(false)}>
              <X size={12} strokeWidth={2} /> Cancel
            </button>
          )}
        </h3>

        <div className="detail-fields">
          <Field
            label="Target Audience"
            value={state.target_audience}
            editing={editing}
            editValue={targetAudience}
            onEdit={setTargetAudience}
            placeholder="e.g. college_students, educators"
            loading={loading}
          />
          <Field
            label="Audience Brief"
            value={state.audience_brief}
            editing={editing}
            editValue={audienceBrief}
            onEdit={setAudienceBrief}
            multiline
            rows={3}
            loading={loading}
          />
          <Field
            label="Visual Style"
            value={state.visual_style}
            editing={editing}
            editValue={visualStyle}
            onEdit={setVisualStyle}
            multiline
            rows={2}
            loading={loading}
          />
          <Field
            label="Visual Elements"
            value={state.visual_elements}
            editing={editing}
            editValue={visualElements}
            onEdit={setVisualElements}
            multiline
            rows={2}
            loading={loading}
          />
        </div>
      </section>

      <section className="review-section">
        <h3 className="review-section-title">
          <span className="review-section-num">3</span>
          Additional guidance
          <span className="review-section-sub">Optional</span>
        </h3>
        <textarea
          className="textarea"
          placeholder="e.g. 'Focus on hope rather than fear', 'Emphasize legal action'"
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
          disabled={loading}
          rows={2}
        />
        <p className="input-help">Flows into copy and image generation</p>
      </section>

      <div className="review-actions">
        <button
          className="btn btn-primary btn-lg-elevated"
          onClick={editing ? handleEdit : handleApprove}
          disabled={loading}
        >
          {loading ? 'Processing…' : editing ? 'Save & Continue' : 'Approve & Continue'}
          {!loading && <ChevronRight size={16} strokeWidth={2.4} />}
        </button>
      </div>
    </div>
  )
}

function Field({ label, value, editing, editValue, onEdit, multiline, rows, placeholder, loading }) {
  return (
    <div className="detail-field">
      <label className="detail-field-label">{label}</label>
      {editing ? (
        multiline ? (
          <textarea
            className="textarea"
            value={editValue}
            onChange={(e) => onEdit(e.target.value)}
            disabled={loading}
            rows={rows || 2}
            placeholder={placeholder}
          />
        ) : (
          <input
            className="input"
            value={editValue}
            onChange={(e) => onEdit(e.target.value)}
            disabled={loading}
            placeholder={placeholder}
          />
        )
      ) : (
        <p className="detail-field-value">{value || 'N/A'}</p>
      )}
    </div>
  )
}

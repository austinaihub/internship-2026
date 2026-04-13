import { useState } from 'react'
import { approveAudience } from '../api'

const STYLE_PRESETS = [
  {
    value: 'rembrandt',
    label: 'Rembrandt Studio',
    desc: 'Dark studio backdrop, dramatic 45° key light, sculptural shadows',
    mood: 'Classical, dramatic',
  },
  {
    value: 'editorial_flat',
    label: 'Editorial Flat',
    desc: 'Overhead angle, solid-color surface, shadowless diffused light',
    mood: 'Clean, graphic, modern',
  },
  {
    value: 'fog_silence',
    label: 'Fog & Silence',
    desc: 'Mist-filled frame, tiny distant subject, near-monochrome',
    mood: 'Poetic, ethereal',
  },
  {
    value: 'cinematic_depth',
    label: 'Cinematic Depth',
    desc: 'Shallow DOF, bokeh background, dramatic chiaroscuro',
    mood: 'Magazine-cover intensity',
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
      const payload = { action: 'approve' }
      // Always send the selected preset (user may have changed it without editing other fields)
      payload.visualStylePreset = visualStylePreset
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

  return (
    <div className="fade-in">

      {/* AI Decision Summary */}
      <div className="card mb-lg">
        <p className="caption mb-xs">AI Selected Audience</p>
        <div className="audience-tag mb-sm">{state.target_audience || 'N/A'}</div>
      </div>

      {/* Visual Style Preset Selector — always visible */}
      <div className="mb-lg">
        <label className="input-label">Photography Style</label>
        <div className="style-preset-grid">
          {STYLE_PRESETS.map((preset) => (
            <label
              key={preset.value}
              className={`style-preset-card ${visualStylePreset === preset.value ? 'selected' : ''}`}
              onClick={() => setVisualStylePreset(preset.value)}
            >
              <input
                type="radio"
                name="stylePreset"
                checked={visualStylePreset === preset.value}
                onChange={() => setVisualStylePreset(preset.value)}
              />
              <div className="style-preset-content">
                <div className="style-preset-name">{preset.label}</div>
                <div className="style-preset-desc">{preset.desc}</div>
                <div className="style-preset-mood">{preset.mood}</div>
              </div>
            </label>
          ))}
        </div>
        <p className="input-help">
          AI recommended: <strong>{state.visual_style_preset || 'cinematic_depth'}</strong> — you can override
        </p>
      </div>

      {/* Audience Fields — read-only or editable */}
      <div className="audience-fields mb-lg">

        <div className="audience-field">
          <label className="input-label">Target Audience</label>
          {editing ? (
            <input
              className="input"
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              disabled={loading}
              placeholder="e.g. college_students, educators, business_owners"
            />
          ) : (
            <p className="audience-value">{state.target_audience || 'N/A'}</p>
          )}
        </div>

        <div className="audience-field">
          <label className="input-label">Audience Brief</label>
          {editing ? (
            <textarea
              className="textarea"
              value={audienceBrief}
              onChange={(e) => setAudienceBrief(e.target.value)}
              disabled={loading}
              rows={3}
            />
          ) : (
            <p className="audience-value">{state.audience_brief || 'N/A'}</p>
          )}
        </div>

        <div className="audience-field">
          <label className="input-label">Visual Style (color/mood)</label>
          {editing ? (
            <textarea
              className="textarea"
              value={visualStyle}
              onChange={(e) => setVisualStyle(e.target.value)}
              disabled={loading}
              rows={2}
            />
          ) : (
            <p className="audience-value">{state.visual_style || 'N/A'}</p>
          )}
        </div>

        <div className="audience-field">
          <label className="input-label">Visual Elements</label>
          {editing ? (
            <textarea
              className="textarea"
              value={visualElements}
              onChange={(e) => setVisualElements(e.target.value)}
              disabled={loading}
              rows={2}
            />
          ) : (
            <p className="audience-value">{state.visual_elements || 'N/A'}</p>
          )}
        </div>
      </div>

      {/* Creative Guidance (always visible) */}
      <div className="mb-lg">
        <label className="input-label">Additional creative guidance (optional)</label>
        <textarea
          className="textarea"
          placeholder="e.g. 'Focus on hope rather than fear', 'Emphasize legal action'"
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
          disabled={loading}
          rows={2}
        />
        <p className="input-help">
          This guidance will influence text writing and image generation
        </p>
      </div>

      {/* Actions */}
      <div className="btn-row">
        <button
          className="btn btn-primary"
          onClick={editing ? handleEdit : handleApprove}
          disabled={loading}
        >
          {loading ? 'Processing...' : editing ? 'Save & Continue' : 'Approve & Continue'}
        </button>
        {!editing && (
          <button
            className="btn btn-secondary"
            onClick={() => setEditing(true)}
            disabled={loading}
          >
            Edit Fields
          </button>
        )}
        {editing && (
          <button
            className="btn btn-secondary"
            onClick={() => setEditing(false)}
            disabled={loading}
          >
            Cancel Edit
          </button>
        )}
      </div>
    </div>
  )
}

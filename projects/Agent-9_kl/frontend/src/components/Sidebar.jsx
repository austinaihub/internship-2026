// ── Status Badge (extracted from old Header.jsx) ────────────────────────────
function StatusBadge({ status }) {
  const config = {
    approving_trend: { label: 'Reviewing Topic', className: 'badge-yellow' },
    approving_image: { label: 'Reviewing Content', className: 'badge-yellow' },
    approved_trend: { label: 'Processing', className: 'badge-blue' },
    approved_text: { label: 'Processing', className: 'badge-blue' },
    audience_approved: { label: 'Processing', className: 'badge-blue' },
    audience_selected: { label: 'Processing', className: 'badge-blue' },
    done: { label: 'Published', className: 'badge-green' },
    error: { label: 'Error', className: 'badge-red' },
  }

  const { label, className } = config[status] || { label: 'Processing', className: 'badge-blue' }

  return <span className={`badge ${className}`}>{label}</span>
}

// ── Step Definitions ────────────────────────────────────────────────────────
const STEPS = [
  { key: 'setup',   label: 'Campaign Setup' },
  { key: 'topic',   label: 'News Topic' },
  { key: 'content', label: 'Content Generation' },
  { key: 'review',  label: 'Content Review' },
  { key: 'done',    label: 'Published' },
]

function getStepMode(stepKey, status, state) {
  if (!status) return 'idle'

  switch (stepKey) {
    case 'setup':
      return 'completed'

    case 'topic':
      if (status === 'approving_trend') return 'active'
      if (state?.trend_topic && status !== 'approving_trend') return 'completed'
      return 'loading'

    case 'content': {
      const trendDone = state?.trend_topic && status !== 'approving_trend'
      if (!trendDone) return 'idle'
      if (['approving_image', 'done'].includes(status)) return 'completed'
      if (status === 'error') return 'idle'
      return 'loading'
    }

    case 'review':
      if (status === 'approving_image') return 'active'
      if (status === 'done') return 'completed'
      return 'idle'

    case 'done':
      if (status === 'done') return 'active'
      return 'idle'

    default:
      return 'idle'
  }
}

function getStepSummary(stepKey, state) {
  if (!state) return null

  switch (stepKey) {
    case 'setup':
      return state.user_search_keywords
        ? `"${state.user_search_keywords}"`
        : 'Auto discovery'
    case 'topic':
      return state.trend_topic || null
    case 'content':
      return state.target_audience
        ? `Audience: ${state.target_audience}`
        : null
    case 'review':
      return null
    case 'done':
      return null
    default:
      return null
  }
}

// ── Sidebar Component ───────────────────────────────────────────────────────
export default function Sidebar({ state, status }) {
  return (
    <aside className="sidebar">
      {/* Logo + Badge */}
      <div className="sidebar-header">
        <div className="header-logo">
          Agent-9 <span>Campaign</span>
        </div>
        {status && <StatusBadge status={status} />}
      </div>

      <hr className="divider" />

      {/* Stepper */}
      <nav className="sidebar-stepper">
        {STEPS.map((step) => {
          const mode = getStepMode(step.key, status, state)
          const summary = mode === 'completed' || mode === 'active'
            ? getStepSummary(step.key, state)
            : null

          const modeClass = {
            completed: 'step-completed',
            active: 'step-active',
            loading: 'step-loading',
            idle: 'step-idle',
          }[mode] || 'step-idle'

          const dotLabel = mode === 'completed'
            ? '✓'
            : mode === 'loading'
            ? '⋯'
            : STEPS.indexOf(step) + 1

          return (
            <div key={step.key} className={`sidebar-step ${modeClass}`}>
              <div className="sidebar-step-dot">{dotLabel}</div>
              <div className="sidebar-step-info">
                <div className="sidebar-step-label">{step.label}</div>
                {summary && (
                  <div className="sidebar-step-summary">{summary}</div>
                )}
              </div>
            </div>
          )
        })}
      </nav>

      <hr className="divider" />

      {/* Metadata */}
      <div className="sidebar-meta">
        {state?.user_search_keywords && (
          <div className="sidebar-meta-item">
            <span className="sidebar-meta-label">Keywords</span>
            <span className="meta-tag">{state.user_search_keywords}</span>
          </div>
        )}

        {state?.trend_topic && (
          <div className="sidebar-meta-item">
            <span className="sidebar-meta-label">Topic</span>
            <span className="sidebar-meta-value">{state.trend_topic}</span>
          </div>
        )}

        {state?.target_audience && (
          <div className="sidebar-meta-item">
            <span className="sidebar-meta-label">Audience</span>
            <span className="meta-tag">{state.target_audience.replace(/_/g, ' ')}</span>
          </div>
        )}

        {state?.user_guidance && (
          <div className="sidebar-meta-item">
            <span className="sidebar-meta-label">Guidance</span>
            <span className="sidebar-meta-value">{state.user_guidance}</span>
          </div>
        )}

        {!state?.trend_topic && !state?.user_search_keywords && (
          <p className="caption" style={{ textAlign: 'center' }}>
            Campaign info will appear here
          </p>
        )}
      </div>
    </aside>
  )
}

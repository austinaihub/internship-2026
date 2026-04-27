export const WORKFLOW_STEPS = [
  { key: 'start',    label: 'Start' },
  { key: 'setup',    label: 'Campaign Setup' },
  { key: 'topic',    label: 'News Topic' },
  { key: 'audience', label: 'Audience Strategy' },
  { key: 'writing',  label: 'Content Writing' },
  { key: 'visual',   label: 'Visual Generation' },
  { key: 'done',     label: 'Published' },
]

export function getStepMode(stepKey, status, state) {
  if (status === 'pre_start' || !status) {
    if (stepKey === 'start') return status === 'pre_start' ? 'active' : 'idle'
    return 'idle'
  }

  switch (stepKey) {
    case 'start':
      return 'completed'

    case 'setup':
      return 'completed'

    case 'topic':
      if (status === 'approving_trend') return 'active'
      if (state?.trend_topic && status !== 'approving_trend') return 'completed'
      return 'loading'

    case 'audience': {
      const trendDone = state?.trend_topic && !['approving_trend', 'starting'].includes(status)
      if (!trendDone) return 'idle'
      if (status === 'approved_trend') return 'loading'
      if (status === 'approving_audience') return 'active'
      if (state?.target_audience) return 'completed'
      return 'idle'
    }

    case 'writing': {
      if (!state?.target_audience) return 'idle'
      if (['approving_audience', 'approved_trend', 'starting', 'approving_trend'].includes(status)) return 'idle'
      if (status === 'audience_approved') return 'loading'
      if (state?.post_text && state.post_text !== 'REJECTED') return 'completed'
      return 'idle'
    }

    case 'visual': {
      if (!state?.post_text || state.post_text === 'REJECTED') return 'idle'
      if (status === 'approved_text') return 'loading'
      if (status === 'approving_image') return 'active'
      if (status === 'done') return 'completed'
      return 'idle'
    }

    case 'done':
      if (status === 'done') return 'active'
      return 'idle'

    default:
      return 'idle'
  }
}

export function getStepSummary(stepKey, state) {
  if (!state) return null

  switch (stepKey) {
    case 'setup':
      return state.user_search_keywords
        ? `"${state.user_search_keywords}"`
        : 'Auto discovery'
    case 'topic':
      return state.trend_topic || null
    case 'audience':
      return state.target_audience
        ? state.target_audience.replace(/_/g, ' ')
        : null
    case 'writing':
      return state.post_text && state.post_text !== 'REJECTED'
        ? `${state.post_text.substring(0, 40)}...`
        : null
    default:
      return null
  }
}

// variant: 'sidebar' (vertical, with summary) | 'horizontal' (compact, framed, sticky-footer friendly)
export default function WorkflowStepper({ state, status, variant = 'sidebar' }) {
  if (variant === 'horizontal') {
    return (
      <nav className="workflow-horizontal" aria-label="Campaign workflow progress">
        {WORKFLOW_STEPS.map((step, idx) => {
          const mode = getStepMode(step.key, status, state)
          const modeClass = `wh-step-${mode}`
          const dotLabel = mode === 'completed' ? '✓' : mode === 'loading' ? '⋯' : idx + 1
          return (
            <div key={step.key} className={`wh-step ${modeClass}`}>
              <div className="wh-step-frame">
                <span className="wh-step-dot">{dotLabel}</span>
                <span className="wh-step-label">{step.label}</span>
              </div>
              {idx < WORKFLOW_STEPS.length - 1 && (
                <span className={`wh-connector ${mode === 'completed' ? 'wh-connector-done' : ''}`} />
              )}
            </div>
          )
        })}
      </nav>
    )
  }

  // Default: sidebar (vertical)
  return (
    <nav className="sidebar-stepper">
      {WORKFLOW_STEPS.map((step) => {
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
          : WORKFLOW_STEPS.indexOf(step) + 1

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
  )
}

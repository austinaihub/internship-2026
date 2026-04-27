import { WORKFLOW_STEPS } from './WorkflowStepper'

// Page header with step chip + title + optional subtitle.
// stepKey: one of WORKFLOW_STEPS keys → shown as "Step N of M · Label" chip.
export default function PageHeader({ stepKey, title, subtitle, icon: Icon, accent = 'blue' }) {
  const idx = WORKFLOW_STEPS.findIndex(s => s.key === stepKey)
  const stepNum = idx >= 0 ? idx + 1 : null
  const stepLabel = idx >= 0 ? WORKFLOW_STEPS[idx].label : null
  const total = WORKFLOW_STEPS.length

  return (
    <header className={`page-header page-header-accent-${accent}`}>
      {stepNum && (
        <div className="page-header-chip">
          <span className="page-header-chip-num">{stepNum}</span>
          <span className="page-header-chip-sep">·</span>
          <span className="page-header-chip-label">{stepLabel}</span>
          <span className="page-header-chip-of">of {total}</span>
        </div>
      )}
      <h1 className="page-header-title">
        {Icon && <Icon className="page-header-icon" size={28} strokeWidth={1.8} />}
        {title}
      </h1>
      {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
    </header>
  )
}

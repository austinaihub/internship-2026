export default function Header({ status }) {
  return (
    <header className="header">
      <div className="header-logo">
        Campaign <span>Agent</span>
      </div>
      {status && <StatusBadge status={status} />}
    </header>
  )
}

function StatusBadge({ status }) {
  const config = {
    approving_trend: { label: 'Reviewing Topic', className: 'badge-yellow' },
    approving_image: { label: 'Reviewing Image', className: 'badge-yellow' },
    approved_trend: { label: 'Processing', className: 'badge-blue' },
    approved_text: { label: 'Processing', className: 'badge-blue' },
    done: { label: 'Published', className: 'badge-green' },
    error: { label: 'Error', className: 'badge-red' },
  }

  const { label, className } = config[status] || { label: 'Processing', className: 'badge-blue' }

  return <span className={`badge ${className}`}>{label}</span>
}

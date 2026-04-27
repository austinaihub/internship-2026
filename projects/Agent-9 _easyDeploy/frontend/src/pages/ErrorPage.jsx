export default function ErrorPage({ state, onNewCampaign }) {
  return (
    <div className="fade-in">
      <div className="alert alert-error mb-lg">
        ⚠️ Workflow encountered an error
      </div>

      <div className="card mb-lg">
        <h3 className="section-title">Error Details</h3>
        <p style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)' }}>
          {state?.feedback || state?.status || 'An unknown error occurred.'}
        </p>
      </div>

      <div className="btn-row">
        <button className="btn btn-primary" onClick={onNewCampaign}>
          🆕 Start New Campaign
        </button>
      </div>
    </div>
  )
}

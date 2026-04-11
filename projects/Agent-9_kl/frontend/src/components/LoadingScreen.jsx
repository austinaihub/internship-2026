export default function LoadingScreen({ status }) {
  const messages = {
    starting: 'Searching for trending news...',
    planning: 'Analyzing trends...',
    approved_trend: 'Analyzing audience & generating content...',
    audience_approved: 'Writing campaign post...',
    approved_text: 'Generating campaign image...',
    generating_image: 'Creating visual with AI...',
    publisher: 'Publishing campaign...',
  }

  const message = messages[status] || 'Agents are working...'

  return (
    <div className="page-center fade-in" style={{ minHeight: '60vh' }}>
      <div className="spinner mb-lg" />
      <p className="page-title mb-sm">{message}</p>
      <p className="caption">This may take 15–30 seconds</p>
    </div>
  )
}

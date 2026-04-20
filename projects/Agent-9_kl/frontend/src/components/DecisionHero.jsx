import { Sparkles } from 'lucide-react'

// The "AI picked" hero card used at the top of review pages.
// label: small kicker like "AI Recommended Topic"
// title: the main decision content (can be any node)
// description: optional paragraph below title
// accent: "blue" (default) | "purple" | "green"
export default function DecisionHero({
  label = 'AI Recommendation',
  title,
  description,
  accent = 'blue',
  children,
}) {
  return (
    <div className={`decision-hero decision-hero-accent-${accent}`}>
      <div className="decision-hero-kicker">
        <span className="decision-hero-badge">
          <Sparkles size={11} strokeWidth={2.4} />
          <span>AI picked</span>
        </span>
        <span className="decision-hero-label">{label}</span>
      </div>
      {title && <h2 className="decision-hero-title">{title}</h2>}
      {description && <p className="decision-hero-description">{description}</p>}
      {children}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Search, Target, Edit3, Image as ImageIcon, Send, Sparkles } from 'lucide-react'

const STATUS_CONFIG = {
  starting: {
    label: 'Searching for trending news',
    icon: Search,
    taglines: [
      'Querying Reuters, AP, BBC, Guardian…',
      'Scanning past 14 days of coverage…',
      'Filtering trafficking-relevant stories…',
      'Ranking results by semantic relevance…',
    ],
  },
  planning: {
    label: 'Analyzing trends',
    icon: Search,
    taglines: [
      'Identifying dominant narratives…',
      'Cross-referencing sources…',
      'Surfacing the strongest storyline…',
    ],
  },
  approved_trend: {
    label: 'Analyzing audience & generating content',
    icon: Target,
    taglines: [
      'Profiling target demographics…',
      'Mapping message resonance…',
      'Selecting channel-appropriate tone…',
    ],
  },
  audience_selected: {
    label: 'Analyzing audience',
    icon: Target,
    taglines: [
      'Refining audience brief…',
      'Aligning with campaign goals…',
    ],
  },
  audience_approved: {
    label: 'Writing campaign post',
    icon: Edit3,
    taglines: [
      'Drafting headline & hook…',
      'Tuning emotional register…',
      'Polishing call-to-action…',
    ],
  },
  approved_text: {
    label: 'Generating campaign image',
    icon: ImageIcon,
    taglines: [
      'Composing visual concept…',
      'Rendering with AI image model…',
      'Applying visual style preset…',
      'Finalizing overlay text…',
    ],
  },
  generating_image: {
    label: 'Creating visual with AI',
    icon: ImageIcon,
    taglines: [
      'Rendering image pixels…',
      'Applying photographic style…',
    ],
  },
  publisher: {
    label: 'Publishing campaign',
    icon: Send,
    taglines: [
      'Packaging final assets…',
      'Writing campaign report…',
    ],
  },
}

const DEFAULT_CONFIG = {
  label: 'Agents are working',
  icon: Sparkles,
  taglines: ['Please wait…'],
}

export default function LoadingScreen({ status }) {
  const config = STATUS_CONFIG[status] || DEFAULT_CONFIG
  const Icon = config.icon || Sparkles
  const [idx, setIdx] = useState(0)

  useEffect(() => {
    setIdx(0)
  }, [status])

  useEffect(() => {
    if (config.taglines.length <= 1) return
    const timer = setInterval(() => {
      setIdx(prev => (prev + 1) % config.taglines.length)
    }, 2800)
    return () => clearInterval(timer)
  }, [config.taglines.length])

  const tagline = config.taglines[idx] || ''

  return (
    <div className="loader-stage fade-in">
      <div className="loader-orb">
        <span className="loader-orb-icon">
          <Icon size={22} strokeWidth={2} />
        </span>
      </div>
      <p className="loader-label">{config.label}</p>
      <div className="loader-tagline-wrap">
        <p key={`${status}-${idx}`} className="loader-tagline">{tagline}</p>
      </div>
      <p className="loader-hint">This may take 15–30 seconds</p>
    </div>
  )
}

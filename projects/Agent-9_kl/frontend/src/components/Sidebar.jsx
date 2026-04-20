import { useState, useEffect } from 'react'

// ── Section Icons (monoline SVG) ───────────────────────────────────────────
const SECTION_ICONS = {
  campaign: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="10" height="11" rx="1.5" />
      <path d="M6 2v2M10 2v2M5.5 7h5M5.5 10h3" />
    </svg>
  ),
  prompts: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 2l1.2 2.8L12 6l-2.8 1.2L8 10 6.8 7.2 4 6l2.8-1.2L8 2z" />
      <path d="M12.5 11l.6 1.4 1.4.6-1.4.6-.6 1.4-.6-1.4-1.4-.6 1.4-.6.6-1.4z" />
    </svg>
  ),
  news: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2.5" y="3.5" width="11" height="9" rx="1" />
      <path d="M5 6h6M5 8.5h6M5 11h3.5" />
    </svg>
  ),
  inputs: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 4.5c0-.8.7-1.5 1.5-1.5h7c.8 0 1.5.7 1.5 1.5v5c0 .8-.7 1.5-1.5 1.5H7l-3 2.5v-2.5h-.5c-.3 0-.5-.2-.5-.5v-6z" />
    </svg>
  ),
}

// ── Collapsible Section ────────────────────────────────────────────────────
function SidebarSection({ title, icon, count, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen)
  const [hasAutoOpened, setHasAutoOpened] = useState(defaultOpen)

  // Auto-open when count goes from 0 to >0
  useEffect(() => {
    if (count > 0 && !hasAutoOpened) {
      setOpen(true)
      setHasAutoOpened(true)
    }
  }, [count, hasAutoOpened])

  return (
    <div className="sidebar-section">
      <button
        className="sidebar-section-header"
        onClick={() => setOpen(!open)}
      >
        <span className="sidebar-section-title">
          {icon && <span className="sidebar-section-icon">{SECTION_ICONS[icon]}</span>}
          {title}
          {count != null && count > 0 && (
            <span className="sidebar-section-count">{count}</span>
          )}
        </span>
        <span className={`sidebar-section-chevron ${open ? 'open' : ''}`}>
          &#x25B8;
        </span>
      </button>
      {open && (
        <div className="sidebar-section-body">
          {children}
        </div>
      )}
    </div>
  )
}

// ── Status Badge ───────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const config = {
    approving_trend: { label: 'Reviewing Topic', className: 'badge-yellow' },
    approving_audience: { label: 'Reviewing Audience', className: 'badge-yellow' },
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

// ── Expandable Text ────────────────────────────────────────────────────────
function ExpandableText({ text, maxLines = 2 }) {
  const [expanded, setExpanded] = useState(false)

  if (!text) return null

  return (
    <div>
      <p
        className="sidebar-meta-value"
        style={expanded ? { WebkitLineClamp: 'unset' } : undefined}
      >
        {text}
      </p>
      {text.length > 80 && (
        <button
          className="sidebar-expand-btn"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  )
}

// ── Step Label Map ─────────────────────────────────────────────────────────
const STEP_LABELS = {
  start: 'Campaign Start',
  trend_review: 'Trend Review',
  audience_review: 'Audience Review',
  image_review: 'Content Review',
  done_refine: 'Refinement',
}

const ACTION_LABELS = {
  start: 'Started',
  approve: 'Approved',
  edit: 'Edited',
  're-search': 'Re-searched',
  regen_image: 'Regen Image',
  regen_text_and_image: 'Regen All',
  refine: 'Refined',
}

// Active agent mapping for processing states
const ACTIVE_AGENT = {
  starting: 'Trend Analyzer',
  approved_trend: 'Audience Analyzer',
  audience_approved: 'Writer',
  approved_text: 'Image Generator',
  publisher: 'Publisher',
}

// ── Sidebar Component ──────────────────────────────────────────────────────
export default function Sidebar({ state, status, inputHistory = [] }) {
  const allNews = [...(state?.all_retrieved_news || [])]
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
  const rawNews = state?.raw_news || []

  // Determine which articles were used by AI (by URL match)
  const usedUrls = new Set(rawNews.map(a => a.url))

  return (
    <aside className="sidebar">
      {/* Logo + Badge */}
      <div className="sidebar-header">
        <div className="header-logo">
          Campaign <span>Agent</span>
        </div>
        {status && <StatusBadge status={status} />}
      </div>

      <hr className="divider" />

      {/* ── Hero Card: current campaign snapshot ── */}
      {(ACTIVE_AGENT[status] || state?.trend_topic || state?.target_audience) && (
        <div className="sidebar-hero">
          {ACTIVE_AGENT[status] && (
            <div className="sidebar-hero-running">
              <span className="sidebar-active-dot" />
              <span>Running · {ACTIVE_AGENT[status]}</span>
            </div>
          )}
          {state?.trend_topic && (
            <div className="sidebar-hero-field">
              <span className="sidebar-hero-label">Topic</span>
              <p className="sidebar-hero-topic">{state.trend_topic}</p>
            </div>
          )}
          {state?.target_audience && (
            <div className="sidebar-hero-field">
              <span className="sidebar-hero-label">Audience</span>
              <span className="meta-tag">{state.target_audience.replace(/_/g, ' ')}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Section: Campaign Summary ── */}
      <SidebarSection title="Campaign" icon="campaign" defaultOpen={true}>
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

          {state?.trend_context && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Context</span>
              <ExpandableText text={state.trend_context} />
            </div>
          )}

          {state?.target_audience && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Audience</span>
              <span className="meta-tag">{state.target_audience.replace(/_/g, ' ')}</span>
            </div>
          )}

          {state?.visual_style_preset && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Photo Style</span>
              <span className="meta-tag">{state.visual_style_preset.replace(/_/g, ' ')}</span>
            </div>
          )}

          {state?.audience_brief && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Audience Brief</span>
              <ExpandableText text={state.audience_brief} />
            </div>
          )}

          {state?.visual_style && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Visual Style</span>
              <ExpandableText text={state.visual_style} />
            </div>
          )}

          {state?.visual_elements && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Visual Elements</span>
              <ExpandableText text={state.visual_elements} />
            </div>
          )}

          {state?.image_prompt && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Image Prompt</span>
              <ExpandableText text={state.image_prompt} />
            </div>
          )}

          {state?.overlay_text && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Overlay Text</span>
              <div className="sidebar-overlay-text">
                {state.overlay_text.headline && (
                  <div className="sidebar-overlay-line">
                    <strong>Headline:</strong> {state.overlay_text.headline}
                  </div>
                )}
                {state.overlay_text.key_fact && (
                  <div className="sidebar-overlay-line">
                    <strong>Key Fact:</strong> {state.overlay_text.key_fact}
                  </div>
                )}
                {state.overlay_text.source_line && (
                  <div className="sidebar-overlay-line">
                    <strong>Source:</strong> {state.overlay_text.source_line}
                  </div>
                )}
              </div>
            </div>
          )}

          {state?.user_guidance && (
            <div className="sidebar-meta-item">
              <span className="sidebar-meta-label">Guidance</span>
              <ExpandableText text={state.user_guidance} />
            </div>
          )}

          {!state?.trend_topic && !state?.user_search_keywords && (
            <p className="caption" style={{ textAlign: 'center' }}>
              Campaign info will appear here
            </p>
          )}
        </div>
      </SidebarSection>

      {/* ── Section: Agent Prompts ── */}
      {(state?.prompt_log?.length > 0) && (
        <SidebarSection
          title="Agent Prompts"
          icon="prompts"
          count={state.prompt_log.length}
          defaultOpen={false}
        >
          <div className="sidebar-prompt-log">
            {state.prompt_log.map((entry, i) => (
              <div key={i} className="sidebar-prompt-entry">
                <div className="sidebar-prompt-agent">{entry.agent}</div>
                <p className="sidebar-prompt-summary">{entry.summary}</p>
                <div className="sidebar-prompt-flags">
                  {entry.user_guidance && <span className="meta-tag small">user guidance</span>}
                  {entry.user_keywords && <span className="meta-tag small">user keywords</span>}
                  {entry.text_feedback && <span className="meta-tag small">text feedback</span>}
                  {entry.image_feedback && <span className="meta-tag small">image feedback</span>}
                  {entry.audience_feedback && <span className="meta-tag small">audience feedback</span>}
                  {entry.writer_prompt_override && <span className="meta-tag small">custom prompt</span>}
                </div>
              </div>
            ))}
          </div>
        </SidebarSection>
      )}

      {/* ── Section: News Sources ── */}
      <SidebarSection
        title="News Sources"
        icon="news"
        count={allNews.length}
        defaultOpen={allNews.length > 0}
      >
        {allNews.length === 0 ? (
          <p className="caption" style={{ textAlign: 'center' }}>
            No articles yet
          </p>
        ) : (
          <div className="sidebar-news-list">
            {allNews.map((article, i) => {
              const isUsed = usedUrls.has(article.url)
              return (
                <NewsItem key={i} article={article} isUsed={isUsed} />
              )
            })}
          </div>
        )}
      </SidebarSection>

      {/* ── Section: User Input History ── */}
      <SidebarSection
        title="Your Inputs"
        icon="inputs"
        count={inputHistory.length}
        defaultOpen={inputHistory.length > 0}
      >
        {inputHistory.length === 0 ? (
          <p className="caption" style={{ textAlign: 'center' }}>
            Your actions will appear here
          </p>
        ) : (
          <div className="sidebar-input-list">
            {[...inputHistory].reverse().map((entry, i) => (
              <div key={i}>
                {entry.step === 'done_refine' && (
                  <div className="sidebar-input-divider">Refinement</div>
                )}
              <div className={`sidebar-input-entry ${i === 0 ? 'latest' : ''}`}>
                <div className="sidebar-input-header">
                  <span className="sidebar-input-step">
                    {STEP_LABELS[entry.step] || entry.step}
                  </span>
                  <span className="sidebar-input-right">
                    <span className="sidebar-input-action">
                      {ACTION_LABELS[entry.action] || entry.action}
                    </span>
                    {entry.timestamp && (
                      <span className="sidebar-input-time">
                        {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    )}
                  </span>
                </div>
                {entry.keywords && (
                  <p className="sidebar-input-text">Keywords: "{entry.keywords}"</p>
                )}
                {entry.customTopic && (
                  <p className="sidebar-input-text">Custom topic: "{entry.customTopic}"</p>
                )}
                {entry.selectedArticle && (
                  <p className="sidebar-input-text">Selected: "{entry.selectedArticle}"</p>
                )}
                {entry.guidance && (
                  <p className="sidebar-input-text">Guidance: "{entry.guidance}"</p>
                )}
                {entry.feedback && (
                  <p className="sidebar-input-text">Feedback: "{entry.feedback}"</p>
                )}
                {entry.targetAudience && (
                  <p className="sidebar-input-text">Audience: "{entry.targetAudience}"</p>
                )}
                {entry.refineTarget && (
                  <p className="sidebar-input-text">Target: {entry.refineTarget}</p>
                )}
              </div>
              </div>
            ))}
          </div>
        )}
      </SidebarSection>
    </aside>
  )
}

// ── News Item Sub-component ────────────────────────────────────────────────
function NewsItem({ article, isUsed }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`sidebar-news-item ${isUsed ? 'selected' : ''}`}>
      <a
        href={article.url}
        target="_blank"
        rel="noreferrer"
        className="sidebar-news-title"
      >
        {article.title || 'Untitled'}
      </a>
      <div className="sidebar-news-meta">
        <span className="sidebar-news-source">{article.source || 'Unknown'}</span>
        {article.timestamp && (
          <span className="sidebar-news-time"> · {article.timestamp}</span>
        )}
        {isUsed && <span className="sidebar-news-used">AI used</span>}
      </div>
      {article.content && (
        <>
          <p
            className="sidebar-news-content"
            style={expanded ? { WebkitLineClamp: 'unset' } : undefined}
          >
            {article.content}
          </p>
          {article.content.length > 120 && (
            <button
              className="sidebar-expand-btn"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </>
      )}
    </div>
  )
}

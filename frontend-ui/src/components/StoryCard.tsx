/**
 * Story card component showing vulnerability details.
 * Styled with the sensei theme - like ancient scrolls.
 */

import { useState } from 'react'
import clsx from 'clsx'
import type { StoryCard as StoryCardType, Severity, StoryType } from '@/types/api'

interface StoryCardProps {
  story: StoryCardType
  onGenerateComic: (story: StoryCardType) => void
  isGenerating?: boolean
}

const SEVERITY_STYLES: Record<Severity, { bg: string; text: string; label: string }> = {
  CRITICAL: { bg: 'bg-[#c45c48]/10', text: 'text-[#c45c48]', label: 'Critical' },
  HIGH: { bg: 'bg-[#d4a853]/10', text: 'text-[#b8923a]', label: 'High' },
  MEDIUM: { bg: 'bg-[#d4a853]/10', text: 'text-[#9a7a2e]', label: 'Medium' },
  LOW: { bg: 'bg-[#7a9e7e]/10', text: 'text-[#5d7e61]', label: 'Low' },
  INFO: { bg: 'bg-[#9ca8b3]/10', text: 'text-[#6a7580]', label: 'Info' },
}

const STORY_TYPE_STYLES: Record<StoryType, { bg: string; text: string; label: string }> = {
  ACTIVE: { bg: 'bg-[#c45c48]', text: 'text-white', label: 'Active Threat' },
  HISTORICAL_YOURS: { bg: 'bg-[#7a5c8f]/10', text: 'text-[#7a5c8f]', label: 'Historical' },
  HISTORICAL_GENERAL: { bg: 'bg-[#9ca8b3]/10', text: 'text-[#6a7580]', label: 'Wisdom Tale' },
}

export function StoryCard({ story, onGenerateComic, isGenerating }: StoryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const storyStyle = STORY_TYPE_STYLES[story.storyType]
  const severityStyle = story.severity ? SEVERITY_STYLES[story.severity] : null

  return (
    <div
      className={clsx(
        'paper-card rounded-xl overflow-hidden transition-all',
        isExpanded && 'ring-2 ring-[#c45c48]/30'
      )}
    >
      {/* Header - Always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-5 text-left hover:bg-[#faf8f5]/50 transition-colors"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-[#2d2a26] text-lg">
              {story.title}
            </h3>
            <p className="text-sm text-[#6a6560] mt-1 font-mono">
              {story.packageName}@{story.packageVersion}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Story type badge */}
            <span
              className={clsx(
                'px-2.5 py-1 text-xs font-medium rounded-full',
                storyStyle.bg,
                storyStyle.text
              )}
            >
              {storyStyle.label}
            </span>
            {/* Severity badge */}
            {severityStyle && (
              <span
                className={clsx(
                  'px-2.5 py-1 text-xs font-medium rounded-full',
                  severityStyle.bg,
                  severityStyle.text
                )}
              >
                {severityStyle.label}
              </span>
            )}
            {/* Expand icon */}
            <span
              className={clsx(
                'text-[#9a9590] transition-transform ml-1',
                isExpanded && 'rotate-180'
              )}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </span>
          </div>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-5 pb-5 border-t border-[#e8e4df]">
          <div className="mt-5 space-y-5">
            {/* What happened */}
            <section>
              <h4 className="text-sm font-semibold text-[#2d2a26] mb-2 flex items-center gap-2">
                <span className="temple-accent">☞</span>
                What happened?
              </h4>
              <ul className="space-y-1.5">
                {story.whatHappened.map((item, i) => (
                  <li key={i} className="text-sm text-[#5a5550] flex items-start gap-2">
                    <span className="text-[#c45c48] mt-0.5">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            {/* Why should I care */}
            <section>
              <h4 className="text-sm font-semibold text-[#2d2a26] mb-2 flex items-center gap-2">
                <span className="gold-accent">⚠</span>
                Why should I care?
              </h4>
              <ul className="space-y-1.5">
                {story.whyShouldICare.map((item, i) => (
                  <li key={i} className="text-sm text-[#5a5550] flex items-start gap-2">
                    <span className="text-[#d4a853] mt-0.5">!</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            {/* What should I do */}
            <section>
              <h4 className="text-sm font-semibold text-[#2d2a26] mb-2 flex items-center gap-2">
                <span className="bamboo-accent">✓</span>
                Path to enlightenment
              </h4>
              <ul className="space-y-1.5">
                {story.whatShouldIDo.map((item, i) => (
                  <li key={i} className="text-sm text-[#5a5550] flex items-start gap-2">
                    <span className="text-[#7a9e7e] mt-0.5">→</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            {/* Incident date if available */}
            {story.incidentDate && (
              <p className="text-xs text-[#9a9590] flex items-center gap-1">
                <span>📅</span>
                Incident date: {story.incidentDate}
              </p>
            )}

            {/* Sources */}
            {story.sources.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2">
                {story.sources.map((source, i) => (
                  <a
                    key={i}
                    href={source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-[#7a9e7e] hover:text-[#5d7e61] hover:underline"
                  >
                    🔗 Source {i + 1}
                  </a>
                ))}
              </div>
            )}

            {/* Generate comic button */}
            <button
              onClick={() => onGenerateComic(story)}
              disabled={isGenerating}
              className={clsx(
                'w-full mt-4 px-5 py-3.5 rounded-xl font-medium transition-all',
                'flex items-center justify-center gap-2',
                isGenerating
                  ? 'bg-[#e8e4df] text-[#9a9590] cursor-wait'
                  : 'temple-button shadow-md hover:shadow-lg'
              )}
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  The brush moves...
                </>
              ) : (
                <>
                  <span>🎨</span>
                  Illustrate This Tale
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

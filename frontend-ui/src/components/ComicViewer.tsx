/**
 * Comic viewer component for displaying generated comics.
 * Styled with the sensei theme.
 */

import { useState } from 'react'
import clsx from 'clsx'
import type { GeneratedComic } from '@/types/api'

interface ComicViewerProps {
  comic: GeneratedComic
  onBack: () => void
}

export function ComicViewer({ comic, onBack }: ComicViewerProps) {
  const [currentPage, setCurrentPage] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const currentPageData = comic.pages[currentPage]
  const hasNext = currentPage < comic.pages.length - 1
  const hasPrev = currentPage > 0

  const handlePrev = () => {
    if (hasPrev) setCurrentPage((p) => p - 1)
  }

  const handleNext = () => {
    if (hasNext) setCurrentPage((p) => p + 1)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') handlePrev()
    if (e.key === 'ArrowRight') handleNext()
    if (e.key === 'Escape') setIsFullscreen(false)
  }

  return (
    <div
      className={clsx(
        'flex flex-col',
        isFullscreen && 'fixed inset-0 z-50 bg-[#1a1918]'
      )}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Header */}
      {!isFullscreen && (
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-[#6a6560] hover:text-[#2d2a26] transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Return to scrolls
          </button>

          <div className="text-center">
            <h2 className="brush-text text-xl text-[#2d2a26]">
              {comic.title}
            </h2>
            <p className="text-sm text-[#9a9590]">
              {comic.archetype.toLowerCase()} tale &bull; {comic.artStyle.replace(/_/g, ' ').toLowerCase()}
            </p>
          </div>

          <button
            onClick={() => setIsFullscreen(true)}
            className="p-2 text-[#6a6560] hover:text-[#2d2a26] transition-colors"
            title="Enter meditation mode"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>
      )}

      {/* Fullscreen close button */}
      {isFullscreen && (
        <button
          onClick={() => setIsFullscreen(false)}
          className="absolute top-4 right-4 z-10 p-2 bg-black/50 rounded-full text-white hover:bg-black/70 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      {/* Comic page display */}
      <div
        className={clsx(
          'relative flex-1 flex items-center justify-center',
          isFullscreen ? 'p-4' : 'bg-[#f5f2ef] rounded-xl overflow-hidden border border-[#e8e4df]'
        )}
      >
        {/* Previous button */}
        <button
          onClick={handlePrev}
          disabled={!hasPrev}
          className={clsx(
            'absolute left-2 z-10 p-3 rounded-full transition-all',
            hasPrev
              ? 'bg-white/90 text-[#2d2a26] hover:bg-white shadow-lg'
              : 'bg-[#e8e4df]/50 text-[#b5b0ab] cursor-not-allowed'
          )}
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* Page image */}
        <img
          src={currentPageData.imageUrl}
          alt={`Page ${currentPageData.pageNumber} of ${comic.title}`}
          className={clsx(
            'max-h-[70vh] w-auto object-contain shadow-2xl rounded-lg',
            isFullscreen && 'max-h-[90vh]'
          )}
        />

        {/* Next button */}
        <button
          onClick={handleNext}
          disabled={!hasNext}
          className={clsx(
            'absolute right-2 z-10 p-3 rounded-full transition-all',
            hasNext
              ? 'bg-white/90 text-[#2d2a26] hover:bg-white shadow-lg'
              : 'bg-[#e8e4df]/50 text-[#b5b0ab] cursor-not-allowed'
          )}
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Page indicator and navigation */}
      <div className={clsx('flex items-center justify-center gap-4 mt-4', isFullscreen && 'absolute bottom-8 left-0 right-0')}>
        {/* Page dots */}
        <div className="flex items-center gap-2">
          {comic.pages.map((page, index) => (
            <button
              key={page.pageNumber}
              onClick={() => setCurrentPage(index)}
              className={clsx(
                'w-3 h-3 rounded-full transition-all',
                index === currentPage
                  ? 'bg-[#c45c48] scale-125'
                  : 'bg-[#d4d0cb] hover:bg-[#b5b0ab]'
              )}
              aria-label={`Go to page ${page.pageNumber}`}
            />
          ))}
        </div>

        {/* Page count */}
        <span className={clsx('text-sm', isFullscreen ? 'text-white' : 'text-[#6a6560]')}>
          Page {currentPage + 1} of {comic.pages.length}
        </span>
      </div>

      {/* Share URL */}
      {!isFullscreen && (
        <div className="mt-6 p-4 bg-[#f5f2ef] rounded-lg border border-[#e8e4df]">
          <p className="text-sm text-[#6a6560] mb-2 flex items-center gap-1">
            <span>🔗</span>
            Share this wisdom:
          </p>
          <div className="flex items-center gap-2">
            <input
              type="text"
              readOnly
              value={comic.shareUrl}
              className="flex-1 px-3 py-2 bg-white border border-[#e8e4df] rounded-lg text-sm text-[#6a6560] font-mono"
            />
            <button
              onClick={() => navigator.clipboard.writeText(comic.shareUrl)}
              className="px-4 py-2 temple-button rounded-lg text-sm font-medium"
            >
              Copy
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

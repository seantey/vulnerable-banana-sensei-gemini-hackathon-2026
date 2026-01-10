/**
 * Comic generation loading screen.
 * Styled with the sensei theme - meditative waiting.
 */

import { useState, useEffect } from 'react'

interface ComicGenerationLoadingProps {
  title: string
}

const LOADING_MESSAGES = [
  'The sensei contemplates the narrative...',
  'Grinding ink for the brush...',
  'Consulting ancient scrolls...',
  'Meditating on visual harmony...',
  'The brush dances across paper...',
  'Balancing light and shadow...',
  'Crafting the hero\'s journey...',
  'Infusing wisdom into each panel...',
]

export function ComicGenerationLoading({ title }: ComicGenerationLoadingProps) {
  const [messageIndex, setMessageIndex] = useState(0)
  const [dots, setDots] = useState('')

  // Cycle through messages
  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length)
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  // Animate dots
  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'))
    }, 500)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] text-center px-4">
      {/* Zen circle animation */}
      <div className="relative mb-10">
        {/* Outer circle - rotating */}
        <div className="w-32 h-32 rounded-full border-4 border-[#e8e4df] relative">
          {/* Ink brush stroke effect */}
          <div
            className="absolute inset-0 rounded-full border-4 border-t-[#c45c48] border-r-transparent border-b-transparent border-l-transparent animate-spin"
            style={{ animationDuration: '2s' }}
          />
        </div>
        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-4xl">📜</span>
        </div>
        {/* Floating elements */}
        <div className="absolute -top-2 -right-2 text-xl animate-bounce" style={{ animationDuration: '2s' }}>
          ✨
        </div>
        <div className="absolute -bottom-2 -left-2 text-lg animate-pulse">
          🎨
        </div>
      </div>

      <h2 className="brush-text text-2xl text-[#2d2a26] mb-3">
        The Sensei Creates
      </h2>

      <p className="text-lg text-[#c45c48] font-medium mb-4 max-w-md">
        "{title}"
      </p>

      <p className="text-[#6a6560] mb-8 h-6">
        {LOADING_MESSAGES[messageIndex]}{dots}
      </p>

      {/* Progress bar styled as ink stroke */}
      <div className="w-64 h-1 bg-[#e8e4df] rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-[#c45c48] to-[#d4a853] rounded-full"
          style={{
            width: '60%',
            animation: 'pulse 2s ease-in-out infinite',
          }}
        />
      </div>

      <p className="text-sm text-[#9a9590] mt-6">
        ☯ Creating a visual masterpiece takes 2-5 minutes
      </p>

      <p className="text-xs text-[#b5b0ab] mt-2">
        Each page is hand-crafted by the AI brush
      </p>
    </div>
  )
}

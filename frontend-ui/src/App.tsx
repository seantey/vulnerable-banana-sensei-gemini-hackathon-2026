/**
 * Main application component for Vulnerable Banana Sensei.
 * Manages the flow: Upload → Stories → Generate Comic → View
 */

import { useState, useCallback } from 'react'
import { UploadZone } from '@/components/UploadZone'
import { StoryCard } from '@/components/StoryCard'
import { ComicViewer } from '@/components/ComicViewer'
import { ComicGenerationLoading } from '@/components/ComicGenerationLoading'
import { scanFile, generateComic, ApiError } from '@/lib/api'
import { saveScan, addComicToScan, generateScanId } from '@/lib/storage'
import type { ScanResponse, StoryCard as StoryCardType, GeneratedComic } from '@/types/api'

type AppView = 'upload' | 'stories' | 'generating' | 'comic'

// Banana Sensei mascot SVG component
function BananaSensei({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Banana body */}
      <ellipse cx="50" cy="55" rx="25" ry="35" fill="#F7DC6F" stroke="#D4AC0D" strokeWidth="2"/>
      {/* Banana curve highlight */}
      <path d="M35 40 Q50 30 65 40" stroke="#FEF9E7" strokeWidth="4" strokeLinecap="round" fill="none"/>
      {/* Sensei beard */}
      <path d="M35 70 Q50 95 65 70" fill="#E8E4DF" stroke="#9CA8B3" strokeWidth="1"/>
      <path d="M40 72 Q50 88 60 72" fill="#F4F1ED" stroke="none"/>
      {/* Eyes */}
      <circle cx="42" cy="50" r="4" fill="#2D2A26"/>
      <circle cx="58" cy="50" r="4" fill="#2D2A26"/>
      <circle cx="43" cy="49" r="1.5" fill="white"/>
      <circle cx="59" cy="49" r="1.5" fill="white"/>
      {/* Wise eyebrows */}
      <path d="M36 44 Q42 40 48 44" stroke="#2D2A26" strokeWidth="2" strokeLinecap="round" fill="none"/>
      <path d="M52 44 Q58 40 64 44" stroke="#2D2A26" strokeWidth="2" strokeLinecap="round" fill="none"/>
      {/* Sensei headband */}
      <rect x="30" y="32" width="40" height="6" rx="2" fill="#C45C48"/>
      <circle cx="50" cy="35" r="4" fill="#D4A853" stroke="#C45C48" strokeWidth="1"/>
      {/* Stem as top knot */}
      <ellipse cx="50" cy="22" rx="6" ry="8" fill="#7A9E7E" stroke="#5D7E61" strokeWidth="1"/>
    </svg>
  )
}

function App() {
  // App state
  const [view, setView] = useState<AppView>('upload')
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null)
  const [currentScanId, setCurrentScanId] = useState<string | null>(null)
  const [selectedStory, setSelectedStory] = useState<StoryCardType | null>(null)
  const [generatedComic, setGeneratedComic] = useState<GeneratedComic | null>(null)

  // Loading and error states
  const [isScanning, setIsScanning] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Handle file upload and scan
  const handleFileSelect = useCallback(async (file: File) => {
    setIsScanning(true)
    setError(null)

    try {
      const result = await scanFile(file)
      setScanResult(result)

      // Save to localStorage
      const scanId = generateScanId()
      setCurrentScanId(scanId)
      saveScan({
        id: scanId,
        filename: result.filename,
        timestamp: new Date().toISOString(),
        packageCount: result.packageCount,
        scanResponse: result,
        report: null,
        comics: [],
      })

      setView('stories')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to scan file. Please try again.')
      }
    } finally {
      setIsScanning(false)
    }
  }, [])

  // Handle comic generation
  const handleGenerateComic = useCallback(
    async (story: StoryCardType) => {
      setSelectedStory(story)
      setIsGenerating(true)
      setView('generating')
      setError(null)

      try {
        const comic = await generateComic(story)
        setGeneratedComic(comic)

        // Save comic to scan history
        if (currentScanId) {
          addComicToScan(currentScanId, { hash: comic.comicHash, title: comic.title })
        }

        setView('comic')
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message)
        } else {
          setError('Failed to generate comic. Please try again.')
        }
        setView('stories')
      } finally {
        setIsGenerating(false)
      }
    },
    [currentScanId]
  )

  // Navigation handlers
  const handleBackToStories = useCallback(() => {
    setGeneratedComic(null)
    setSelectedStory(null)
    setView('stories')
  }, [])

  const handleStartOver = useCallback(() => {
    setScanResult(null)
    setCurrentScanId(null)
    setSelectedStory(null)
    setGeneratedComic(null)
    setError(null)
    setView('upload')
  }, [])

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-10">
          <button
            onClick={handleStartOver}
            className="inline-flex flex-col items-center hover:opacity-90 transition-opacity"
          >
            <BananaSensei className="w-20 h-20 mb-3 drop-shadow-lg" />
            <h1 className="brush-text text-4xl text-[#2d2a26] mb-1">
              Vulnerable Banana <span className="temple-accent">Sensei</span>
            </h1>
          </button>
          <p className="text-[#5a5550] mt-2 text-lg">
            Transform your dependency vulnerabilities into educational comics
          </p>
          <div className="ink-divider w-32 mx-auto mt-4" />
        </header>

        <main className="max-w-4xl mx-auto">
          {/* Upload View */}
          {view === 'upload' && (
            <div className="paper-card rounded-2xl p-8">
              <div className="text-center mb-6">
                <h2 className="brush-text text-2xl text-[#2d2a26] mb-2">
                  Begin Your Training
                </h2>
                <p className="text-[#6a6560]">
                  Submit your package.json and learn the way of secure dependencies
                </p>
              </div>
              <UploadZone
                onFileSelect={handleFileSelect}
                isLoading={isScanning}
                error={error}
              />
            </div>
          )}

          {/* Stories View */}
          {view === 'stories' && scanResult && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="paper-card rounded-2xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="brush-text text-xl text-[#2d2a26]">
                      Scroll of Discoveries
                    </h2>
                    <p className="text-[#6a6560] mt-1">
                      <span className="font-medium">{scanResult.packageCount}</span> packages examined &bull;{' '}
                      <span className="temple-accent font-medium">{scanResult.vulnerabilities.length}</span> vulnerabilities found &bull;{' '}
                      <span className="bamboo-accent font-medium">{scanResult.storyCards.length}</span> tales to tell
                    </p>
                  </div>
                  <button
                    onClick={handleStartOver}
                    className="px-4 py-2 text-sm text-[#6a6560] hover:text-[#2d2a26] border border-[#e8e4df] rounded-lg hover:border-[#d4d0cb] transition-colors"
                  >
                    New Scroll
                  </button>
                </div>
              </div>

              {/* Story Cards */}
              {scanResult.storyCards.length > 0 ? (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-[#5a5550] flex items-center gap-2">
                    <span className="gold-accent">☞</span>
                    Choose a tale to illuminate through comics:
                  </h3>
                  {scanResult.storyCards.map((story) => (
                    <StoryCard
                      key={story.id}
                      story={story}
                      onGenerateComic={handleGenerateComic}
                      isGenerating={isGenerating && selectedStory?.id === story.id}
                    />
                  ))}
                </div>
              ) : (
                <div className="paper-card rounded-2xl p-8 text-center">
                  <span className="text-5xl mb-4 block">☯</span>
                  <h3 className="brush-text text-xl text-[#7a9e7e] mb-2">
                    Your Dependencies are at Peace
                  </h3>
                  <p className="text-[#6a6560]">
                    The sensei finds no vulnerabilities. Your code walks the path of security.
                  </p>
                </div>
              )}

              {/* Error display */}
              {error && (
                <div className="paper-card rounded-lg p-4 border-l-4 border-[#c45c48]">
                  <p className="text-[#c45c48]">{error}</p>
                </div>
              )}
            </div>
          )}

          {/* Generating View */}
          {view === 'generating' && selectedStory && (
            <div className="paper-card rounded-2xl p-8">
              <ComicGenerationLoading title={selectedStory.title} />
            </div>
          )}

          {/* Comic View */}
          {view === 'comic' && generatedComic && (
            <div className="paper-card rounded-2xl p-6">
              <ComicViewer comic={generatedComic} onBack={handleBackToStories} />
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="mt-16 text-center text-sm text-[#9a9590]">
          <div className="ink-divider w-24 mx-auto mb-4" />
          <p>
            Powered by Gemini 3 Pro &bull; The way of the Nano Banana Pro
          </p>
          <p className="mt-1 text-xs">
            ☯ Security wisdom through visual storytelling
          </p>
        </footer>
      </div>
    </div>
  )
}

export default App

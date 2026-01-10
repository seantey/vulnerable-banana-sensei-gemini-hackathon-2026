/**
 * Upload zone component with drag & drop support.
 * Styled with the sensei theme.
 */

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import clsx from 'clsx'

interface UploadZoneProps {
  onFileSelect: (file: File) => void
  isLoading?: boolean
  error?: string | null
}

export function UploadZone({ onFileSelect, isLoading, error }: UploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0])
      }
    },
    [onFileSelect]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/json': ['.json'],
    },
    multiple: false,
    disabled: isLoading,
  })

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={clsx(
          'relative border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer',
          isDragActive && 'border-[#c45c48] bg-[#c45c48]/5',
          !isDragActive &&
            !isLoading &&
            'border-[#d4d0cb] hover:border-[#c45c48] hover:bg-[#faf8f5]',
          isLoading && 'border-[#e8e4df] cursor-wait bg-[#faf8f5]',
          error && 'border-[#c45c48]/50'
        )}
      >
        <input {...getInputProps()} />

        {isLoading ? (
          <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-4 sensei-spinner" />
            <div>
              <p className="text-lg font-medium text-[#2d2a26]">
                The sensei examines your dependencies...
              </p>
              <p className="text-sm text-[#6a6560] mt-1">
                Consulting the ancient scrolls of OSV
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="text-5xl">{isDragActive ? '📜' : '📚'}</div>
            <div>
              <p className="text-lg font-medium text-[#2d2a26]">
                {isDragActive ? 'Release to begin training' : 'Present your package.json scroll'}
              </p>
              <p className="text-sm text-[#6a6560] mt-1">
                Drag & drop or click to select
              </p>
            </div>
            <div className="flex items-center gap-2 mt-2 text-xs text-[#9a9590]">
              <span>☰</span>
              <span>Supports package.json files up to 1MB</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-[#c45c48]/5 border border-[#c45c48]/20 rounded-lg border-l-4 border-l-[#c45c48]">
          <p className="text-sm text-[#c45c48]">{error}</p>
        </div>
      )}
    </div>
  )
}

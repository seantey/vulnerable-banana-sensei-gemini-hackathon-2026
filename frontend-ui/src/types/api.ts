/**
 * TypeScript interfaces for API types.
 * These mirror the Python Pydantic models, using camelCase.
 */

export type Ecosystem = 'npm' | 'pypi'
export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
export type StoryType = 'ACTIVE' | 'HISTORICAL_YOURS' | 'HISTORICAL_GENERAL'
export type Archetype = 'HEIST' | 'OOPS' | 'SAGA' | 'LURKER'
export type ArtStyle =
  | 'EPIC_SCIFI'
  | 'NOIR_THRILLER'
  | 'RETRO_COMIC'
  | 'MINIMAL_XKCD'
  | 'CYBERPUNK'
  | 'PROPAGANDA_POSTER'

/**
 * A potential story for comic generation.
 */
export interface StoryCard {
  id: string
  title: string
  packageName: string
  packageVersion: string
  storyType: StoryType
  severity: Severity | null
  whatHappened: string[]
  whyShouldICare: string[]
  whatShouldIDo: string[]
  incidentDate: string | null
  sources: string[]
}

/**
 * A vulnerability from OSV.
 */
export interface Vulnerability {
  vulnId: string
  packageName: string
  affectedVersions: string
  severity: Severity
  summary: string
  details: string | null
  references: string[]
}

/**
 * Response from scanning a dependency file.
 */
export interface ScanResponse {
  filename: string
  packageCount: number
  storyCards: StoryCard[]
  vulnerabilities: Vulnerability[]
  cleanCount: number
}

/**
 * A single generated page image.
 */
export interface GeneratedPage {
  pageNumber: number
  imageUrl: string
}

/**
 * A generated comic ready for viewing.
 */
export interface GeneratedComic {
  comicHash: string
  title: string
  archetype: Archetype
  artStyle: ArtStyle
  pageCount: number
  totalPanels: number
  pages: GeneratedPage[]
  shareUrl: string
  generatedAt: string
}

/**
 * Summary counts for the report.
 */
export interface ReportSummary {
  critical: number
  high: number
  medium: number
  low: number
  clean: number
}

/**
 * A single issue in the security report.
 */
export interface ReportIssue {
  packageName: string
  packageVersion: string
  issue: string
  recommendation: string | null
  severity: Severity
  comicHash: string | null
}

/**
 * The full security report.
 */
export interface SecurityReport {
  reportHash: string
  filename: string
  generatedAt: string
  summary: ReportSummary
  requiresAction: ReportIssue[]
  informational: ReportIssue[]
  cleanCount: number
  downloadUrl: string
}

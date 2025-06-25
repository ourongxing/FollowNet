export interface UserData {
  username: string
  display_name: string
  bio: string
  avatar_url: string
  profile_url: string
  platform: string
  type: string
  follower_count: number
  following_count: number
  company: string
  location: string
  website: string
  twitter: string
  email: string
  public_repos?: number
  scraped_at: string
}

export interface ScrapeResult {
  success: boolean
  message: string
  platform: string
  total_extracted: number
  data: UserData[]
  download_url: string
  current_page: number
  has_next_page: boolean
  cache_id: string
}

export type SortField = 'follower_count' | 'following_count' | 'public_repos' | 'scraped_at' | 'username'
export type SortOrder = 'asc' | 'desc'

export type StreamingControlState = 'running' | 'paused' | 'stopping' | 'stopped'

export interface StreamingStatus {
  isStreaming: boolean
  progress: number
  message: string
  stage?: number
  currentUser?: string
  processedCount?: number
  totalCount?: number
  controlState?: StreamingControlState
}

export interface StreamingControls {
  onPause: () => void
  onResume: () => void
  onStop: () => void
  canPause: boolean
  canResume: boolean
  canStop: boolean
}
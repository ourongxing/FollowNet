'use client'

import { useState } from 'react'
import { Github, Twitter, Download, Users, Building, MapPin, Globe, ExternalLink, Calendar, Hash, ChevronLeft, ChevronRight, Mail } from 'lucide-react'

interface UserData {
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

interface ScrapeResult {
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

export default function Home() {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ScrapeResult | null>(null)
  const [error, setError] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  
  const detectPlatform = (inputUrl: string) => {
    const url = inputUrl.toLowerCase()
    if (url.includes('github.com')) return 'GitHub'
    if (url.includes('twitter.com') || url.includes('x.com')) return 'Twitter/X'
    if (url.includes('producthunt.com')) return 'Product Hunt'
    if (url.includes('weibo.com')) return 'Weibo'
    if (url.includes('news.ycombinator.com')) return 'Hacker News'
    if (url.includes('youtube.com') || url.includes('youtu.be')) return 'YouTube'
    if (url.includes('reddit.com')) return 'Reddit'
    if (url.includes('medium.com')) return 'Medium'
    if (url.includes('bilibili.com')) return 'Bilibili'
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return
    
    setCurrentPage(1)
    await fetchPage(1, true)
  }

  const fetchPage = async (page: number, isNewSearch: boolean = false) => {
    setIsLoading(true)
    if (isNewSearch) {
      setError('')
      setResult(null)
    }

    try {
      const response = await fetch('http://localhost:8000/api/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url: url.trim(),
          page: page
        }),
      })

      const data = await response.json()

      if (data.success) {
        setResult(data)
        setCurrentPage(page)
      } else {
        setError(data.message || 'Scraping failed')
      }
    } catch (err) {
      setError('Network error, please try again later')
    } finally {
      setIsLoading(false)
    }
  }

  const handleNextPage = () => {
    if (result?.has_next_page) {
      const nextPage = currentPage + 1
      fetchPage(nextPage)
    }
  }

  const handlePrevPage = () => {
    if (currentPage > 1) {
      const prevPage = currentPage - 1
      fetchPage(prevPage)
    }
  }

  const handleDownloadCSV = () => {
    if (result?.download_url) {
      const fullUrl = result.download_url.startsWith('/') 
        ? `http://localhost:8000${result.download_url}` 
        : result.download_url
      window.open(fullUrl, '_blank')
    }
  }

  const handleUserClick = (profileUrl: string) => {
    window.open(profileUrl, '_blank', 'noopener,noreferrer')
  }

  const detectedPlatform = detectPlatform(url)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 mb-6">
            <span className="text-3xl font-bold text-white">F</span>
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">FollowNet</h1>
          <p className="text-xl text-blue-200 max-w-2xl mx-auto">
            One-click scraping of social media platform follower data, supporting pagination and data export
          </p>
        </div>

        {/* 搜索表单 */}
        <div className="max-w-4xl mx-auto mb-12">
          <form onSubmit={handleSubmit} className="relative">
            <div className="relative">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter URL to scrape, e.g.: https://github.com/username"
                className="w-full px-6 py-4 text-lg bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl text-white placeholder-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent pr-32"
                disabled={isLoading}
              />
              {detectedPlatform && (
                <div className="absolute right-20 top-1/2 transform -translate-y-1/2 px-3 py-1 bg-blue-500/20 text-blue-200 text-sm rounded-lg">
                  {detectedPlatform}
                </div>
              )}
              <button
                type="submit"
                disabled={isLoading || !url.trim()}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                {isLoading ? 'Scraping...' : 'Start Scraping'}
              </button>
            </div>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-200">
              {error}
            </div>
          )}
        </div>

        {/* 结果展示 */}
        {result && (
          <div className="max-w-7xl mx-auto">
            {/* 结果概览 */}
            <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 mb-8">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Scraping Results</h2>
                  <div className="flex flex-wrap gap-4 text-blue-200">
                    <span className="flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      Page {result.current_page}, {result.total_extracted} users total
                    </span>
                    <span className="flex items-center gap-2">
                      <Hash className="w-4 h-4" />
                      Platform: {result.platform}
                    </span>
                    <span className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      {new Date().toLocaleString('zh-CN')}
                    </span>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleDownloadCSV}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-200"
                  >
                    <Download className="w-4 h-4" />
                    Export Current Page CSV
                  </button>
                </div>
              </div>
            </div>

            {/* 分页控制 */}
            <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 mb-6">
              <div className="flex items-center justify-between">
                <button
                  onClick={handlePrevPage}
                  disabled={currentPage === 1 || isLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-all"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>
                
                <span className="text-blue-200">
                  Page {currentPage} {result.has_next_page && '/ More'}
                </span>
                
                <button
                  onClick={handleNextPage}
                  disabled={!result.has_next_page || isLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-all"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* 用户列表 */}
            <div className="grid gap-4 mb-6">
              {result.data.map((user, index) => (
                <div 
                  key={`${user.username}-${index}`} 
                  className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all duration-200 cursor-pointer"
                  onClick={() => handleUserClick(user.profile_url)}
                >
                  <div className="flex items-start gap-4">
                    <img
                      src={user.avatar_url}
                      alt={user.username}
                      className="w-16 h-16 rounded-full border-2 border-white/20"
                      onError={(e) => {
                        e.currentTarget.src = `https://ui-avatars.com/api/?name=${user.username}&background=random`
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-semibold text-white truncate">
                          {user.display_name || user.username}
                        </h3>
                        <span className="text-blue-200">@{user.username}</span>
                        <ExternalLink className="w-4 h-4 text-blue-400" />
                      </div>
                      
                      {user.bio && (
                        <p className="text-blue-100 mb-3 line-clamp-2">{user.bio}</p>
                      )}
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        {user.follower_count > 0 && (
                          <div className="flex items-center gap-2 text-blue-200">
                            <Users className="w-4 h-4" />
                            {user.follower_count.toLocaleString()} followers
                          </div>
                        )}
                        {user.following_count > 0 && (
                          <div className="flex items-center gap-2 text-blue-200">
                            <Users className="w-4 h-4" />
                            {user.following_count.toLocaleString()} following
                          </div>
                        )}
                        {user.company && (
                          <div className="flex items-center gap-2 text-blue-200">
                            <Building className="w-4 h-4" />
                            {user.company}
                          </div>
                        )}
                        {user.location && (
                          <div className="flex items-center gap-2 text-blue-200">
                            <MapPin className="w-4 h-4" />
                            {user.location}
                          </div>
                        )}
                        {user.email && (
                          <div className="flex items-center gap-2 text-blue-200">
                            <Mail className="w-4 h-4" />
                            {user.email}
                          </div>
                        )}
                        {user.website && (
                          <div className="flex items-center gap-2 text-blue-200">
                            <Globe className="w-4 h-4" />
                            <span className="hover:text-blue-100 truncate">
                              {user.website}
                            </span>
                          </div>
                        )}
                        {user.public_repos && user.public_repos > 0 && (
                          <div className="flex items-center gap-2 text-blue-200">
                            <Github className="w-4 h-4" />
                            {user.public_repos} Repositories
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 底部分页控制 */}
            <div className="flex justify-center gap-4">
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1 || isLoading}
                className="flex items-center gap-2 px-6 py-3 bg-white/10 border border-white/20 rounded-xl text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
                上一页
              </button>
              
              <div className="flex items-center px-6 py-3 bg-white/10 border border-white/20 rounded-xl text-blue-200">
                第 {currentPage} 页 {result.has_next_page && '/ 更多'}
              </div>
              
              <button
                onClick={handleNextPage}
                disabled={!result.has_next_page || isLoading}
                className="flex items-center gap-2 px-6 py-3 bg-white/10 border border-white/20 rounded-xl text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-all"
              >
                下一页
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* 平台展示 - 只在没有结果时显示 */}
        {!result && (
          <div className="max-w-6xl mx-auto">
            <h3 className="text-2xl font-bold text-white text-center mb-8">支持的平台</h3>
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="bg-gradient-to-br from-gray-700 to-gray-900 p-8 rounded-3xl shadow-2xl hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-6 mx-auto">
                  <Github className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white text-center mb-3">GitHub</h3>
                <p className="text-white/80 text-center text-sm">Repositories Star 用户 & 用户关注者</p>
              </div>
              
              <div className="bg-gradient-to-br from-blue-400 to-blue-600 p-8 rounded-3xl shadow-2xl hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-6 mx-auto">
                  <Twitter className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white text-center mb-3">Twitter/X</h3>
                <p className="text-white/80 text-center text-sm">用户关注者 & 关注列表</p>
              </div>
              
              <div className="bg-gradient-to-br from-orange-400 to-orange-600 p-8 rounded-3xl shadow-2xl hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-6 mx-auto">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white text-center mb-3">Product Hunt</h3>
                <p className="text-white/80 text-center text-sm">产品投票者数据</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { name: 'Weibo', color: 'from-red-400 to-red-600' },
                { name: 'Hacker News', color: 'from-orange-500 to-yellow-500' },
                { name: 'YouTube', color: 'from-red-500 to-red-700' },
                { name: 'Reddit', color: 'from-orange-600 to-red-600' },
                { name: 'Medium', color: 'from-green-400 to-green-600' },
                { name: 'Bilibili', color: 'from-pink-400 to-pink-600' }
              ].map((platform) => (
                <div key={platform.name} className={`bg-gradient-to-br ${platform.color} p-6 rounded-2xl shadow-lg hover:scale-105 transition-all duration-300`}>
                  <h4 className="text-lg font-semibold text-white text-center">{platform.name}</h4>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 
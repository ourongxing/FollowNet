'use client'

import { useState, useMemo } from 'react'
import { Github, Twitter, Download, Users, Building, MapPin, Globe, ExternalLink, Mail, ArrowUpDown, ArrowUp, ArrowDown, Search, Star } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

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

type SortField = 'follower_count' | 'following_count' | 'public_repos' | 'scraped_at' | 'username'
type SortOrder = 'asc' | 'desc'

export default function Home() {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [maxUsers, setMaxUsers] = useState(10)
  const [streamingData, setStreamingData] = useState<UserData[]>([])
  const [sortField, setSortField] = useState<SortField>('follower_count')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [streamingStatus, setStreamingStatus] = useState<{
    isStreaming: boolean
    progress: number
    message: string
    stage?: number
    currentUser?: string
    processedCount?: number
    totalCount?: number
  }>({
    isStreaming: false,
    progress: 0,
    message: ''
  })

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
    if (!url.trim() || streamingStatus.isStreaming) return

    await handleStreamingScrape()
  }

  const handleStreamingScrape = async () => {
    if (!url.trim()) return

    setStreamingData([])
    setError('')
    setStreamingStatus({
      isStreaming: true,
      progress: 0,
      message: '正在连接...'
    })

    try {
      const response = await fetch('http://localhost:8000/api/scrape-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.trim(),
          page: 1,
          max_users: maxUsers
        }),
      })

      if (!response.ok) {
        throw new Error('网络请求失败')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法读取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              switch (data.type) {
                case 'start':
                case 'platform':
                case 'progress':
                  setStreamingStatus(prev => ({
                    ...prev,
                    message: data.message,
                    progress: data.progress || prev.progress,
                    stage: data.stage,
                    currentUser: data.current_user,
                    processedCount: data.processed_count,
                    totalCount: data.total_count
                  }))
                  break

                case 'user_completed':
                  if (data.user_data) {
                    setStreamingData(prev => [...prev, data.user_data])
                  }
                  setStreamingStatus(prev => ({
                    ...prev,
                    message: data.message,
                    progress: data.progress || prev.progress,
                    currentUser: data.current_user,
                    processedCount: data.processed_count,
                    totalCount: data.total_count
                  }))
                  break

                case 'complete':
                  setStreamingData(data.data || [])
                  setStreamingStatus({
                    isStreaming: false,
                    progress: 100,
                    message: data.message
                  })
                  break

                case 'error':
                  setError(data.message)
                  setStreamingStatus({
                    isStreaming: false,
                    progress: 0,
                    message: ''
                  })
                  break
              }
            } catch (e) {
              console.error('解析数据时出错:', e)
            }
          }
        }
      }
    } catch (err) {
      console.error('流式爬取错误:', err)
      setError('网络错误，请稍后重试')
      setStreamingStatus({
        isStreaming: false,
        progress: 0,
        message: ''
      })
    }
  }



  const handleUserClick = (profileUrl: string) => {
    window.open(profileUrl, '_blank', 'noopener,noreferrer')
  }

  // CSV生成和下载函数
  const generateCSV = (data: UserData[]) => {
    const headers = [
      'username', 'display_name', 'bio', 'avatar_url', 'profile_url',
      'platform', 'type', 'follower_count', 'following_count',
      'company', 'location', 'website', 'twitter', 'email',
      'public_repos', 'scraped_at'
    ]

    const csvContent = [
      headers.join(','),
      ...data.map(user => headers.map(header => {
        const value = user[header as keyof UserData]
        // 处理包含逗号或引号的值
        if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
          return `"${value.replace(/"/g, '""')}"`
        }
        return value || ''
      }).join(','))
    ].join('\n')

    return csvContent
  }

  const downloadCSV = (csvContent: string, filename: string) => {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', filename)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }
  }

  const detectedPlatform = detectPlatform(url)

  // 排序后的数据
  const sortedStreamingData = useMemo(() => {
    if (streamingData.length === 0) return []

    return [...streamingData].sort((a, b) => {
      let aValue: any = a[sortField]
      let bValue: any = b[sortField]

      // 处理数值类型
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'desc' ? bValue - aValue : aValue - bValue
      }

      // 处理字符串类型
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        aValue = aValue.toLowerCase()
        bValue = bValue.toLowerCase()
        return sortOrder === 'desc'
          ? bValue.localeCompare(aValue)
          : aValue.localeCompare(bValue)
      }

      // 处理日期类型
      if (sortField === 'scraped_at') {
        const aDate = new Date(aValue).getTime()
        const bDate = new Date(bValue).getTime()
        return sortOrder === 'desc' ? bDate - aDate : aDate - bDate
      }

      return 0
    })
  }, [streamingData, sortField, sortOrder])

  // 处理排序
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')
    } else {
      setSortField(field)
      setSortOrder('desc')
    }
  }

    // 获取排序图标
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-4 h-4 text-gray-400" />
    }
    return sortOrder === 'desc'
      ? <ArrowDown className="w-4 h-4 text-blue-400" />
      : <ArrowUp className="w-4 h-4 text-blue-400" />
  }

  // 排序表头组件
  const SortableTableHead = ({ field, children, className }: {
    field: SortField,
    children: React.ReactNode,
    className?: string
  }) => (
    <TableHead
      className={`cursor-pointer hover:bg-white/5 transition-colors ${className}`}
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-2">
        {children}
        {getSortIcon(field)}
      </div>
    </TableHead>
  )

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-900 via-blue-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-linear-to-r from-blue-500 to-purple-600 mb-6">
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
                className={`w-full px-6 py-4 text-lg bg-white/10 backdrop-blur-xs border border-white/20 rounded-2xl text-white placeholder-blue-200 focus:outline-hidden focus:ring-2 focus:ring-blue-400 focus:border-transparent ${
                  detectedPlatform ? 'pr-48' : 'pr-32'
                }`}
                disabled={streamingStatus.isStreaming}
              />
              {detectedPlatform && (
                <div className="absolute right-32 top-1/2 transform -translate-y-1/2 px-3 py-1 bg-blue-500/20 text-blue-200 text-sm rounded-lg flex items-center gap-2">
                  {detectedPlatform === 'GitHub' && <Github className="w-4 h-4" />}
                  {detectedPlatform === 'Twitter/X' && <Twitter className="w-4 h-4" />}
                  {detectedPlatform === 'Product Hunt' && <Star className="w-4 h-4" />}
                  {detectedPlatform === 'Hacker News' && <Search className="w-4 h-4" />}
                  {(detectedPlatform === 'Weibo' || detectedPlatform === 'YouTube' || detectedPlatform === 'Reddit' || detectedPlatform === 'Medium' || detectedPlatform === 'Bilibili') && <Globe className="w-4 h-4" />}
                  <span>{detectedPlatform}</span>
                </div>
              )}
              <button
                type="submit"
                disabled={streamingStatus.isStreaming || !url.trim()}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-linear-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 text-sm font-medium"
              >
                {streamingStatus.isStreaming ? '爬取中...' : '开始爬取'}
              </button>
            </div>
          </form>

          {/* 设置选项 */}
          <div className="mt-6 bg-white/10 backdrop-blur-xs border border-white/20 rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <label className="text-white font-medium">最大用户数:</label>
                <select
                  value={maxUsers}
                  onChange={(e) => setMaxUsers(Number(e.target.value))}
                  disabled={streamingStatus.isStreaming}
                  className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-hidden focus:ring-2 focus:ring-blue-400 disabled:opacity-50"
                  style={{ colorScheme: 'dark' }}
                >
                  <option value={5} className="bg-slate-800 text-white">5 用户</option>
                  <option value={10} className="bg-slate-800 text-white">10 用户</option>
                  <option value={20} className="bg-slate-800 text-white">20 用户</option>
                  <option value={50} className="bg-slate-800 text-white">50 用户</option>
                  <option value={100} className="bg-slate-800 text-white">100 用户</option>
                </select>
              </div>

              {/* 导出按钮 */}
              {streamingData.length > 0 && (
                <button
                  onClick={() => {
                    const csvContent = generateCSV(sortedStreamingData)
                    downloadCSV(csvContent, `follownet_${detectedPlatform || 'data'}_sorted_by_${sortField}_${sortOrder}_${new Date().toISOString().split('T')[0]}.csv`)
                  }}
                  disabled={streamingStatus.isStreaming}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                >
                  <Download className="w-4 h-4" />
                  导出CSV ({streamingData.length} 用户)
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-200">
              {error}
            </div>
          )}
        </div>

                {/* 实时爬取显示区域 */}
        {(streamingStatus.isStreaming || streamingData.length > 0) && (
          <div className="max-w-7xl mx-auto mb-8">
            {/* 进度条显示 */}
            {streamingStatus.isStreaming && (
              <div className="bg-white/10 backdrop-blur-xs border border-white/20 rounded-2xl p-6 mb-6">
                <div className="flex items-center gap-4 mb-4">
                  <div className="animate-spin w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  <h2 className="text-xl font-semibold text-white">实时爬取中</h2>
                </div>

                <div className="mb-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-blue-200 text-sm">
                      {streamingStatus.stage && `阶段 ${streamingStatus.stage}: `}
                      {streamingStatus.message}
                      {streamingStatus.currentUser && ` - 当前用户: ${streamingStatus.currentUser}`}
                    </span>
                    <span className="text-blue-400 font-medium text-sm">{Math.round(streamingStatus.progress)}%</span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-3">
                    <div
                      className="bg-linear-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${streamingStatus.progress}%` }}
                    ></div>
                  </div>
                </div>

                {streamingStatus.processedCount !== undefined && streamingStatus.totalCount !== undefined && (
                  <div className="text-sm text-blue-200">
                    已处理: <span className="text-blue-400 font-medium">{streamingStatus.processedCount}/{streamingStatus.totalCount}</span> 用户
                    {streamingData.length > 0 && (
                      <span className="ml-4">已获取详细信息: <span className="text-green-400 font-medium">{streamingData.length}</span> 用户</span>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* 实时用户数据显示 */}
            {streamingData.length > 0 && (
              <>
                <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 mb-6">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-semibold text-white mb-2">
                        爬取结果 (<span className="text-blue-400">{streamingData.length}</span> 用户)
                        {streamingStatus.isStreaming && <span className="text-green-400 ml-2 animate-pulse">持续更新中...</span>}
                        {!streamingStatus.isStreaming && <span className="text-green-400 ml-2">✓ 完成</span>}
                      </h2>
                      {!streamingStatus.isStreaming && (
                        <p className="text-blue-300 text-sm">
                          当前排序: {sortField === 'follower_count' && '关注者数量'}
                          {sortField === 'following_count' && '关注中数量'}
                          {sortField === 'public_repos' && '仓库数量'}
                          {sortField === 'scraped_at' && '爬取时间'}
                          {sortField === 'username' && '用户名'}
                          <span className="ml-1">
                            ({sortOrder === 'desc' ? '从高到低' : '从低到高'})
                          </span>
                        </p>
                      )}
                    </div>


                  </div>
                </div>

                                                {/* 用户数据表格 */}
                <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <Table className="min-w-[800px]">
                      <TableHeader>
                        <TableRow className="border-white/20 hover:bg-white/5">
                          <TableHead className="text-blue-200 font-medium">头像</TableHead>
                          <SortableTableHead field="username" className="text-blue-200 font-medium">
                            用户信息
                          </SortableTableHead>
                          <TableHead className="text-blue-200 font-medium">简介</TableHead>
                          <SortableTableHead field="follower_count" className="text-blue-200 font-medium text-right">
                            关注者
                          </SortableTableHead>
                          <SortableTableHead field="following_count" className="text-blue-200 font-medium text-right">
                            关注中
                          </SortableTableHead>
                          <SortableTableHead field="public_repos" className="text-blue-200 font-medium text-right">
                            仓库
                          </SortableTableHead>
                          <TableHead className="text-blue-200 font-medium">位置/公司</TableHead>
                          <TableHead className="text-blue-200 font-medium">操作</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {sortedStreamingData.map((user, index) => (
                          <TableRow
                            key={`${user.username}-${index}`}
                            className="border-white/20 hover:bg-white/5 cursor-pointer animate-fade-in"
                            onClick={() => handleUserClick(user.profile_url)}
                            style={{
                              animationDelay: `${(index % 5) * 100}ms`
                            }}
                          >
                            {/* 头像 */}
                            <TableCell>
                              <img
                                src={user.avatar_url}
                                alt={user.username}
                                className="w-12 h-12 rounded-full border-2 border-white/20"
                                onError={(e) => {
                                  e.currentTarget.src = `https://ui-avatars.com/api/?name=${user.username}&background=random`
                                }}
                              />
                            </TableCell>

                            {/* 用户信息 */}
                            <TableCell>
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold text-white truncate max-w-[150px]">
                                    {user.display_name || user.username}
                                  </span>
                                  {index < 3 && streamingStatus.isStreaming && (
                                    <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full animate-pulse">
                                      新增
                                    </span>
                                  )}
                                </div>
                                <div className={`text-sm ${
                                  sortField === 'username' ? 'text-blue-300 font-medium' : 'text-blue-200'
                                }`}>
                                  @{user.username}
                                </div>
                              </div>
                            </TableCell>

                            {/* 简介 */}
                            <TableCell>
                              <div className="text-blue-100 text-sm max-w-[200px] truncate">
                                {user.bio || '-'}
                              </div>
                            </TableCell>

                            {/* 关注者数 */}
                            <TableCell className="text-right">
                              <div className={`flex items-center justify-end gap-1 ${
                                sortField === 'follower_count' ? 'text-blue-300 font-medium' : 'text-blue-200'
                              }`}>
                                <Users className="w-4 h-4 text-blue-400" />
                                <span>{user.follower_count.toLocaleString()}</span>
                              </div>
                            </TableCell>

                            {/* 关注中数 */}
                            <TableCell className="text-right">
                              <div className={`flex items-center justify-end gap-1 ${
                                sortField === 'following_count' ? 'text-blue-300 font-medium' : 'text-blue-200'
                              }`}>
                                <Users className="w-4 h-4 text-green-400" />
                                <span>{user.following_count.toLocaleString()}</span>
                              </div>
                            </TableCell>

                            {/* 仓库数 */}
                            <TableCell className="text-right">
                              <div className={`flex items-center justify-end gap-1 ${
                                sortField === 'public_repos' ? 'text-blue-300 font-medium' : 'text-blue-200'
                              }`}>
                                <Github className="w-4 h-4 text-gray-400" />
                                <span>{user.public_repos || 0}</span>
                              </div>
                            </TableCell>

                            {/* 位置/公司 */}
                            <TableCell>
                              <div className="space-y-1 text-sm">
                                {user.location && (
                                  <div className="flex items-center gap-1 text-blue-200">
                                    <MapPin className="w-3 h-3 text-orange-400" />
                                    <span className="truncate max-w-[100px]">{user.location}</span>
                                  </div>
                                )}
                                {user.company && (
                                  <div className="flex items-center gap-1 text-blue-200">
                                    <Building className="w-3 h-3 text-purple-400" />
                                    <span className="truncate max-w-[100px]">{user.company}</span>
                                  </div>
                                )}
                                {!user.location && !user.company && (
                                  <span className="text-gray-500">-</span>
                                )}
                              </div>
                            </TableCell>

                            {/* 操作 */}
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleUserClick(user.profile_url)
                                  }}
                                  className="p-1 rounded hover:bg-white/10 transition-colors"
                                  title="访问用户主页"
                                >
                                  <ExternalLink className="w-4 h-4 text-blue-400" />
                                </button>
                                {user.email && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      window.location.href = `mailto:${user.email}`
                                    }}
                                    className="p-1 rounded hover:bg-white/10 transition-colors"
                                    title="发送邮件"
                                  >
                                    <Mail className="w-4 h-4 text-red-400" />
                                  </button>
                                )}
                                {user.website && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      window.open(user.website, '_blank')
                                    }}
                                    className="p-1 rounded hover:bg-white/10 transition-colors"
                                    title="访问网站"
                                  >
                                    <Globe className="w-4 h-4 text-teal-400" />
                                  </button>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </>
            )}
          </div>
        )}



        {/* 平台展示 - 只在没有结果且不在爬取时显示 */}
        {!streamingStatus.isStreaming && streamingData.length === 0 && (
          <div className="max-w-6xl mx-auto">
            <h3 className="text-2xl font-bold text-white text-center mb-8">支持的平台</h3>
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="bg-linear-to-br from-gray-700 to-gray-900 p-8 rounded-3xl shadow-2xl hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-6 mx-auto">
                  <Github className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white text-center mb-3">GitHub</h3>
                <p className="text-white/80 text-center text-sm">Repositories Star 用户 & 用户关注者</p>
              </div>

              <div className="bg-linear-to-br from-blue-400 to-blue-600 p-8 rounded-3xl shadow-2xl hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-6 mx-auto">
                  <Twitter className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white text-center mb-3">Twitter/X</h3>
                <p className="text-white/80 text-center text-sm">用户关注者 & 关注列表</p>
              </div>

              <div className="bg-linear-to-br from-orange-400 to-orange-600 p-8 rounded-3xl shadow-2xl hover:scale-105 transition-all duration-300">
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
                <div key={platform.name} className={`bg-linear-to-br ${platform.color} p-6 rounded-2xl shadow-lg hover:scale-105 transition-all duration-300`}>
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
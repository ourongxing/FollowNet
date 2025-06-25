'use client'

import { useState, useMemo, useRef } from 'react'
import { UserData, SortField, SortOrder, StreamingStatus } from "@/types"
import { Header } from "@/components/Header"
import { SearchForm } from "@/components/SearchForm"
import { StreamingProgress } from "@/components/StreamingProgress"
import { UserTable } from "@/components/UserTable"
import { ThemeToggle } from "@/components/ThemeToggle"
import { AlertTriangle, CheckCircle, Clock, Users } from 'lucide-react'
import { Badge } from "@/components/ui/badge"

export default function Home() {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [maxUsers, setMaxUsers] = useState(10)
  const [streamingData, setStreamingData] = useState<UserData[]>([])
  const [sortField, setSortField] = useState<SortField>('follower_count')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [streamingStatus, setStreamingStatus] = useState<StreamingStatus>({
    isStreaming: false,
    progress: 0,
    message: ''
  })

  // 用于控制流式处理的引用
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null)

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

      readerRef.current = reader
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
                    totalCount: data.total_count,
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
                    totalCount: data.total_count,
                  }))
                  break

                case 'stopped':
                  setStreamingStatus(prev => ({
                    ...prev,
                    isStreaming: false,
                    message: data.message,
                  }))
                  break

                case 'complete':
                  setStreamingData(data.data || [])
                  setStreamingStatus({
                    isStreaming: false,
                    progress: 100,
                    message: data.message,
                  })
                  break

                case 'error':
                  setError(data.message)
                  setStreamingStatus({
                    isStreaming: false,
                    progress: 0,
                    message: '',
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
      if (err instanceof Error && err.name === 'AbortError') {
        setStreamingStatus({
          isStreaming: false,
          progress: 0,
          message: '爬取已停止',
        })
      } else {
        setError('网络错误，请稍后重试')
        setStreamingStatus({
          isStreaming: false,
          progress: 0,
          message: '',
        })
      }
    } finally {
      // 清理资源
      readerRef.current = null
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

  const handleExportCSV = () => {
    const csvContent = generateCSV(streamingData)
    const detectedPlatform = detectPlatform(url)
    downloadCSV(csvContent, `follownet_${detectedPlatform || 'data'}_sorted_by_${sortField}_${sortOrder}_${new Date().toISOString().split('T')[0]}.csv`)
  }

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

  const showDataSection = streamingStatus.isStreaming || streamingData.length > 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-100 to-purple-50 dark:from-slate-900/20 dark:via-blue-900/20 dark:to-slate-900/20 transition-colors duration-300">
      {/* 主题切换按钮 */}
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      <div className="container mx-auto px-6 py-12">
        {/* Header */}
        <Header />

        {/* 搜索表单 */}
        <SearchForm
          url={url}
          setUrl={setUrl}
          maxUsers={maxUsers}
          setMaxUsers={setMaxUsers}
          onSubmit={handleSubmit}
          isStreaming={streamingStatus.isStreaming}
        />

        {/* 错误信息 */}
        {error && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-white/80 dark:bg-white/10 backdrop-blur-sm border border-gray-300 dark:border-white/20 rounded-2xl overflow-hidden">
              <div className="flex items-center gap-3 p-4 bg-red-50/50 dark:bg-red-900/10">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <div>
                  <div className="font-medium text-red-800 dark:text-red-300">
                    爬取失败
                  </div>
                  <div className="text-sm text-red-600 dark:text-red-400">
                    {error}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 实时爬取显示区域 */}
        {showDataSection && (
          <div className="max-w-7xl mx-auto mb-16">
            {/* 进度条显示 */}
            <StreamingProgress
              streamingStatus={streamingStatus}
              streamingDataLength={streamingData.length}
            />

            {/* 实时用户数据显示 */}
            {streamingData.length > 0 && (
              <UserTable
                users={sortedStreamingData}
                sortField={sortField}
                sortOrder={sortOrder}
                onSort={handleSort}
                onUserClick={handleUserClick}
                isStreaming={streamingStatus.isStreaming}
                onExportCSV={handleExportCSV}
              />
            )}
          </div>
        )}

        {/* 欢迎信息 - 当没有数据且未在爬取时显示 */}
        {!showDataSection && (
          <div className="max-w-4xl mx-auto mb-16">
            <div className="bg-white/80 dark:bg-white/10 backdrop-blur-sm border border-gray-300 dark:border-white/20 rounded-2xl overflow-hidden">
              {/* 工具栏 */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-white/20 bg-gray-50/50 dark:bg-white/5">
                <div className="flex items-center gap-3">
                  <Users className="w-5 h-5 text-blue-400" />
                  <span className="font-medium text-gray-700 dark:text-blue-200">开始您的第一次爬取</span>
                </div>
                <Badge className="bg-blue-500/20 text-blue-300 border-blue-200 dark:border-blue-800">
                  支持多平台
                </Badge>
              </div>

              {/* 内容区域 */}
              <div className="p-8 text-center">
                <div className="mb-6">
                  <div className="w-16 h-16 mx-auto mb-4 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <Users className="w-8 h-8 text-blue-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-blue-100 mb-2">
                    欢迎使用 FollowNet
                  </h3>
                  <p className="text-gray-600 dark:text-blue-300 max-w-md mx-auto">
                    输入平台URL开始爬取用户数据。支持GitHub、Twitter、Product Hunt等多个平台。
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
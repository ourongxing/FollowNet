import React from 'react'
import { Github, Twitter, Star, Search, Globe } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"

interface SearchFormProps {
  url: string
  setUrl: (url: string) => void
  maxUsers: number
  setMaxUsers: (count: number) => void
  onSubmit: (e: React.FormEvent) => void
  isStreaming: boolean
}

export function SearchForm({
  url,
  setUrl,
  maxUsers,
  setMaxUsers,
  onSubmit,
  isStreaming
}: SearchFormProps) {
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

  const detectedPlatform = detectPlatform(url)

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'GitHub': return <Github className="w-4 h-4" />
      case 'Twitter/X': return <Twitter className="w-4 h-4" />
      case 'Product Hunt': return <Star className="w-4 h-4" />
      case 'Hacker News': return <Search className="w-4 h-4" />
      default: return <Globe className="w-4 h-4" />
    }
  }

  return (
    <div className="max-w-4xl mx-auto mb-12">
      <div className="overflow-hidden bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm rounded-lg">
        <form onSubmit={onSubmit}>
          <div className="relative">
            {/* URL输入框 */}
            <Input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="输入要爬取的URL，例如：https://github.com/username"
              className="w-full h-14 pl-24 pr-32 text-base bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:focus:border-blue-400"
              disabled={isStreaming}
            />

            {/* 绝对定位的用户数选择器 */}
            <div className="absolute left-3 top-1/2 -translate-y-1/2">
              <Select
                value={maxUsers.toString()}
                onValueChange={(value) => setMaxUsers(Number(value))}
                disabled={isStreaming}
              >
                <SelectTrigger className="w-16 h-8 text-sm border-0 bg-transparent p-0 font-medium flex items-center justify-center">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5</SelectItem>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="1000">1000</SelectItem>
                  <SelectItem value="10000">10000</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 平台检测标签 */}
            {detectedPlatform && (
              <Badge
                variant="secondary"
                className="absolute right-36 top-1/2 -translate-y-1/2 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700"
              >
                {getPlatformIcon(detectedPlatform)}
                <span className="ml-1.5">{detectedPlatform}</span>
              </Badge>
            )}

            {/* 绝对定位的提交按钮 */}
            <Button
              type="submit"
              disabled={isStreaming || !url.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 h-8 px-4 text-sm bg-blue-600 hover:bg-blue-700"
            >
              {isStreaming ? '爬取中...' : '开始爬取'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
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
      <div className="bg-white/80 dark:bg-white/10 backdrop-blur-sm border border-gray-300 dark:border-white/20 rounded-2xl overflow-hidden">
        <form onSubmit={onSubmit}>
          {/* 主要输入区域 */}
          <div className="p-6">
            <div className="grid grid-cols-12 gap-4 items-center">
              {/* 用户数选择器 */}
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-700 dark:text-blue-200 mb-2">
                  用户数量
                </label>
                <Select
                  value={maxUsers.toString()}
                  onValueChange={(value) => setMaxUsers(Number(value))}
                  disabled={isStreaming}
                >
                  <SelectTrigger className="w-full h-10 text-sm border-gray-300 dark:border-white/20 bg-white/50 dark:bg-white/5 text-gray-800 dark:text-blue-200 hover:bg-white/70 dark:hover:bg-white/10 transition-colors">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm border-gray-300 dark:border-white/20">
                    <SelectItem value="5" className="text-gray-800 dark:text-blue-200 hover:bg-gray-50 dark:hover:bg-white/10">5</SelectItem>
                    <SelectItem value="10" className="text-gray-800 dark:text-blue-200 hover:bg-gray-50 dark:hover:bg-white/10">10</SelectItem>
                    <SelectItem value="20" className="text-gray-800 dark:text-blue-200 hover:bg-gray-50 dark:hover:bg-white/10">20</SelectItem>
                    <SelectItem value="50" className="text-gray-800 dark:text-blue-200 hover:bg-gray-50 dark:hover:bg-white/10">50</SelectItem>
                    <SelectItem value="100" className="text-gray-800 dark:text-blue-200 hover:bg-gray-50 dark:hover:bg-white/10">100</SelectItem>
                    <SelectItem value="1000000" className="text-gray-800 dark:text-blue-200 hover:bg-gray-50 dark:hover:bg-white/10">不限</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* URL输入框 */}
              <div className="col-span-8">
                <label className="block text-xs font-medium text-gray-700 dark:text-blue-200 mb-2">
                  平台URL
                </label>
                <div className="relative">
                  <Input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="例如：https://github.com/username 或 https://github.com/owner/repo"
                    className="w-full h-10 pr-24 text-sm border-gray-300 dark:border-white/20 bg-white/50 dark:bg-white/5 text-gray-800 dark:text-blue-200 placeholder:text-gray-500 dark:placeholder:text-blue-300/60 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:focus:border-blue-400 hover:bg-white/70 dark:hover:bg-white/10 transition-colors"
                    disabled={isStreaming}
                  />

                  {/* 平台检测标签 */}
                  {detectedPlatform && (
                    <div className="absolute right-2 top-1/2 -translate-y-1/2">
                      <Badge
                        variant="secondary"
                        className="bg-blue-500/30 dark:bg-blue-500/20 border-blue-200 dark:border-blue-800 text-xs"
                      >
                        {getPlatformIcon(detectedPlatform)}
                        <span className="ml-1">{detectedPlatform}</span>
                      </Badge>
                    </div>
                  )}
                </div>
              </div>

              {/* 提交按钮 */}
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-700 dark:text-blue-200 mb-2">
                  操作
                </label>
                <Button
                  type="submit"
                  disabled={isStreaming || !url.trim()}
                  className="w-full h-10 text-sm bg-blue-400 hover:bg-blue-500 dark:bg-blue-500/20 dark:hover:bg-blue-500/30 text-white dark:text-blue-200 border-0 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isStreaming ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>爬取中...</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <span>开始爬取</span>
                    </div>
                  )}
                </Button>
              </div>
            </div>

            {/* 平台支持提示 */}
            <div className="mt-4 p-3 bg-gray-50/50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
              <div className="text-xs text-gray-600 dark:text-blue-300/80">
                <span className="font-medium">支持的平台：</span>
                <span className="ml-2">GitHub (用户/仓库)、Twitter/X、Product Hunt、Weibo、Hacker News、YouTube、Reddit、Medium、Bilibili</span>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
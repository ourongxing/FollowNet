import React from 'react'
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { StreamingStatus } from "@/types"
import { Activity, Users, User, Loader2 } from 'lucide-react'

interface StreamingProgressProps {
  streamingStatus: StreamingStatus
  streamingDataLength: number
}

export function StreamingProgress({ streamingStatus, streamingDataLength }: StreamingProgressProps) {
  if (!streamingStatus.isStreaming) return null

  return (
    <div className="max-w-4xl mx-auto mb-8">
      <div className="bg-white/80 dark:bg-white/10 backdrop-blur-sm border border-gray-300 dark:border-white/20 rounded-2xl overflow-hidden">
        {/* 工具栏 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-white/20 bg-gray-50/50 dark:bg-white/5">
          <div className="flex items-center gap-3">
            <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <span className="font-medium text-gray-700 dark:text-blue-200">实时爬取进行中</span>
            {streamingStatus.stage && (
              <Badge variant="outline" className="text-xs text-blue-600 dark:text-blue-300 border-blue-400 dark:border-blue-600">
                阶段 {streamingStatus.stage}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* 进度百分比 */}
            <Badge className="bg-blue-500/20 text-blue-300 border-blue-200 dark:border-blue-800">
              {Math.round(streamingStatus.progress)}%
            </Badge>

            {/* 已获取用户数 */}
            {streamingDataLength > 0 && (
              <Badge className="bg-green-500/20 text-green-300 border-green-200 dark:border-green-800">
                已获取 {streamingDataLength} 用户
              </Badge>
            )}
          </div>
        </div>

        {/* 主要内容区域 */}
        <div className="p-6">
          {/* 进度条 */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-blue-200">
                爬取进度
              </span>
              <span className="text-sm text-gray-600 dark:text-blue-300">
                {Math.round(streamingStatus.progress)}%
              </span>
            </div>
            <Progress
              value={streamingStatus.progress}
              className="w-full h-3 bg-gray-200 dark:bg-white/10"
            />
          </div>

          {/* 统计信息网格 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 处理进度 */}
            {streamingStatus.processedCount !== undefined && streamingStatus.totalCount !== undefined && (
              <div className="p-3 bg-gray-50/50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="w-4 h-4 text-blue-400" />
                  <span className="text-xs font-medium text-gray-700 dark:text-blue-200">处理进度</span>
                </div>
                <div className="text-lg font-semibold text-gray-800 dark:text-blue-100">
                  {streamingStatus.processedCount}/{streamingStatus.totalCount}
                </div>
                <div className="text-xs text-gray-600 dark:text-blue-300">
                  {streamingStatus.totalCount > 0 ? Math.round((streamingStatus.processedCount / streamingStatus.totalCount) * 100) : 0}% 完成
                </div>
              </div>
            )}

            {/* 已获取用户 */}
            {streamingDataLength > 0 && (
              <div className="p-3 bg-gray-50/50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                <div className="flex items-center gap-2 mb-1">
                  <Users className="w-4 h-4 text-green-400" />
                  <span className="text-xs font-medium text-gray-700 dark:text-blue-200">已获取用户</span>
                </div>
                <div className="text-lg font-semibold text-gray-800 dark:text-blue-100">
                  {streamingDataLength.toLocaleString()}
                </div>
                <div className="text-xs text-gray-600 dark:text-blue-300">
                  用户数据
                </div>
              </div>
            )}

            {/* 当前阶段 */}
            <div className="p-3 bg-gray-50/50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
              <div className="flex items-center gap-2 mb-1">
                <Loader2 className="w-4 h-4 text-orange-400 animate-spin" />
                <span className="text-xs font-medium text-gray-700 dark:text-blue-200">
                  {streamingStatus.stage ? `阶段 ${streamingStatus.stage}` : '状态'}
                </span>
              </div>
              <div className="text-sm font-medium text-gray-800 dark:text-blue-100 truncate">
                {streamingStatus.message || '正在处理...'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
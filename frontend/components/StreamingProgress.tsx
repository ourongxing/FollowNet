import React from 'react'
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { StreamingStatus, StreamingControls } from "@/types"
import { Pause, Play, Square, Loader2 } from "lucide-react"

interface StreamingProgressProps {
  streamingStatus: StreamingStatus
  streamingDataLength: number
  controls?: StreamingControls
}

export function StreamingProgress({ streamingStatus, streamingDataLength, controls }: StreamingProgressProps) {
  if (!streamingStatus.isStreaming) return null

  const getStatusInfo = () => {
    switch (streamingStatus.controlState) {
      case 'paused':
        return {
          label: '已暂停',
          color: 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300',
          icon: <Pause className="w-4 h-4" />
        }
      case 'stopping':
        return {
          label: '正在停止',
          color: 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300',
          icon: <Loader2 className="w-4 h-4 animate-spin" />
        }
      case 'stopped':
        return {
          label: '已停止',
          color: 'bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300',
          icon: <Square className="w-4 h-4" />
        }
      default:
        return {
          label: '实时爬取中',
          color: 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300',
          icon: <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        }
    }
  }

  const statusInfo = getStatusInfo()

  return (
    <div className="max-w-4xl mx-auto mb-8">
      <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm rounded-lg border border-slate-200 dark:border-slate-700 p-4">
        {/* 头部状态和控制按钮 */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            {statusInfo.icon}
            <span className="font-medium text-slate-800 dark:text-slate-200">{statusInfo.label}</span>
            {streamingStatus.stage && (
              <Badge variant="outline" className="text-xs text-blue-600 dark:text-blue-300 border-blue-400">
                阶段 {streamingStatus.stage}
              </Badge>
            )}
          </div>

          {/* 控制按钮组 */}
          <div className="flex items-center gap-2">
            <Badge className={statusInfo.color}>
              {Math.round(streamingStatus.progress)}%
            </Badge>

            {controls && (
              <div className="flex items-center gap-1 ml-2">
                {/* 暂停/继续按钮 */}
                {streamingStatus.controlState === 'paused' ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={controls.onResume}
                    disabled={!controls.canResume}
                    className="h-8 px-3 text-xs"
                  >
                    <Play className="w-3 h-3 mr-1" />
                    继续
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={controls.onPause}
                    disabled={!controls.canPause || streamingStatus.controlState === 'stopping'}
                    className="h-8 px-3 text-xs"
                  >
                    <Pause className="w-3 h-3 mr-1" />
                    暂停
                  </Button>
                )}

                {/* 停止按钮 */}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={controls.onStop}
                  disabled={!controls.canStop || streamingStatus.controlState === 'stopping'}
                  className="h-8 px-3 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-900/20"
                >
                  {streamingStatus.controlState === 'stopping' ? (
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  ) : (
                    <Square className="w-3 h-3 mr-1" />
                  )}
                  停止
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* 进度条 */}
        <div className="mb-3">
          <Progress
            value={streamingStatus.progress}
            className="w-full h-2 bg-slate-200 dark:bg-slate-700"
          />
        </div>

        {/* 底部信息行 */}
        <div className="flex items-center justify-between text-sm">
          {/* 左侧统计信息 */}
          <div className="flex items-center gap-4 text-slate-600 dark:text-slate-400">
            {streamingStatus.processedCount !== undefined && streamingStatus.totalCount !== undefined && (
              <span>
                已处理: <span className="text-blue-600 dark:text-blue-400 font-medium">
                  {streamingStatus.processedCount}/{streamingStatus.totalCount}
                </span>
              </span>
            )}
            {streamingDataLength > 0 && (
              <span>
                已获取: <span className="text-green-600 dark:text-green-400 font-medium">
                  {streamingDataLength}
                </span> 用户
              </span>
            )}
            <span className="text-slate-500 dark:text-slate-400">
              {streamingStatus.message}
            </span>
          </div>

          {/* 右侧当前用户信息 */}
          {streamingStatus.currentUser && streamingStatus.controlState === 'running' && (
            <div className="flex items-center gap-2">
              <span className="text-slate-600 dark:text-slate-400">正在爬取:</span>
              <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 rounded px-2 py-1">
                <Avatar className="w-5 h-5">
                  <AvatarFallback className="bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 text-xs">
                    {streamingStatus.currentUser.slice(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  {streamingStatus.currentUser}
                </span>
                <div className="animate-pulse w-1.5 h-1.5 bg-green-500 rounded-full"></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
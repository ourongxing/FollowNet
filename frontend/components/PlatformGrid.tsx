import React from 'react'
import { Github, Twitter, Users } from 'lucide-react'
import { Card, CardContent } from "@/components/ui/card"

interface PlatformGridProps {
  show: boolean
}

export function PlatformGrid({ show }: PlatformGridProps) {
  if (!show) return null

  const mainPlatforms = [
    {
      name: 'GitHub',
      icon: Github,
      description: 'Repositories Star 用户 & 用户关注者',
      gradient: 'from-gray-700 to-gray-900'
    },
    {
      name: 'Twitter/X',
      icon: Twitter,
      description: '用户关注者 & 关注列表',
      gradient: 'from-blue-400 to-blue-600'
    },
    {
      name: 'Product Hunt',
      icon: Users,
      description: '产品投票者数据',
      gradient: 'from-orange-400 to-orange-600'
    }
  ]

  const otherPlatforms = [
    { name: 'Weibo', color: 'from-red-400 to-red-600' },
    { name: 'Hacker News', color: 'from-orange-500 to-yellow-500' },
    { name: 'YouTube', color: 'from-red-500 to-red-700' },
    { name: 'Reddit', color: 'from-orange-600 to-red-600' },
    { name: 'Medium', color: 'from-green-400 to-green-600' },
    { name: 'Bilibili', color: 'from-pink-400 to-pink-600' }
  ]

  return (
    <div className="max-w-6xl mx-auto">
            <h3 className="text-2xl font-bold text-gray-800 dark:text-white text-center mb-12">支持的平台</h3>

      {/* 主要平台 */}
      <div className="grid md:grid-cols-3 gap-8 mb-12">
        {mainPlatforms.map((platform) => {
          const IconComponent = platform.icon
          return (
            <Card
              key={platform.name}
              className={`bg-gradient-to-br ${platform.gradient} border-none shadow-2xl hover:scale-105 transition-all duration-300`}
            >
              <CardContent className="p-10 text-center">
                <div className="flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-6 mx-auto">
                  <IconComponent className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">{platform.name}</h3>
                <p className="text-white/80 text-sm">{platform.description}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 其他平台 */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
        {otherPlatforms.map((platform) => (
          <Card
            key={platform.name}
            className={`bg-gradient-to-br ${platform.color} border-none shadow-lg hover:scale-105 transition-all duration-300`}
          >
            <CardContent className="p-8">
              <h4 className="text-lg font-semibold text-white text-center">{platform.name}</h4>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
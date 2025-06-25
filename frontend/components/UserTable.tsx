import React from 'react'
import { Users, Github, MapPin, Building, ExternalLink, Mail, Globe, ArrowUpDown, ArrowUp, ArrowDown, Download } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { UserData, SortField, SortOrder } from "@/types"

interface UserTableProps {
  users: UserData[]
  sortField: SortField
  sortOrder: SortOrder
  onSort: (field: SortField) => void
  onUserClick: (profileUrl: string) => void
  isStreaming: boolean
  onExportCSV: () => void
}

export function UserTable({ users, sortField, sortOrder, onSort, onUserClick, isStreaming, onExportCSV }: UserTableProps) {
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-4 h-4 text-gray-400" />
    }
    return sortOrder === 'desc'
      ? <ArrowDown className="w-4 h-4 text-blue-400" />
      : <ArrowUp className="w-4 h-4 text-blue-400" />
  }

  const SortableTableHead = ({ field, children, className }: {
    field: SortField,
    children: React.ReactNode,
    className?: string
  }) => (
    <TableHead
      className={`cursor-pointer hover:bg-white/5 transition-colors ${className}`}
      onClick={() => onSort(field)}
    >
      <div className={`flex items-center gap-2 ${className?.includes('text-center') ? 'justify-center' : ''}`}>
        {children}
        {getSortIcon(field)}
      </div>
    </TableHead>
  )

  return (
            <div className="bg-white/80 dark:bg-white/10 backdrop-blur-sm border border-gray-300 dark:border-white/20 rounded-2xl overflow-hidden">
      {/* 工具栏 */}
      {users.length > 0 && (
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-white/20 bg-gray-50/50 dark:bg-white/5">
          <div className="text-sm text-gray-700 dark:text-blue-200">
            共 <span className="font-semibold text-gray-900 dark:text-white">{users.length}</span> 个用户
          </div>
          <Button
            onClick={onExportCSV}
            disabled={isStreaming}
            size="sm"
            variant="outline"
            className="h-8 text-sm border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/20"
          >
            <Download className="w-4 h-4 mr-2" />
            导出CSV ({users.length})
          </Button>
        </div>
      )}

      <div className="overflow-x-auto">
        <Table className="min-w-[800px]">
          <TableHeader>
            <TableRow className="border-gray-200 dark:border-white/20 hover:bg-gray-50 dark:hover:bg-white/5">
              <TableHead className="text-gray-800 dark:text-blue-200 font-medium text-center">头像</TableHead>
              <SortableTableHead field="username" className="text-gray-800 dark:text-blue-200 font-medium">
                用户信息
              </SortableTableHead>
              <TableHead className="text-gray-800 dark:text-blue-200 font-medium">简介</TableHead>
              <SortableTableHead field="follower_count" className="text-gray-800 dark:text-blue-200 font-medium text-center">
                关注者
              </SortableTableHead>
              <SortableTableHead field="following_count" className="text-gray-800 dark:text-blue-200 font-medium text-center">
                关注中
              </SortableTableHead>
              <SortableTableHead field="public_repos" className="text-gray-800 dark:text-blue-200 font-medium text-center">
                仓库
              </SortableTableHead>
              <TableHead className="text-gray-800 dark:text-blue-200 font-medium">位置/公司</TableHead>
              <TableHead className="text-gray-800 dark:text-blue-200 font-medium text-center">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user, index) => (
              <TableRow
                key={`${user.username}-${index}`}
                className="border-gray-200 dark:border-white/20 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer animate-fade-in"
                onClick={() => onUserClick(user.profile_url)}
                style={{
                  animationDelay: `${(index % 5) * 100}ms`
                }}
              >
                {/* 头像 */}
                <TableCell className="text-center">
                  <div className="flex justify-center">
                    <Avatar className="w-12 h-12 border-2 border-white/20">
                      <AvatarImage src={user.avatar_url} alt={user.username} />
                      <AvatarFallback className="bg-blue-500/20 text-blue-200">
                        {user.username.slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </div>
                </TableCell>

                {/* 用户信息 */}
                <TableCell>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 dark:text-white truncate max-w-[150px]">
                        {user.display_name || user.username}
                      </span>
                      {index < 3 && isStreaming && (
                        <Badge variant="secondary" className="bg-green-500/20 text-green-600 dark:text-green-400 animate-pulse">
                          新增
                        </Badge>
                      )}
                    </div>
                    <div className={`text-sm ${
                      sortField === 'username' ? 'text-blue-600 dark:text-blue-300 font-medium' : 'text-gray-600 dark:text-blue-200'
                    }`}>
                      @{user.username}
                    </div>
                  </div>
                </TableCell>

                {/* 简介 */}
                <TableCell>
                  <div className="text-gray-600 dark:text-blue-100 text-sm max-w-[200px] truncate">
                    {user.bio || '-'}
                  </div>
                </TableCell>

                {/* 关注者数 */}
                <TableCell className="text-center">
                  <div className={`flex items-center justify-center gap-1 ${
                    sortField === 'follower_count' ? 'text-blue-600 dark:text-blue-300 font-medium' : 'text-gray-700 dark:text-blue-200'
                  }`}>
                    <Users className="w-4 h-4 text-blue-500 dark:text-blue-400" />
                    <span>{user.follower_count.toLocaleString()}</span>
                  </div>
                </TableCell>

                {/* 关注中数 */}
                <TableCell className="text-center">
                  <div className={`flex items-center justify-center gap-1 ${
                    sortField === 'following_count' ? 'text-blue-600 dark:text-blue-300 font-medium' : 'text-gray-700 dark:text-blue-200'
                  }`}>
                    <Users className="w-4 h-4 text-green-500 dark:text-green-400" />
                    <span>{user.following_count.toLocaleString()}</span>
                  </div>
                </TableCell>

                {/* 仓库数 */}
                <TableCell className="text-center">
                  <div className={`flex items-center justify-center gap-1 ${
                    sortField === 'public_repos' ? 'text-blue-600 dark:text-blue-300 font-medium' : 'text-gray-700 dark:text-blue-200'
                  }`}>
                    <Github className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                    <span>{user.public_repos || 0}</span>
                  </div>
                </TableCell>

                {/* 位置/公司 */}
                <TableCell>
                  <div className="space-y-1 text-sm">
                    {user.location && (
                      <div className="flex items-center gap-1 text-gray-700 dark:text-blue-200">
                        <MapPin className="w-3 h-3 text-orange-500 dark:text-orange-400" />
                        <span className="truncate max-w-[100px]">{user.location}</span>
                      </div>
                    )}
                    {user.company && (
                      <div className="flex items-center gap-1 text-gray-700 dark:text-blue-200">
                        <Building className="w-3 h-3 text-purple-500 dark:text-purple-400" />
                        <span className="truncate max-w-[100px]">{user.company}</span>
                      </div>
                    )}
                    {!user.location && !user.company && (
                      <span className="text-gray-500 dark:text-gray-500">-</span>
                    )}
                  </div>
                </TableCell>

                {/* 操作 */}
                <TableCell className="text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        onUserClick(user.profile_url)
                      }}
                      className="p-1 h-8 w-8 hover:bg-gray-100 dark:hover:bg-white/10"
                      title="访问用户主页"
                    >
                      <ExternalLink className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    </Button>
                    {user.email && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          window.location.href = `mailto:${user.email}`
                        }}
                        className="p-1 h-8 w-8 hover:bg-gray-100 dark:hover:bg-white/10"
                        title="发送邮件"
                      >
                        <Mail className="w-4 h-4 text-red-600 dark:text-red-400" />
                      </Button>
                    )}
                    {user.website && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          window.open(user.website, '_blank')
                        }}
                        className="p-1 h-8 w-8 hover:bg-gray-100 dark:hover:bg-white/10"
                        title="访问网站"
                      >
                        <Globe className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
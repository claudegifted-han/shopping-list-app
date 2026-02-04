'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { Bell, AlertTriangle, BookOpen, DoorOpen, Info, Check, Trash2 } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { Notification, NotificationType } from '@/types/database'

const typeIcons: Record<NotificationType, React.ComponentType<{ className?: string }>> = {
  penalty: AlertTriangle,
  study: BookOpen,
  outing: DoorOpen,
  system: Info,
}

const typeLabels: Record<NotificationType, string> = {
  penalty: '벌점',
  study: '자습',
  outing: '외출',
  system: '시스템',
}

const typeColors: Record<NotificationType, string> = {
  penalty: 'text-red-500 bg-red-500/10',
  study: 'text-purple-500 bg-purple-500/10',
  outing: 'text-blue-500 bg-blue-500/10',
  system: 'text-gray-500 bg-gray-500/10',
}

export default function NotificationsPage() {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<NotificationType | 'all'>('all')

  const supabase = createClient()

  useEffect(() => {
    if (user) {
      fetchNotifications()
    }
  }, [user])

  const fetchNotifications = async () => {
    if (!user) return
    setLoading(true)

    try {
      const { data, error } = await supabase
        .from('notifications')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })

      if (error) throw error
      setNotifications(data || [])
    } catch (error) {
      console.error('Error fetching notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = async (notificationId: string) => {
    try {
      const { error } = await supabase
        .from('notifications')
        .update({ is_read: true, read_at: new Date().toISOString() })
        .eq('id', notificationId)

      if (error) throw error

      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
      )
    } catch (error) {
      console.error('Error marking notification as read:', error)
    }
  }

  const markAllAsRead = async () => {
    if (!user) return

    try {
      const { error } = await supabase
        .from('notifications')
        .update({ is_read: true, read_at: new Date().toISOString() })
        .eq('user_id', user.id)
        .eq('is_read', false)

      if (error) throw error

      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
    } catch (error) {
      console.error('Error marking all as read:', error)
    }
  }

  const filteredNotifications = notifications.filter(
    (n) => filter === 'all' || n.type === filter
  )

  const unreadCount = notifications.filter((n) => !n.is_read).length

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6" />
            알림
          </h1>
          {unreadCount > 0 && (
            <p className="text-foreground-secondary mt-1">
              읽지 않은 알림 {unreadCount}개
            </p>
          )}
        </div>
        {unreadCount > 0 && (
          <Button variant="default" size="sm" onClick={markAllAsRead}>
            <Check className="h-4 w-4 mr-2" />
            모두 읽음
          </Button>
        )}
      </div>

      {/* Filter */}
      <div className="flex gap-1 mb-6 overflow-x-auto pb-1">
        <Button
          variant={filter === 'all' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setFilter('all')}
        >
          전체
        </Button>
        {(Object.keys(typeLabels) as NotificationType[]).map((type) => (
          <Button
            key={type}
            variant={filter === type ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilter(type)}
          >
            {typeLabels[type]}
          </Button>
        ))}
      </div>

      {/* Notifications */}
      <div className="space-y-3">
        {loading ? (
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </CardContent>
          </Card>
        ) : filteredNotifications.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-foreground-secondary">
              <Bell className="h-12 w-12 mb-4 opacity-50" />
              <p>알림이 없습니다</p>
            </CardContent>
          </Card>
        ) : (
          filteredNotifications.map((notification) => {
            const Icon = typeIcons[notification.type]
            return (
              <Card
                key={notification.id}
                className={cn(
                  'transition-colors',
                  !notification.is_read && 'border-accent/50 bg-accent/5'
                )}
              >
                <CardContent className="p-4">
                  <div className="flex gap-4">
                    <div
                      className={cn(
                        'h-10 w-10 rounded-full flex items-center justify-center shrink-0',
                        typeColors[notification.type]
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className={cn('font-medium', !notification.is_read && 'text-accent')}>
                              {notification.title}
                            </p>
                            {!notification.is_read && (
                              <Badge className="bg-accent text-white text-xs">새로운</Badge>
                            )}
                          </div>
                          {notification.message && (
                            <p className="text-sm text-foreground-secondary mt-1">
                              {notification.message}
                            </p>
                          )}
                          <p className="text-xs text-foreground-secondary mt-2">
                            {format(new Date(notification.created_at), 'yyyy년 M월 d일 HH:mm', {
                              locale: ko,
                            })}
                          </p>
                        </div>
                        {!notification.is_read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => markAsRead(notification.id)}
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>

      {/* Info */}
      <p className="text-xs text-foreground-secondary text-center mt-8">
        {filteredNotifications.length}개의 알림
      </p>
    </div>
  )
}

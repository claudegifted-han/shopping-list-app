'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { Bell, AlertTriangle, BookOpen, DoorOpen, Info, Check } from 'lucide-react'
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

const typeColors: Record<NotificationType, string> = {
  penalty: 'text-red-500',
  study: 'text-purple-500',
  outing: 'text-blue-500',
  system: 'text-gray-500',
}

export function NotificationBell() {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const supabase = createClient()

  useEffect(() => {
    if (user) {
      fetchNotifications()

      // Subscribe to new notifications
      const channel = supabase
        .channel('notifications')
        .on(
          'postgres_changes',
          {
            event: 'INSERT',
            schema: 'public',
            table: 'notifications',
            filter: `user_id=eq.${user.id}`,
          },
          (payload) => {
            setNotifications((prev) => [payload.new as Notification, ...prev])
            setUnreadCount((prev) => prev + 1)
          }
        )
        .subscribe()

      return () => {
        supabase.removeChannel(channel)
      }
    }
  }, [user])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const fetchNotifications = async () => {
    if (!user) return

    try {
      const { data, error } = await supabase
        .from('notifications')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(10)

      if (error) throw error

      setNotifications(data || [])
      setUnreadCount(data?.filter((n) => !n.is_read).length || 0)
    } catch (error) {
      console.error('Error fetching notifications:', error)
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
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Error marking notification as read:', error)
    }
  }

  const markAllAsRead = async () => {
    if (!user || loading) return
    setLoading(true)

    try {
      const { error } = await supabase
        .from('notifications')
        .update({ is_read: true, read_at: new Date().toISOString() })
        .eq('user_id', user.id)
        .eq('is_read', false)

      if (error) throw error

      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch (error) {
      console.error('Error marking all as read:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="ghost"
        size="sm"
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center bg-red-500 text-white text-xs">
            {unreadCount > 9 ? '9+' : unreadCount}
          </Badge>
        )}
      </Button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 rounded-lg border border-border bg-background shadow-lg z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-border">
            <h3 className="font-medium">알림</h3>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={markAllAsRead}
                disabled={loading}
              >
                <Check className="h-3 w-3 mr-1" />
                모두 읽음
              </Button>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-foreground-secondary">
                <Bell className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">알림이 없습니다</p>
              </div>
            ) : (
              notifications.map((notification) => {
                const Icon = typeIcons[notification.type]
                return (
                  <button
                    key={notification.id}
                    onClick={() => !notification.is_read && markAsRead(notification.id)}
                    className={cn(
                      'w-full p-3 text-left border-b border-border last:border-0 transition-colors',
                      notification.is_read
                        ? 'bg-background'
                        : 'bg-accent/5 hover:bg-accent/10'
                    )}
                  >
                    <div className="flex gap-3">
                      <div className={cn('mt-0.5', typeColors[notification.type])}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={cn('text-sm', !notification.is_read && 'font-medium')}>
                          {notification.title}
                        </p>
                        {notification.message && (
                          <p className="text-xs text-foreground-secondary mt-0.5 truncate">
                            {notification.message}
                          </p>
                        )}
                        <p className="text-xs text-foreground-secondary mt-1">
                          {format(new Date(notification.created_at), 'M월 d일 HH:mm', { locale: ko })}
                        </p>
                      </div>
                      {!notification.is_read && (
                        <div className="h-2 w-2 rounded-full bg-accent mt-1" />
                      )}
                    </div>
                  </button>
                )
              })
            )}
          </div>

          {/* Footer */}
          <div className="p-2 border-t border-border">
            <Link href="/notifications" onClick={() => setIsOpen(false)}>
              <Button variant="ghost" size="sm" className="w-full">
                모든 알림 보기
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

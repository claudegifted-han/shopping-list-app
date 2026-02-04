'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import {
  User,
  Settings,
  Utensils,
  Bell,
  BookOpen,
  DoorOpen,
  Info,
  Key,
  Plus,
  Trash2,
  Smartphone,
  Monitor,
  Mail,
  Loader2,
} from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { createClient } from '@/lib/supabase/client'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils/cn'
import type { Passkey } from '@/types/database'

const menuItems = [
  { title: '프로필', href: '/profile', icon: User },
  { title: '일반', href: '/settings', icon: Settings },
  { title: '급식', href: '/settings/meals', icon: Utensils },
  { title: '알림', href: '/settings/notifications', icon: Bell },
  { title: '자습 신청', href: '/settings/study', icon: BookOpen },
  { title: '외출 신청', href: '/settings/outing', icon: DoorOpen },
  { title: '사이트 정보', href: '/settings/about', icon: Info },
]

export default function SettingsPage() {
  const { user, profile } = useAuth()
  const [passkeys, setPasskeys] = useState<Passkey[]>([])
  const [loading, setLoading] = useState(true)
  const [alternativeEmail, setAlternativeEmail] = useState('')
  const supabase = createClient()

  useEffect(() => {
    if (user) {
      fetchPasskeys()
      setAlternativeEmail(profile?.alternative_email || '')
    }
  }, [user, profile])

  const fetchPasskeys = async () => {
    if (!user) return

    const { data, error } = await supabase
      .from('passkeys')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error fetching passkeys:', error)
    } else {
      setPasskeys(data || [])
    }
    setLoading(false)
  }

  const handleCreatePasskey = async () => {
    // TODO: Implement WebAuthn passkey registration
    alert('패스키 생성 기능은 WebAuthn 서버 설정 후 구현됩니다.')
  }

  const handleDeletePasskey = async (passkeyId: string) => {
    if (!confirm('이 패스키를 삭제하시겠습니까?')) return

    const { error } = await supabase
      .from('passkeys')
      .delete()
      .eq('id', passkeyId)

    if (error) {
      alert('패스키 삭제에 실패했습니다.')
    } else {
      setPasskeys(passkeys.filter((p) => p.id !== passkeyId))
    }
  }

  const handleSaveAlternativeEmail = async () => {
    if (!user) return

    const { error } = await supabase
      .from('profiles')
      .update({ alternative_email: alternativeEmail })
      .eq('id', user.id)

    if (error) {
      alert('저장에 실패했습니다.')
    } else {
      alert('저장되었습니다.')
    }
  }

  const getDeviceIcon = (deviceType: string | null) => {
    if (!deviceType) return Monitor
    if (deviceType.toLowerCase().includes('android') || deviceType.toLowerCase().includes('ios')) {
      return Smartphone
    }
    return Monitor
  }

  if (!user || !profile) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">설정</h1>

      <div className="grid gap-6 md:grid-cols-4">
        {/* Left Menu */}
        <Card className="md:col-span-1 h-fit">
          <CardContent className="p-2">
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon
                const isActive = item.href === '/settings'

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                      isActive
                        ? 'bg-accent text-white'
                        : 'text-foreground-secondary hover:bg-background-secondary hover:text-foreground'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.title}
                  </Link>
                )
              })}
            </nav>
          </CardContent>
        </Card>

        {/* Settings Content */}
        <div className="md:col-span-3 space-y-6">
          {/* Passkeys */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="h-5 w-5" />
                    패스키 관리
                  </CardTitle>
                  <CardDescription>
                    패스키를 사용하면 비밀번호 없이 로그인할 수 있습니다
                  </CardDescription>
                </div>
                <Button variant="primary" size="sm" onClick={handleCreatePasskey}>
                  <Plus className="h-4 w-4 mr-2" />
                  패스키 생성
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-foreground-secondary" />
                </div>
              ) : passkeys.length === 0 ? (
                <p className="text-sm text-foreground-secondary text-center py-8">
                  등록된 패스키가 없습니다
                </p>
              ) : (
                <div className="space-y-3">
                  {passkeys.map((passkey) => {
                    const DeviceIcon = getDeviceIcon(passkey.device_type)

                    return (
                      <div
                        key={passkey.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-background-secondary"
                      >
                        <div className="flex items-center gap-3">
                          <DeviceIcon className="h-5 w-5 text-foreground-secondary" />
                          <div>
                            <p className="text-sm font-medium">
                              {passkey.device_type || '알 수 없는 기기'} / {passkey.browser || '알 수 없는 브라우저'}
                            </p>
                            <p className="text-xs text-foreground-secondary">
                              생성: {format(new Date(passkey.created_at), 'yyyy년 M월 d일', { locale: ko })}
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeletePasskey(passkey.id)}
                        >
                          <Trash2 className="h-4 w-4 text-danger" />
                        </Button>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Alternative Email */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                대체 이메일
              </CardTitle>
              <CardDescription>
                패스키를 분실했을 때 계정 복구에 사용됩니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                <Input
                  type="email"
                  placeholder="backup@example.com"
                  value={alternativeEmail}
                  onChange={(e) => setAlternativeEmail(e.target.value)}
                  className="flex-1"
                />
                <Button variant="default" onClick={handleSaveAlternativeEmail}>
                  저장
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import {
  Key,
  Plus,
  Trash2,
  Smartphone,
  Monitor,
  Mail,
  Moon,
  Sun,
  Monitor as SystemIcon,
  ChevronRight,
} from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { createClient } from '@/lib/supabase/client'
import { useTheme } from '@/components/providers/theme-provider'
import { cn } from '@/lib/utils/cn'
import type { Passkey } from '@/types/database'

export default function SettingsPage() {
  const { user, profile } = useAuth()
  const { theme, setTheme } = useTheme()
  const [passkeys, setPasskeys] = useState<Passkey[]>([])
  const [loading, setLoading] = useState(true)
  const [alternativeEmail, setAlternativeEmail] = useState('')
  const [saving, setSaving] = useState(false)
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
    setSaving(true)

    const { error } = await supabase
      .from('profiles')
      .update({ alternative_email: alternativeEmail })
      .eq('id', user.id)

    setSaving(false)
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
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">설정</h1>

      <div className="space-y-6">
        {/* Theme Settings */}
        <div className="rounded-lg border border-border bg-background-secondary p-4">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <Moon className="h-4 w-4" />
            테마
          </h3>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => setTheme('light')}
              className={cn(
                'flex items-center justify-center gap-2 py-3 px-4 rounded-lg border transition-colors',
                theme === 'light'
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border hover:border-accent/50'
              )}
            >
              <Sun className="h-4 w-4" />
              <span className="text-sm">라이트</span>
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={cn(
                'flex items-center justify-center gap-2 py-3 px-4 rounded-lg border transition-colors',
                theme === 'dark'
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border hover:border-accent/50'
              )}
            >
              <Moon className="h-4 w-4" />
              <span className="text-sm">다크</span>
            </button>
            <button
              onClick={() => setTheme('system')}
              className={cn(
                'flex items-center justify-center gap-2 py-3 px-4 rounded-lg border transition-colors',
                theme === 'system'
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border hover:border-accent/50'
              )}
            >
              <SystemIcon className="h-4 w-4" />
              <span className="text-sm">시스템</span>
            </button>
          </div>
        </div>

        {/* Passkeys */}
        <div className="rounded-lg border border-border bg-background-secondary p-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-medium flex items-center gap-2">
                <Key className="h-4 w-4" />
                패스키 관리
              </h3>
              <p className="text-xs text-foreground-secondary mt-1">
                패스키를 사용하면 비밀번호 없이 로그인할 수 있습니다
              </p>
            </div>
            <button
              onClick={handleCreatePasskey}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-accent text-white text-sm hover:bg-accent/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              추가
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </div>
          ) : passkeys.length === 0 ? (
            <p className="text-sm text-foreground-secondary text-center py-8">
              등록된 패스키가 없습니다
            </p>
          ) : (
            <div className="space-y-2">
              {passkeys.map((passkey) => {
                const DeviceIcon = getDeviceIcon(passkey.device_type)

                return (
                  <div
                    key={passkey.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-background border border-border"
                  >
                    <div className="flex items-center gap-3">
                      <DeviceIcon className="h-5 w-5 text-foreground-secondary" />
                      <div>
                        <p className="text-sm font-medium">
                          {passkey.device_type || '알 수 없는 기기'}
                        </p>
                        <p className="text-xs text-foreground-secondary">
                          {passkey.browser || '알 수 없는 브라우저'} · {format(new Date(passkey.created_at), 'M월 d일', { locale: ko })}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeletePasskey(passkey.id)}
                      className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Alternative Email */}
        <div className="rounded-lg border border-border bg-background-secondary p-4">
          <h3 className="font-medium mb-1 flex items-center gap-2">
            <Mail className="h-4 w-4" />
            대체 이메일
          </h3>
          <p className="text-xs text-foreground-secondary mb-4">
            패스키를 분실했을 때 계정 복구에 사용됩니다
          </p>
          <div className="flex gap-2">
            <input
              type="email"
              placeholder="backup@example.com"
              value={alternativeEmail}
              onChange={(e) => setAlternativeEmail(e.target.value)}
              className="flex-1 px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:border-accent"
            />
            <button
              onClick={handleSaveAlternativeEmail}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-accent text-white text-sm hover:bg-accent/90 transition-colors disabled:opacity-50"
            >
              {saving ? '저장 중...' : '저장'}
            </button>
          </div>
        </div>

        {/* App Info */}
        <div className="rounded-lg border border-border bg-background-secondary p-4">
          <h3 className="font-medium mb-4">앱 정보</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-sm text-foreground-secondary">버전</span>
              <span className="text-sm">1.0.0</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-border">
              <span className="text-sm text-foreground-secondary">개발자</span>
              <span className="text-sm">대전과학고등학교</span>
            </div>
            <a
              href="/updates"
              className="flex items-center justify-between py-2 hover:text-accent transition-colors"
            >
              <span className="text-sm">업데이트 내역</span>
              <ChevronRight className="h-4 w-4" />
            </a>
            <a
              href="/feedback"
              className="flex items-center justify-between py-2 hover:text-accent transition-colors"
            >
              <span className="text-sm">피드백 보내기</span>
              <ChevronRight className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

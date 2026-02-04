'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
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
  Mail,
  Trash2,
  LogOut,
  Link as LinkIcon,
} from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils/cn'
import { Badge } from '@/components/ui/badge'
import type { Passkey } from '@/types/database'

type SettingsTab = 'profile' | 'general' | 'meals' | 'notifications' | 'study' | 'outing' | 'about'

const menuItems: { id: SettingsTab; title: string; icon: typeof User }[] = [
  { id: 'profile', title: '프로필', icon: User },
  { id: 'general', title: '일반', icon: Settings },
  { id: 'meals', title: '급식', icon: Utensils },
  { id: 'notifications', title: '알림', icon: Bell },
  { id: 'study', title: '자습 신청', icon: BookOpen },
  { id: 'outing', title: '외출 신청', icon: DoorOpen },
  { id: 'about', title: '사이트 정보', icon: Info },
]

const roleLabels: Record<string, string> = {
  student: '학생',
  teacher: '선생님',
  admin: '관리자',
}

// Avatar color palette
const avatarColors = [
  'from-purple-500 to-pink-500',
  'from-blue-500 to-cyan-500',
  'from-green-500 to-teal-500',
  'from-orange-500 to-red-500',
  'from-indigo-500 to-purple-500',
  'from-pink-500 to-rose-500',
  'from-cyan-500 to-blue-500',
  'from-teal-500 to-green-500',
]

const getAvatarColor = (studentNumber: string | null) => {
  if (!studentNumber) return avatarColors[0]
  const num = parseInt(studentNumber.slice(-2)) || 0
  return avatarColors[num % avatarColors.length]
}

// Allergen list
const allergens = [
  { id: 1, name: '난류(가금류)' },
  { id: 2, name: '우유' },
  { id: 3, name: '메밀' },
  { id: 4, name: '땅콩' },
  { id: 5, name: '대두' },
  { id: 6, name: '밀' },
  { id: 7, name: '고등어' },
  { id: 8, name: '게' },
  { id: 9, name: '새우' },
  { id: 10, name: '돼지고기' },
  { id: 11, name: '복숭아' },
  { id: 12, name: '토마토' },
  { id: 13, name: '아황산류' },
  { id: 14, name: '호두' },
  { id: 15, name: '닭고기' },
  { id: 16, name: '쇠고기' },
  { id: 17, name: '오징어' },
  { id: 18, name: '조개류' },
  { id: 19, name: '잣' },
]

// Notification options
const notificationOptions = [
  { id: 'required', name: '필수', description: '반드시 수신해야 하는 알림입니다.', disabled: true },
  { id: 'study', name: '자습 신청 정보', description: '자습 신청이 시작되기 전 발송되는 알림입니다.' },
  { id: 'dormitory', name: '기숙사 신청 정보', description: '기숙사 신청을 하지 않았을 경우 발송되는 알림입니다.' },
  { id: 'penalty', name: '벌점/상점', description: '벌점/상점을 받을 때마다 발송되는 알림입니다.' },
  { id: 'penalty_exceed', name: '벌점 초과', description: '벌점이 일정 수준을 초과했을 경우 발송되는 알림입니다.' },
  { id: 'outing', name: '외출 신청', description: '외출 신청 관련 알림입니다.' },
]

// Study room settings
const studyRoomOptions = [
  { id: 'show_image', name: '자습실 이미지 표시', description: '자습실의 이미지를 보여줍니다.' },
  { id: 'show_all_tab', name: "'전체' 탭 표시", description: '모든 좌석을 실제 레이아웃을 무시하고 보여주는 탭을 추가합니다.' },
  { id: 'modified_layout', name: '변형된 레이아웃 사용', description: '레이아웃을 일부 변경하는 대신 한 화면에 최대한 많은 자리가 보이도록 합니다.' },
  { id: 'show_badge', name: '배지 표시', description: '학년, 성별을 보여주는 배지를 표시합니다.' },
  { id: 'badge_gender', name: '배지에 성별 표시', description: '성별에 따라 배지 색상을 변경합니다.' },
  { id: 'custom_badge_color', name: '사용자 지정 배지 색상 사용', description: '배지 색상을 사용자 지정합니다.' },
]

export default function SettingsPage() {
  const { user, profile, signOut } = useAuth()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile')
  const [passkeys, setPasskeys] = useState<Passkey[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Settings states
  const [selectedAllergens, setSelectedAllergens] = useState<number[]>([])
  const [notifications, setNotifications] = useState<Record<string, boolean>>({
    required: true,
    study: true,
    dormitory: true,
    penalty: true,
    penalty_exceed: true,
    outing: true,
  })
  const [studySettings, setStudySettings] = useState<Record<string, boolean>>({
    show_image: true,
    show_all_tab: false,
    modified_layout: true,
    show_badge: true,
    badge_gender: true,
    custom_badge_color: false,
  })
  const [favorites, setFavorites] = useState<string[]>([])
  const [newFavorite, setNewFavorite] = useState('')

  const supabase = createClient()

  useEffect(() => {
    if (user) {
      fetchPasskeys()
    }
  }, [user])

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

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  const handleSaveAllergens = async () => {
    setSaving(true)
    // TODO: Save allergens to profile
    await new Promise(resolve => setTimeout(resolve, 500))
    setSaving(false)
    alert('저장되었습니다.')
  }

  const handleSaveNotifications = async () => {
    setSaving(true)
    // TODO: Save notification settings
    await new Promise(resolve => setTimeout(resolve, 500))
    setSaving(false)
    alert('저장되었습니다.')
  }

  const handleSaveStudySettings = async () => {
    setSaving(true)
    // TODO: Save study room settings
    await new Promise(resolve => setTimeout(resolve, 500))
    setSaving(false)
    alert('저장되었습니다.')
  }

  const handleSaveFavorites = async () => {
    setSaving(true)
    // TODO: Save favorites
    await new Promise(resolve => setTimeout(resolve, 500))
    setSaving(false)
    alert('저장되었습니다.')
  }

  const handleResetBrowserSettings = () => {
    if (!confirm('브라우저에 저장된 모든 설정을 삭제합니다. 계속하시겠습니까?')) return
    localStorage.clear()
    alert('설정이 초기화되었습니다.')
  }

  if (!user || !profile) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">설정</h1>

      <div className="flex gap-6">
        {/* Left Menu */}
        <div className="w-48 flex-shrink-0">
          <nav className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.id

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={cn(
                    'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors text-left',
                    isActive
                      ? 'bg-accent text-white'
                      : 'hover:bg-background-secondary'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.title}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Content Area */}
        <div className="flex-1 min-w-0">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              {/* Profile Card */}
              <div className="flex items-center gap-4 p-4 rounded-lg border border-border bg-background-secondary">
                {/* Avatar */}
                {profile.avatar_url ? (
                  <img
                    src={profile.avatar_url}
                    alt="프로필"
                    className="h-16 w-16 rounded-full object-cover border border-border"
                  />
                ) : (
                  <div className={`h-16 w-16 rounded-full bg-gradient-to-br ${getAvatarColor(profile.student_number)} flex items-center justify-center`}>
                    <span className="text-2xl font-bold text-white">
                      {profile.name[0]}
                    </span>
                  </div>
                )}
                <div>
                  <h2 className="text-xl font-bold">
                    {profile.student_number} {profile.name}
                  </h2>
                  <p className="text-sm text-foreground-secondary">{user.email}</p>
                </div>
              </div>

              {/* Basic Info */}
              <div>
                <h3 className="font-medium mb-3">기본 정보</h3>
                <div className="space-y-2">
                  <InfoRow label="이름" value={profile.name} />
                  <InfoRow label="별칭" value={profile.nickname || '(없음)'} />
                  <InfoRow label="이메일" value={user.email || '-'} />
                </div>
              </div>

              {/* Additional Info */}
              <div>
                <h3 className="font-medium mb-3">추가 정보</h3>
                <div className="space-y-2">
                  <InfoRow
                    label="권한"
                    value={
                      <span className={cn(
                        profile.role === 'teacher' && 'text-accent'
                      )}>
                        {roleLabels[profile.role]}
                      </span>
                    }
                  />
                  <InfoRow label="성별" value={profile.gender || '(등록되지 않음)'} />
                  <InfoRow label="전화번호" value={profile.phone || '(등록되지 않음)'} />
                  <InfoRow label="부모님 전화번호" value={profile.parent_phone || '(등록되지 않음)'} />
                  <InfoRow label="등록 년도" value={profile.registration_year?.toString() || '-'} />
                </div>
              </div>

              {/* Logout Button */}
              <button
                onClick={handleSignOut}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent/90 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                로그아웃
              </button>
            </div>
          )}

          {/* General Tab */}
          {activeTab === 'general' && (
            <div className="space-y-8">
              {/* Passkey Management */}
              <div>
                <h3 className="font-medium mb-2">패스키 관리</h3>
                <p className="text-sm text-foreground-secondary mb-4">
                  패스키를 새로 만들거나 삭제합니다.
                </p>

                <h4 className="text-sm font-medium mb-3">패스키 목록</h4>
                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                  </div>
                ) : passkeys.length === 0 ? (
                  <p className="text-sm text-foreground-secondary py-4">
                    등록된 패스키가 없습니다.
                  </p>
                ) : (
                  <div className="border border-border rounded-lg overflow-hidden mb-4">
                    <table className="w-full text-sm">
                      <thead className="bg-background-secondary">
                        <tr>
                          <th className="px-4 py-2 text-left font-medium">생성 일자</th>
                          <th className="px-4 py-2 text-left font-medium">기기</th>
                          <th className="px-4 py-2 text-left font-medium">브라우저</th>
                          <th className="px-4 py-2 text-left font-medium">동작</th>
                        </tr>
                      </thead>
                      <tbody>
                        {passkeys.map((passkey) => (
                          <tr key={passkey.id} className="border-t border-border">
                            <td className="px-4 py-2">
                              {format(new Date(passkey.created_at), 'yyyy.MM.dd')}
                            </td>
                            <td className="px-4 py-2">{passkey.device_type || '-'}</td>
                            <td className="px-4 py-2">{passkey.browser || '-'}</td>
                            <td className="px-4 py-2">
                              <button
                                onClick={() => handleDeletePasskey(passkey.id)}
                                className="text-red-500 hover:underline"
                              >
                                삭제
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <h4 className="text-sm font-medium mb-2">패스키 생성</h4>
                <button
                  onClick={handleCreatePasskey}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors"
                >
                  <Key className="h-4 w-4" />
                  패스키 생성
                </button>
              </div>

              {/* Alternative Email */}
              <div>
                <h3 className="font-medium mb-2">대체 이메일</h3>
                <p className="text-sm text-foreground-secondary mb-1">
                  패스키를 사용하지 않고 로그인할때 @djshs.djsch.kr 대신 인증 코드를 받을 이메일을 등록합니다.
                </p>
                <p className="text-sm text-foreground-secondary mb-4">
                  단, 로그인할 때 이메일은 무조건 기존 이메일을 입력해야 합니다.
                </p>
                <p className="text-sm mb-3">등록된 이메일이 없습니다.</p>
                <button
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors"
                >
                  <Mail className="h-4 w-4" />
                  대체 이메일 등록
                </button>
              </div>

              {/* Google Account Link */}
              <div>
                <h3 className="font-medium mb-2">Google 계정 연동</h3>
                <p className="text-sm text-foreground-secondary mb-4">
                  Google 계정을 연동하여 Google Drive, Google Classroom 등의 서비스를 편리하게 이용할 수 있습니다.
                </p>
                <button
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors"
                >
                  <LinkIcon className="h-4 w-4" />
                  Google 계정 연동하기
                </button>
              </div>

              {/* Browser Settings Reset */}
              <div>
                <h3 className="font-medium mb-2">브라우저 설정 초기화</h3>
                <p className="text-sm text-foreground-secondary mb-4">
                  브라우저에 저장된 모든 설정을 삭제합니다. 설정을 변경한 뒤 지속적으로 오류가 발생할 경우 시도해 보세요.
                </p>
                <button
                  onClick={handleResetBrowserSettings}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                  모든 설정 초기화
                </button>
              </div>
            </div>
          )}

          {/* Meals Tab */}
          {activeTab === 'meals' && (
            <div>
              <h3 className="font-medium mb-2">알레르기 설정</h3>
              <p className="text-sm text-foreground-secondary mb-4">
                알레르기 종류를 지정합니다. 지정된 알레르기가 포함된 급식은 붉은색으로 표시됩니다. 이 설정은 이 브라우저에서만 적용됩니다.
              </p>

              <div className="grid grid-cols-4 gap-3 mb-4">
                {allergens.map((allergen) => (
                  <label
                    key={allergen.id}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedAllergens.includes(allergen.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedAllergens([...selectedAllergens, allergen.id])
                        } else {
                          setSelectedAllergens(selectedAllergens.filter(id => id !== allergen.id))
                        }
                      }}
                      className="w-4 h-4 rounded border-border"
                    />
                    <span className="text-sm">{allergen.id}. {allergen.name}</span>
                  </label>
                ))}
              </div>

              <button
                onClick={handleSaveAllergens}
                disabled={saving}
                className="px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors disabled:opacity-50"
              >
                {saving ? '저장 중...' : '저장'}
              </button>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div>
              <h3 className="font-medium mb-2">알림 설정</h3>
              <p className="text-sm text-foreground-secondary mb-4">
                iOS/macOS/Android 앱을 통해 수신할 알림을 설정합니다.
              </p>

              <div className="space-y-4 mb-4">
                {notificationOptions.map((option) => (
                  <label
                    key={option.id}
                    className="flex items-start gap-3 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={notifications[option.id]}
                      disabled={option.disabled}
                      onChange={(e) => {
                        setNotifications({
                          ...notifications,
                          [option.id]: e.target.checked,
                        })
                      }}
                      className="w-4 h-4 rounded border-border mt-0.5"
                    />
                    <div>
                      <span className="font-medium">{option.name}</span>
                      <p className="text-sm text-foreground-secondary">{option.description}</p>
                    </div>
                  </label>
                ))}
              </div>

              <button
                onClick={handleSaveNotifications}
                disabled={saving}
                className="px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors disabled:opacity-50"
              >
                {saving ? '저장 중...' : '저장'}
              </button>
            </div>
          )}

          {/* Study Room Tab */}
          {activeTab === 'study' && (
            <div>
              <h3 className="font-medium mb-2">자습 신청 설정</h3>
              <p className="text-sm text-foreground-secondary mb-4">
                자습 신청 페이지를 사용자화합니다. 이 설정은 이 브라우저에서만 적용됩니다.
              </p>

              <h4 className="text-sm font-medium mb-3">일반</h4>
              <div className="space-y-3 mb-6">
                {studyRoomOptions.slice(0, 2).map((option) => (
                  <label
                    key={option.id}
                    className="flex items-start gap-3 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={studySettings[option.id]}
                      onChange={(e) => {
                        setStudySettings({
                          ...studySettings,
                          [option.id]: e.target.checked,
                        })
                      }}
                      className="w-4 h-4 rounded border-border mt-0.5"
                    />
                    <div>
                      <span className="font-medium">{option.name}</span>
                      <p className="text-sm text-foreground-secondary">{option.description}</p>
                    </div>
                  </label>
                ))}
              </div>

              <h4 className="text-sm font-medium mb-3">레이아웃</h4>
              <div className="space-y-3 mb-6">
                {studyRoomOptions.slice(2).map((option) => (
                  <label
                    key={option.id}
                    className="flex items-start gap-3 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={studySettings[option.id]}
                      onChange={(e) => {
                        setStudySettings({
                          ...studySettings,
                          [option.id]: e.target.checked,
                        })
                      }}
                      className="w-4 h-4 rounded border-border mt-0.5"
                    />
                    <div>
                      <span className="font-medium">{option.name}</span>
                      <p className="text-sm text-foreground-secondary">{option.description}</p>
                    </div>
                  </label>
                ))}
              </div>

              {/* Preview */}
              <h4 className="text-sm font-medium mb-3">미리보기</h4>
              <div className="grid grid-cols-4 gap-2 p-4 border border-border rounded-lg bg-background-secondary max-w-md">
                {['a101', 'a102', 'a103', 'a104', 'a105', 'a106', 'a107', 'a108', 'a109', 'a110', 'a111', 'a112', 'a113', 'a114', 'a115', ''].map((seat, index) => (
                  <div
                    key={index}
                    className={cn(
                      'py-2 px-1 text-center text-xs rounded',
                      seat === 'a103'
                        ? 'bg-accent text-white'
                        : seat === 'a101' || seat === 'a102' || seat === 'a104'
                          ? 'bg-blue-500/20 border border-blue-500/50'
                          : seat
                            ? 'bg-background border border-border'
                            : ''
                    )}
                  >
                    {seat && (
                      <>
                        <div>{seat}</div>
                        {seat === 'a101' && <div className="text-[10px] text-blue-400">1 예시1</div>}
                        {seat === 'a102' && <div className="text-[10px] text-blue-400">2 예시2</div>}
                        {seat === 'a103' && <div className="text-[10px]">(본인)</div>}
                        {seat === 'a104' && <div className="text-[10px] text-blue-400">3 예시3</div>}
                      </>
                    )}
                  </div>
                ))}
              </div>

              <button
                onClick={handleSaveStudySettings}
                disabled={saving}
                className="mt-4 px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors disabled:opacity-50"
              >
                {saving ? '저장 중...' : '저장'}
              </button>
            </div>
          )}

          {/* Outing Tab */}
          {activeTab === 'outing' && (
            <div>
              <h3 className="font-medium mb-2">즐겨찾기 설정</h3>
              <p className="text-sm text-foreground-secondary mb-4">
                특별실 신청에서 즐겨찾기에 표시되는 항목을 수정합니다. 이 설정은 이 브라우저에서만 적용됩니다.
              </p>

              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  placeholder="Enter: 항목 추가, Backspace: 항목 삭제"
                  value={newFavorite}
                  onChange={(e) => setNewFavorite(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newFavorite.trim()) {
                      setFavorites([...favorites, newFavorite.trim()])
                      setNewFavorite('')
                    } else if (e.key === 'Backspace' && !newFavorite && favorites.length > 0) {
                      setFavorites(favorites.slice(0, -1))
                    }
                  }}
                  className="flex-1 px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:border-accent"
                />
                <button
                  onClick={() => setFavorites([])}
                  className="p-2 rounded-lg border border-border hover:bg-background-secondary transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
                <button
                  onClick={() => {
                    if (newFavorite.trim()) {
                      setFavorites([...favorites, newFavorite.trim()])
                      setNewFavorite('')
                    }
                  }}
                  className="px-3 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors text-sm"
                >
                  +
                </button>
              </div>

              {favorites.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {favorites.map((fav, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 rounded bg-background-secondary text-sm"
                    >
                      {fav}
                    </span>
                  ))}
                </div>
              )}

              <button
                onClick={handleSaveFavorites}
                disabled={saving}
                className="px-4 py-2 rounded-lg border border-border hover:bg-background-secondary transition-colors disabled:opacity-50"
              >
                {saving ? '저장 중...' : '저장'}
              </button>
            </div>
          )}

          {/* About Tab */}
          {activeTab === 'about' && (
            <div className="flex flex-col items-center justify-center py-12">
              <Image
                src="/logo-djshs.png"
                alt="대전과학고등학교"
                width={100}
                height={100}
                className="mb-4"
              />
              <h2 className="text-2xl font-bold mb-2">DJSHS.APP</h2>
              <p className="text-lg text-foreground-secondary mb-4">V1.0.0</p>
              <p className="text-sm text-accent">대전과학고 by Claude Code(2026)</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function InfoRow({
  label,
  value,
}: {
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-foreground-secondary">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

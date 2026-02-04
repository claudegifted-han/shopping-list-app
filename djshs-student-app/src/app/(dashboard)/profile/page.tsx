'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  User,
  LogOut,
  Mail,
  Phone,
  Calendar,
  Shield,
  AlertTriangle,
} from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'

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

export default function ProfilePage() {
  const { user, profile, signOut } = useAuth()
  const router = useRouter()

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
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
      {/* Profile Header */}
      <div className="rounded-lg border border-border bg-background-secondary p-6 mb-6">
        <div className="flex items-center gap-4">
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

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xl font-bold">{profile.name}</h2>
              <Badge
                className={cn(
                  'text-xs',
                  profile.role === 'admin'
                    ? 'bg-red-500/10 text-red-500 border-red-500/20'
                    : profile.role === 'teacher'
                      ? 'bg-blue-500/10 text-blue-500 border-blue-500/20'
                      : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                )}
              >
                {roleLabels[profile.role]}
              </Badge>
            </div>
            <p className="text-sm text-foreground-secondary">
              {profile.student_number}
            </p>
            <p className="text-sm text-foreground-secondary">
              {user.email}
            </p>
          </div>
        </div>
      </div>

      {/* Info Sections */}
      <div className="space-y-6">
        {/* Basic Info */}
        <div className="rounded-lg border border-border bg-background-secondary p-4">
          <h3 className="font-medium mb-4">기본 정보</h3>
          <div className="space-y-3">
            <InfoRow icon={User} label="이름" value={profile.name} />
            <InfoRow icon={User} label="별칭" value={profile.nickname || '-'} />
            <InfoRow icon={Mail} label="이메일" value={user.email || '-'} />
          </div>
        </div>

        {/* Additional Info */}
        <div className="rounded-lg border border-border bg-background-secondary p-4">
          <h3 className="font-medium mb-4">추가 정보</h3>
          <div className="space-y-3">
            <InfoRow icon={Shield} label="권한" value={roleLabels[profile.role]} />
            <InfoRow icon={User} label="성별" value={profile.gender || '-'} />
            <InfoRow icon={Phone} label="전화번호" value={profile.phone || '-'} />
            <InfoRow icon={Phone} label="부모님 전화번호" value={profile.parent_phone || '-'} />
            <InfoRow icon={Calendar} label="등록 년도" value={profile.registration_year?.toString() || '-'} />
          </div>
        </div>

        {/* Penalty Info (for students) */}
        {profile.role === 'student' && (
          <div className="rounded-lg border border-border bg-background-secondary p-4">
            <h3 className="font-medium mb-4">벌점 정보</h3>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-foreground-secondary" />
                <span className="text-foreground-secondary">총 벌점</span>
              </div>
              <Badge
                className={cn(
                  'text-lg px-3 py-1',
                  (profile.total_penalty || 0) > 0
                    ? 'bg-red-500/10 text-red-500 border-red-500/20'
                    : (profile.total_penalty || 0) < 0
                      ? 'bg-green-500/10 text-green-500 border-green-500/20'
                      : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                )}
              >
                {(profile.total_penalty || 0) > 0 ? '+' : ''}{profile.total_penalty || 0}점
              </Badge>
            </div>
            <Link
              href="/penalties"
              className="block mt-3 text-sm text-accent hover:underline text-center"
            >
              벌점 기록 보기
            </Link>
          </div>
        )}

        {/* Logout Button */}
        <button
          onClick={handleSignOut}
          className="w-full py-3 px-4 rounded-lg border border-red-500/30 bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors flex items-center justify-center gap-2"
        >
          <LogOut className="h-4 w-4" />
          로그아웃
        </button>
      </div>
    </div>
  )
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <div className="flex items-center gap-2 text-foreground-secondary">
        <Icon className="h-4 w-4" />
        <span className="text-sm">{label}</span>
      </div>
      <span className="text-sm font-medium">{value}</span>
    </div>
  )
}

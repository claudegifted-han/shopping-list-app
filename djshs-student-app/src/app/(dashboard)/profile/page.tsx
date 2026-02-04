'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  User,
  Settings,
  Utensils,
  Bell,
  BookOpen,
  DoorOpen,
  Info,
  LogOut,
  Mail,
  Phone,
  Calendar,
  Shield,
} from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'

const menuItems = [
  { title: '프로필', href: '/profile', icon: User },
  { title: '일반', href: '/settings', icon: Settings },
  { title: '급식', href: '/settings/meals', icon: Utensils },
  { title: '알림', href: '/settings/notifications', icon: Bell },
  { title: '자습 신청', href: '/settings/study', icon: BookOpen },
  { title: '외출 신청', href: '/settings/outing', icon: DoorOpen },
  { title: '사이트 정보', href: '/settings/about', icon: Info },
]

const roleLabels = {
  student: '학생',
  teacher: '선생님',
  admin: '관리자',
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
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">사용자 정보</h1>

      <div className="grid gap-6 md:grid-cols-4">
        {/* Left Menu */}
        <Card className="md:col-span-1 h-fit">
          <CardContent className="p-2">
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon
                const isActive = item.href === '/profile'

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

        {/* Profile Content */}
        <div className="md:col-span-3 space-y-6">
          {/* Profile Card */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start gap-6">
                {/* Avatar */}
                <div className="shrink-0">
                  {profile.avatar_url ? (
                    <img
                      src={profile.avatar_url}
                      alt="프로필"
                      className="h-24 w-24 rounded-xl object-cover border border-border"
                    />
                  ) : (
                    <div className="h-24 w-24 rounded-xl bg-background-card border border-border flex items-center justify-center">
                      <User className="h-12 w-12 text-foreground-secondary" />
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-xl font-bold">
                      {profile.student_number} {profile.name}
                    </h2>
                    <Badge variant="default">
                      {roleLabels[profile.role]}
                    </Badge>
                  </div>
                  <p className="text-foreground-secondary text-sm mb-4">
                    {user.email}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Basic Info */}
          <Card>
            <CardHeader>
              <CardTitle>기본 정보</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <InfoItem
                  icon={User}
                  label="이름"
                  value={profile.name}
                />
                <InfoItem
                  icon={User}
                  label="별칭"
                  value={profile.nickname || '-'}
                />
                <InfoItem
                  icon={Mail}
                  label="이메일"
                  value={user.email || '-'}
                />
              </div>
            </CardContent>
          </Card>

          {/* Additional Info */}
          <Card>
            <CardHeader>
              <CardTitle>추가 정보</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <InfoItem
                  icon={Shield}
                  label="권한"
                  value={
                    <Link href="/settings/role" className="text-link hover:underline">
                      {roleLabels[profile.role]}
                    </Link>
                  }
                />
                <InfoItem
                  icon={User}
                  label="성별"
                  value={profile.gender || '-'}
                />
                <InfoItem
                  icon={Phone}
                  label="전화번호"
                  value={profile.phone || '-'}
                />
                <InfoItem
                  icon={Phone}
                  label="부모님 전화번호"
                  value={profile.parent_phone || '-'}
                />
                <InfoItem
                  icon={Calendar}
                  label="등록 년도"
                  value={profile.registration_year?.toString() || '-'}
                />
              </div>
            </CardContent>
          </Card>

          {/* Logout Button */}
          <Button
            variant="danger"
            className="w-full"
            onClick={handleSignOut}
          >
            <LogOut className="h-4 w-4 mr-2" />
            로그아웃
          </Button>
        </div>
      </div>
    </div>
  )
}

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="shrink-0 p-2 rounded-lg bg-background-secondary">
        <Icon className="h-4 w-4 text-foreground-secondary" />
      </div>
      <div>
        <p className="text-xs text-foreground-secondary">{label}</p>
        <p className="text-sm font-medium">{value}</p>
      </div>
    </div>
  )
}

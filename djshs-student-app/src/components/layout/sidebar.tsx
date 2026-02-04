'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Home,
  BookOpen,
  DoorOpen,
  Utensils,
  Users,
  AlertTriangle,
  ClipboardList,
  User,
  Settings,
  MessageSquare,
  History,
  HelpCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { useAuth } from '@/components/providers/auth-provider'

interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  roles?: ('student' | 'teacher' | 'admin')[]
}

interface NavGroup {
  title: string
  items: NavItem[]
}

const navigation: NavGroup[] = [
  {
    title: '앱',
    items: [
      { title: '자습 신청', href: '/study', icon: BookOpen },
      { title: '외출/특별실 신청', href: '/outing', icon: DoorOpen },
      { title: '급식', href: '/meals', icon: Utensils },
    ],
  },
  {
    title: '교사',
    items: [
      { title: '교사 홈', href: '/teacher', icon: Home, roles: ['teacher', 'admin'] },
      { title: '학생 목록', href: '/teacher/students', icon: Users, roles: ['teacher', 'admin'] },
      { title: '벌점 부여', href: '/penalties/give', icon: AlertTriangle, roles: ['teacher', 'admin'] },
      { title: '벌점 기록', href: '/penalties', icon: ClipboardList, roles: ['teacher', 'admin'] },
    ],
  },
  {
    title: '계정',
    items: [
      { title: '사용자 정보', href: '/profile', icon: User },
      { title: '설정', href: '/settings', icon: Settings },
    ],
  },
  {
    title: '기타',
    items: [
      { title: '피드백', href: '/feedback', icon: MessageSquare },
      { title: '업데이트 내역', href: '/updates', icon: History },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { profile } = useAuth()
  const userRole = profile?.role ?? 'student'

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-sidebar-border bg-sidebar-bg hidden lg:block">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center border-b border-sidebar-border px-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-accent flex items-center justify-center">
              <span className="text-white font-bold text-sm">D</span>
            </div>
            <div>
              <span className="font-bold text-lg">DJSHS.APP</span>
              <span className="text-xs text-foreground-secondary ml-2">v1.0.0</span>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4">
          {navigation.map((group) => {
            const visibleItems = group.items.filter(
              (item) => !item.roles || item.roles.includes(userRole)
            )

            if (visibleItems.length === 0) return null

            return (
              <div key={group.title} className="mb-6">
                <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-foreground-secondary">
                  {group.title}
                </h3>
                <ul className="space-y-1">
                  {visibleItems.map((item) => {
                    const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
                    const Icon = item.icon

                    return (
                      <li key={item.href}>
                        <Link
                          href={item.href}
                          className={cn(
                            'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                            isActive
                              ? 'bg-accent text-white'
                              : 'text-foreground-secondary hover:bg-background-card hover:text-foreground'
                          )}
                        >
                          <Icon className="h-4 w-4" />
                          {item.title}
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-sidebar-border p-4">
          <Link
            href="/help"
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-foreground-secondary hover:bg-background-card hover:text-foreground transition-colors"
          >
            <HelpCircle className="h-4 w-4" />
            도움말
          </Link>
        </div>
      </div>
    </aside>
  )
}

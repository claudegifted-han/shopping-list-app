'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { User, ChevronRight, Sun, Moon, Monitor, MessageSquare, LogOut, Check } from 'lucide-react'
import { useTheme } from '@/components/providers/theme-provider'
import { useAuth } from '@/components/providers/auth-provider'
import { cn } from '@/lib/utils/cn'

export function ProfileDropdown() {
  const [open, setOpen] = useState(false)
  const [themeSubmenuOpen, setThemeSubmenuOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { theme, setTheme } = useTheme()
  const { user, profile, signOut } = useAuth()
  const router = useRouter()

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false)
        setThemeSubmenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  const themeOptions = [
    { value: 'system', label: '시스템', icon: Monitor },
    { value: 'dark', label: '다크', icon: Moon },
    { value: 'light', label: '라이트', icon: Sun },
  ] as const

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-center h-9 w-9 rounded-full bg-background-card border border-border hover:border-border-accent transition-colors overflow-hidden"
      >
        {profile?.avatar_url ? (
          <img
            src={profile.avatar_url}
            alt="프로필"
            className="h-full w-full object-cover"
          />
        ) : (
          <User className="h-4 w-4 text-foreground-secondary" />
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 rounded-lg border border-border bg-background-card shadow-lg">
          {/* User Info */}
          <div className="px-4 py-3 border-b border-border">
            <p className="text-sm text-foreground-secondary truncate">
              {user?.email}
            </p>
            <p className="text-sm font-medium">
              {profile?.student_number} {profile?.name}
            </p>
          </div>

          {/* Menu Items */}
          <div className="py-1">
            {/* Theme Setting with Submenu */}
            <div className="relative">
              <button
                onClick={() => setThemeSubmenuOpen(!themeSubmenuOpen)}
                className="flex w-full items-center justify-between px-4 py-2 text-sm text-foreground hover:bg-background-secondary"
              >
                <span>테마 설정</span>
                <ChevronRight className="h-4 w-4" />
              </button>

              {themeSubmenuOpen && (
                <div className="absolute right-full top-0 mr-1 w-40 rounded-lg border border-border bg-background-card shadow-lg">
                  {themeOptions.map((option) => {
                    const Icon = option.icon
                    return (
                      <button
                        key={option.value}
                        onClick={() => {
                          setTheme(option.value)
                          setThemeSubmenuOpen(false)
                        }}
                        className="flex w-full items-center gap-3 px-4 py-2 text-sm text-foreground hover:bg-background-secondary"
                      >
                        <Icon className="h-4 w-4" />
                        <span className="flex-1 text-left">{option.label}</span>
                        {theme === option.value && (
                          <Check className="h-4 w-4 text-accent" />
                        )}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Feedback */}
            <Link
              href="/feedback"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2 text-sm text-foreground hover:bg-background-secondary"
            >
              <MessageSquare className="h-4 w-4" />
              피드백
            </Link>

            {/* Logout */}
            <button
              onClick={handleSignOut}
              className="flex w-full items-center gap-3 px-4 py-2 text-sm text-danger hover:bg-background-secondary"
            >
              <LogOut className="h-4 w-4" />
              로그아웃
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

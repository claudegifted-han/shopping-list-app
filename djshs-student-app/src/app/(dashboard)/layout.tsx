'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/components/providers/auth-provider'
import { Sidebar } from '@/components/layout/sidebar'
import { Header } from '@/components/layout/header'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { loading } = useAuth()
  const [showContent, setShowContent] = useState(false)

  useEffect(() => {
    // 로딩이 완료되면 바로 표시
    if (!loading) {
      setShowContent(true)
      return
    }

    // 3초 후에도 로딩 중이면 강제로 콘텐츠 표시
    const timer = setTimeout(() => {
      setShowContent(true)
    }, 3000)

    return () => clearTimeout(timer)
  }, [loading])

  if (!showContent) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
          <p className="text-sm text-foreground-secondary">로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar - Desktop only */}
      <Sidebar />

      {/* Main Content */}
      <div className="lg:pl-64">
        <Header />
        <main className="p-4 lg:p-6">{children}</main>
      </div>
    </div>
  )
}

'use client'

import { useAuth } from '@/components/providers/auth-provider'
import { redirect } from 'next/navigation'
import { useEffect } from 'react'

export default function HomePage() {
  const { profile, loading } = useAuth()

  useEffect(() => {
    if (!loading && profile) {
      if (profile.role === 'teacher' || profile.role === 'admin') {
        redirect('/teacher')
      } else {
        redirect('/meals')
      }
    }
  }, [profile, loading])

  return (
    <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
        <p className="text-sm text-foreground-secondary">리디렉션 중...</p>
      </div>
    </div>
  )
}

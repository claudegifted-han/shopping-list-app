'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { AlertTriangle, Search, Calendar, User, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { PenaltyReason, Profile } from '@/types/database'

interface PenaltyRecordDisplay {
  id: string
  issued_date: string
  points: number
  description: string | null
  reason: PenaltyReason | null
  issuer: Pick<Profile, 'name' | 'student_number'>
  targets: Array<Pick<Profile, 'id' | 'name' | 'student_number'>>
}

export default function PenaltiesPage() {
  const { user, profile } = useAuth()
  const [records, setRecords] = useState<PenaltyRecordDisplay[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState<string | null>(null)

  const supabase = createClient()
  const isTeacher = profile?.role === 'teacher' || profile?.role === 'admin'

  useEffect(() => {
    fetchRecords()
  }, [user])

  const fetchRecords = async () => {
    if (!user) return
    setLoading(true)

    try {
      // Fetch penalty records with relations
      const { data: recordsData, error } = await supabase
        .from('penalty_records')
        .select(`
          id,
          issued_date,
          points,
          description,
          reason:penalty_reasons (id, title, points, category),
          issuer:profiles!penalty_records_issued_by_fkey (name, student_number)
        `)
        .order('issued_date', { ascending: false })
        .order('created_at', { ascending: false })

      if (error) throw error

      // Fetch targets for each record
      const recordIds = recordsData?.map((r) => r.id) || []

      const { data: targetsData } = await supabase
        .from('penalty_record_targets')
        .select(`
          record_id,
          user:profiles (id, name, student_number)
        `)
        .in('record_id', recordIds)

      // Map targets to records
      const recordsWithTargets = recordsData?.map((record) => ({
        ...record,
        reason: record.reason as unknown as PenaltyReason | null,
        issuer: record.issuer as unknown as Pick<Profile, 'name' | 'student_number'>,
        targets: targetsData
          ?.filter((t) => t.record_id === record.id)
          .map((t) => t.user as unknown as Pick<Profile, 'id' | 'name' | 'student_number'>) || [],
      })) || []

      setRecords(recordsWithTargets)
    } catch (error) {
      console.error('Error fetching records:', error)
    } finally {
      setLoading(false)
    }
  }

  // Filter records
  const filteredRecords = records.filter((record) => {
    // Search filter
    const searchLower = searchQuery.toLowerCase()
    const matchesSearch =
      !searchQuery ||
      record.reason?.title.toLowerCase().includes(searchLower) ||
      record.issuer.name.toLowerCase().includes(searchLower) ||
      record.targets.some(
        (t) =>
          t.name.toLowerCase().includes(searchLower) ||
          t.student_number?.toLowerCase().includes(searchLower)
      )

    // Category filter
    const matchesCategory = !filterCategory || record.reason?.category === filterCategory

    return matchesSearch && matchesCategory
  })

  // Get unique categories
  const categories = [...new Set(records.map((r) => r.reason?.category).filter(Boolean))] as string[]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">벌점 기록</h1>
        {isTeacher && (
          <Link href="/penalties/give">
            <Button variant="primary">
              <Plus className="h-4 w-4 mr-2" />
              벌점 부여
            </Button>
          </Link>
        )}
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
          <Input
            type="search"
            placeholder="사유, 이름, 학번으로 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-background-secondary border-border"
          />
        </div>
        <div className="flex gap-1 overflow-x-auto pb-1">
          <button
            onClick={() => setFilterCategory(null)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors',
              filterCategory === null
                ? 'bg-accent text-white'
                : 'bg-background-secondary hover:bg-background-secondary/80'
            )}
          >
            전체
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setFilterCategory(category)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors',
                filterCategory === category
                  ? 'bg-accent text-white'
                  : 'bg-background-secondary hover:bg-background-secondary/80'
              )}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Stats for current user (if student) */}
      {!isTeacher && profile && (
        <div className="rounded-lg border border-border bg-background-secondary p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-foreground-secondary">내 총 벌점</p>
              <p className="text-2xl font-bold">{profile.total_penalty || 0}점</p>
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
              {(profile.total_penalty || 0) > 0 ? '+' : ''}{profile.total_penalty || 0}
            </Badge>
          </div>
        </div>
      )}

      {/* Table Headers */}
      <div className="grid grid-cols-12 gap-4 px-4 py-2 text-sm text-foreground-secondary border-b border-border">
        <div className="col-span-2">날짜</div>
        <div className="col-span-5">사유</div>
        <div className="col-span-3">대상</div>
        <div className="col-span-2 text-right">점수</div>
      </div>

      {/* Records */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </div>
      ) : filteredRecords.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-foreground-secondary">
          <AlertTriangle className="h-12 w-12 mb-4 opacity-50" />
          <p>벌점 기록이 없습니다</p>
        </div>
      ) : (
        <div className="divide-y divide-border">
          {filteredRecords.map((record) => (
            <div
              key={record.id}
              className="grid grid-cols-12 gap-4 px-4 py-3 hover:bg-background-secondary/50 transition-colors"
            >
              {/* Date */}
              <div className="col-span-2">
                <p className="text-sm font-medium">
                  {format(new Date(record.issued_date), 'M/d', { locale: ko })}
                </p>
                <p className="text-xs text-foreground-secondary">
                  {record.issuer.name}
                </p>
              </div>

              {/* Reason */}
              <div className="col-span-5">
                <p className="font-medium text-sm">
                  {record.reason?.title || '(삭제된 사유)'}
                </p>
                {record.reason?.category && (
                  <span className="text-xs text-foreground-secondary">
                    {record.reason.category}
                  </span>
                )}
                {record.description && (
                  <p className="text-xs text-foreground-secondary mt-1">{record.description}</p>
                )}
              </div>

              {/* Targets */}
              <div className="col-span-3">
                {record.targets.length === 0 ? (
                  <p className="text-sm text-foreground-secondary">-</p>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {record.targets.slice(0, 3).map((target) => (
                      <span key={target.id} className="text-xs bg-background-secondary px-2 py-0.5 rounded">
                        {target.student_number?.slice(-4)} {target.name}
                      </span>
                    ))}
                    {record.targets.length > 3 && (
                      <span className="text-xs text-foreground-secondary">
                        +{record.targets.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Points */}
              <div className="col-span-2 text-right">
                <Badge
                  className={cn(
                    'text-sm',
                    record.points < 0
                      ? 'bg-green-500/10 text-green-500 border-green-500/20'
                      : 'bg-red-500/10 text-red-500 border-red-500/20'
                  )}
                >
                  {record.points > 0 ? '+' : ''}{record.points}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info */}
      <p className="text-xs text-foreground-secondary text-center mt-8">
        {filteredRecords.length}개의 기록
      </p>
    </div>
  )
}

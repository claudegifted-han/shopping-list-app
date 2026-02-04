'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { AlertTriangle, Search, Calendar, User, Plus, Filter } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
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
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <AlertTriangle className="h-6 w-6" />
          벌점 기록
        </h1>
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
            className="pl-9"
          />
        </div>
        <div className="flex gap-1 overflow-x-auto pb-1">
          <Button
            variant={filterCategory === null ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilterCategory(null)}
          >
            전체
          </Button>
          {categories.map((category) => (
            <Button
              key={category}
              variant={filterCategory === category ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setFilterCategory(category)}
            >
              {category}
            </Button>
          ))}
        </div>
      </div>

      {/* Stats for current user (if student) */}
      {!isTeacher && profile && (
        <Card className="mb-6">
          <CardContent className="flex items-center justify-between py-4">
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
          </CardContent>
        </Card>
      )}

      {/* Records */}
      <div className="space-y-4">
        {loading ? (
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            </CardContent>
          </Card>
        ) : filteredRecords.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-foreground-secondary">
              <AlertTriangle className="h-12 w-12 mb-4 opacity-50" />
              <p>벌점 기록이 없습니다</p>
            </CardContent>
          </Card>
        ) : (
          filteredRecords.map((record) => (
            <Card key={record.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="flex items-center gap-1 text-sm text-foreground-secondary">
                        <Calendar className="h-4 w-4" />
                        {format(new Date(record.issued_date), 'M월 d일', { locale: ko })}
                      </span>
                      <span className="flex items-center gap-1 text-sm text-foreground-secondary">
                        <User className="h-4 w-4" />
                        부과 교사: {record.issuer.name}
                      </span>
                      {record.reason?.category && (
                        <Badge variant="secondary" className="text-xs">
                          {record.reason.category}
                        </Badge>
                      )}
                    </div>
                    <p className="font-medium">{record.reason?.title || '(삭제된 사유)'}</p>
                    {record.description && (
                      <p className="text-sm text-foreground-secondary">{record.description}</p>
                    )}
                    {record.targets.length === 0 ? (
                      <p className="text-sm text-foreground-secondary">(적용된 대상 없음)</p>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {record.targets.map((target) => (
                          <Badge key={target.id} variant="secondary" className="text-xs">
                            {target.student_number} {target.name}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <Badge
                    className={cn(
                      'ml-4 text-base',
                      record.points < 0
                        ? 'bg-green-500/10 text-green-500 border-green-500/20'
                        : 'bg-red-500/10 text-red-500 border-red-500/20'
                    )}
                  >
                    {record.points > 0 ? '+' : ''}{record.points}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Info */}
      <p className="text-xs text-foreground-secondary text-center mt-8">
        {filteredRecords.length}개의 기록
      </p>
    </div>
  )
}

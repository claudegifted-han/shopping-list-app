'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { AlertTriangle, Search, Check, X, Eye, EyeOff, Users } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { Profile, PenaltyReason } from '@/types/database'

export default function PenaltyGivePage() {
  const router = useRouter()
  const { user, profile } = useAuth()
  const [students, setStudents] = useState<Profile[]>([])
  const [reasons, setReasons] = useState<PenaltyReason[]>([])
  const [selectedStudents, setSelectedStudents] = useState<Profile[]>([])
  const [selectedReason, setSelectedReason] = useState<PenaltyReason | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showPreview, setShowPreview] = useState(true)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [step, setStep] = useState<'students' | 'reason'>('students')

  const supabase = createClient()
  const isTeacher = profile?.role === 'teacher' || profile?.role === 'admin'

  useEffect(() => {
    if (isTeacher) {
      fetchData()
    }
  }, [isTeacher])

  const fetchData = async () => {
    setLoading(true)

    try {
      // Fetch students
      const { data: studentsData } = await supabase
        .from('profiles')
        .select('*')
        .eq('role', 'student')
        .order('student_number')

      setStudents(studentsData || [])

      // Fetch active penalty reasons
      const { data: reasonsData } = await supabase
        .from('penalty_reasons')
        .select('*')
        .eq('is_active', true)
        .order('category')
        .order('points')

      setReasons(reasonsData || [])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleStudent = (student: Profile) => {
    setSelectedStudents((prev) => {
      const exists = prev.find((s) => s.id === student.id)
      if (exists) {
        return prev.filter((s) => s.id !== student.id)
      }
      return [...prev, student]
    })
  }

  const handleSubmit = async () => {
    if (!user || !selectedReason || selectedStudents.length === 0 || submitting) return

    if (!confirm(`${selectedStudents.length}명에게 "${selectedReason.title}" (${selectedReason.points > 0 ? '+' : ''}${selectedReason.points}점)을 부과하시겠습니까?`)) {
      return
    }

    setSubmitting(true)

    try {
      // Create penalty record
      const { data: record, error: recordError } = await supabase
        .from('penalty_records')
        .insert({
          reason_id: selectedReason.id,
          issued_by: user.id,
          points: selectedReason.points,
          description: null,
        })
        .select()
        .single()

      if (recordError) throw recordError

      // Create targets
      const targets = selectedStudents.map((student) => ({
        record_id: record.id,
        user_id: student.id,
      }))

      const { error: targetsError } = await supabase
        .from('penalty_record_targets')
        .insert(targets)

      if (targetsError) throw targetsError

      // Create notifications for each student
      const notifications = selectedStudents.map((student) => ({
        user_id: student.id,
        title: selectedReason.points > 0 ? '벌점이 부과되었습니다' : '상점이 부여되었습니다',
        message: `${selectedReason.title} (${selectedReason.points > 0 ? '+' : ''}${selectedReason.points}점)`,
        type: 'penalty' as const,
        related_id: record.id,
      }))

      await supabase.from('notifications').insert(notifications)

      alert('벌점이 성공적으로 부과되었습니다.')
      router.push('/penalties')
    } catch (error) {
      console.error('Error submitting:', error)
      alert('벌점 부과 중 오류가 발생했습니다.')
    } finally {
      setSubmitting(false)
    }
  }

  const filteredStudents = students.filter(
    (student) =>
      student.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      student.student_number?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Group reasons by category
  const reasonsByCategory = reasons.reduce((acc, reason) => {
    const category = reason.category || '기타'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(reason)
    return acc
  }, {} as Record<string, PenaltyReason[]>)

  if (!isTeacher) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-foreground-secondary">교사만 접근할 수 있는 페이지입니다.</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <AlertTriangle className="h-6 w-6" />
          벌점 부여
        </h1>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
            미리보기 {showPreview ? 'OFF' : 'ON'}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Step 1: Select Students */}
          <Card className={cn(step === 'students' && 'border-accent')}>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  대상 선택
                </span>
                {selectedStudents.length > 0 && (
                  <Badge variant="secondary">{selectedStudents.length}명 선택</Badge>
                )}
              </CardTitle>
              <CardDescription>
                벌점을 부과할 학생을 선택하세요 (다중 선택 가능)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {step === 'students' ? (
                <>
                  <div className="relative mb-4">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
                    <Input
                      type="search"
                      placeholder="학번, 이름으로 검색..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>

                  {loading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                    </div>
                  ) : (
                    <div className="max-h-64 overflow-y-auto space-y-1">
                      {filteredStudents.map((student) => {
                        const isSelected = selectedStudents.some((s) => s.id === student.id)
                        return (
                          <button
                            key={student.id}
                            onClick={() => toggleStudent(student)}
                            className={cn(
                              'w-full flex items-center justify-between p-2 rounded-lg transition-colors',
                              isSelected
                                ? 'bg-accent text-white'
                                : 'bg-background-secondary hover:bg-background-secondary/80'
                            )}
                          >
                            <span className="text-sm">
                              {student.student_number} {student.name}
                            </span>
                            {isSelected && <Check className="h-4 w-4" />}
                          </button>
                        )
                      })}
                    </div>
                  )}

                  {selectedStudents.length > 0 && (
                    <div className="flex justify-end mt-4 pt-4 border-t border-border">
                      <Button onClick={() => setStep('reason')}>
                        다음: 사유 선택
                      </Button>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {selectedStudents.map((student) => (
                      <Badge key={student.id} variant="secondary">
                        {student.student_number} {student.name}
                      </Badge>
                    ))}
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => setStep('students')}>
                    수정
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 2: Select Reason */}
          {step === 'reason' && (
            <Card className="border-accent">
              <CardHeader className="pb-3">
                <CardTitle>사유 선택</CardTitle>
                <CardDescription>
                  벌점 사유를 선택하세요
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(reasonsByCategory).map(([category, categoryReasons]) => (
                    <div key={category}>
                      <h4 className="text-sm font-medium text-foreground-secondary mb-2">{category}</h4>
                      <div className="space-y-1">
                        {categoryReasons.map((reason) => {
                          const isSelected = selectedReason?.id === reason.id
                          return (
                            <button
                              key={reason.id}
                              onClick={() => setSelectedReason(reason)}
                              className={cn(
                                'w-full flex items-center justify-between p-3 rounded-lg transition-colors text-left',
                                isSelected
                                  ? 'bg-accent text-white'
                                  : 'bg-background-secondary hover:bg-background-secondary/80'
                              )}
                            >
                              <span className="text-sm">{reason.title}</span>
                              <Badge
                                className={cn(
                                  isSelected
                                    ? 'bg-white/20 text-white border-white/30'
                                    : reason.points < 0
                                      ? 'bg-green-500/10 text-green-500 border-green-500/20'
                                      : 'bg-red-500/10 text-red-500 border-red-500/20'
                                )}
                              >
                                {reason.points > 0 ? '+' : ''}{reason.points}
                              </Badge>
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar - Preview */}
        <div className="space-y-4">
          {showPreview && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">미리보기</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedStudents.length === 0 ? (
                  <p className="text-sm text-foreground-secondary text-center py-4">
                    대상 학생을 선택하세요
                  </p>
                ) : !selectedReason ? (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">대상</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedStudents.map((student) => (
                        <Badge key={student.id} variant="secondary" className="text-xs">
                          {student.student_number} {student.name}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-sm text-foreground-secondary mt-4 text-center">
                      사유를 선택하세요
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-foreground-secondary mb-1">대상</p>
                      <div className="flex flex-wrap gap-1">
                        {selectedStudents.map((student) => (
                          <Badge key={student.id} variant="secondary" className="text-xs">
                            {student.student_number} {student.name}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-foreground-secondary mb-1">사유</p>
                      <p className="text-sm font-medium">{selectedReason.title}</p>
                    </div>
                    <div>
                      <p className="text-sm text-foreground-secondary mb-1">점수</p>
                      <Badge
                        className={
                          selectedReason.points < 0
                            ? 'bg-green-500/10 text-green-500 border-green-500/20'
                            : 'bg-red-500/10 text-red-500 border-red-500/20'
                        }
                      >
                        {selectedReason.points > 0 ? '+' : ''}{selectedReason.points}점
                      </Badge>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Submit Button */}
          {selectedStudents.length > 0 && selectedReason && (
            <Button
              className="w-full bg-red-600 hover:bg-red-700 text-white"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-2" />
              ) : (
                <AlertTriangle className="h-4 w-4 mr-2" />
              )}
              벌점 부여
            </Button>
          )}

          {/* Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">안내</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-foreground-secondary">
                <li>• 벌점은 양수, 상점은 음수입니다</li>
                <li>• 부과 후 취소가 불가능합니다</li>
                <li>• 대상 학생에게 알림이 전송됩니다</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

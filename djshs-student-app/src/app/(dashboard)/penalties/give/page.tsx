'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { AlertTriangle, Search, Check, X, Star, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { Profile, PenaltyReason } from '@/types/database'

type StudentModalTab = 'list' | 'direct' | 'search'
type ReasonTab = 'favorites' | 'list' | 'direct'

// Avatar colors based on student number
const avatarColors = [
  'from-purple-500 to-pink-500',
  'from-blue-500 to-cyan-500',
  'from-green-500 to-teal-500',
  'from-orange-500 to-red-500',
  'from-yellow-500 to-orange-500',
  'from-pink-500 to-rose-500',
  'from-indigo-500 to-purple-500',
  'from-cyan-500 to-blue-500',
]

const getAvatarColor = (studentNumber: string | null) => {
  if (!studentNumber) return avatarColors[0]
  const num = parseInt(studentNumber.slice(-2)) || 0
  return avatarColors[num % avatarColors.length]
}

export default function PenaltyGivePage() {
  const router = useRouter()
  const { user, profile } = useAuth()
  const [students, setStudents] = useState<Profile[]>([])
  const [reasons, setReasons] = useState<PenaltyReason[]>([])
  const [selectedStudents, setSelectedStudents] = useState<Profile[]>([])
  const [selectedReason, setSelectedReason] = useState<{ title: string; points: number; id?: string } | null>(null)
  const [showPreview, setShowPreview] = useState(true)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  // Student modal state
  const [showStudentModal, setShowStudentModal] = useState(false)
  const [studentModalTab, setStudentModalTab] = useState<StudentModalTab>('list')
  const [selectedGrade, setSelectedGrade] = useState<number>(1)
  const [selectedClass, setSelectedClass] = useState<number | '*'>('*')
  const [studentSearchQuery, setStudentSearchQuery] = useState('')
  const [directInputStudents, setDirectInputStudents] = useState<Profile[]>([])
  const [directInputText, setDirectInputText] = useState('')

  // Reason dropdown state
  const [showReasonDropdown, setShowReasonDropdown] = useState(false)
  const [reasonTab, setReasonTab] = useState<ReasonTab>('list')
  const [reasonSearchQuery, setReasonSearchQuery] = useState('')
  const [customReason, setCustomReason] = useState('')
  const [customPoints, setCustomPoints] = useState('')
  const [favoriteReasons, setFavoriteReasons] = useState<string[]>([])

  const supabase = createClient()
  const isTeacher = profile?.role === 'teacher' || profile?.role === 'admin'

  useEffect(() => {
    if (isTeacher) {
      fetchData()
      const saved = localStorage.getItem('penalty_favorite_reasons')
      if (saved) {
        setFavoriteReasons(JSON.parse(saved))
      }
    }
  }, [isTeacher])

  const fetchData = async () => {
    setLoading(true)

    try {
      const { data: studentsData } = await supabase
        .from('profiles')
        .select('*')
        .eq('role', 'student')
        .order('student_number')

      setStudents(studentsData || [])

      const { data: reasonsData } = await supabase
        .from('penalty_reasons')
        .select('*')
        .eq('is_active', true)
        .order('points')

      setReasons(reasonsData || [])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const parseStudentNumber = (studentNumber: string | null) => {
    if (!studentNumber || studentNumber.length < 4) return { grade: null, classNum: null }
    const grade = parseInt(studentNumber[0])
    const classNum = parseInt(studentNumber[1])
    return { grade, classNum }
  }

  const filteredStudentsForList = useMemo(() => {
    return students.filter((student) => {
      const { grade, classNum } = parseStudentNumber(student.student_number)
      if (grade !== selectedGrade) return false
      if (selectedClass !== '*' && classNum !== selectedClass) return false
      return true
    })
  }, [students, selectedGrade, selectedClass])

  const filteredStudentsForSearch = useMemo(() => {
    if (!studentSearchQuery.trim()) return []
    const query = studentSearchQuery.toLowerCase()
    return students.filter(
      (student) =>
        student.name.toLowerCase().includes(query) ||
        student.student_number?.toLowerCase().includes(query)
    )
  }, [students, studentSearchQuery])

  const filteredReasons = useMemo(() => {
    if (!reasonSearchQuery.trim()) return reasons
    const query = reasonSearchQuery.toLowerCase()
    return reasons.filter(
      (reason) =>
        reason.title.toLowerCase().includes(query) ||
        reason.points.toString().includes(query)
    )
  }, [reasons, reasonSearchQuery])

  const favoriteReasonsList = useMemo(() => {
    return reasons.filter((r) => favoriteReasons.includes(r.id))
  }, [reasons, favoriteReasons])

  const toggleStudent = (student: Profile) => {
    setSelectedStudents((prev) => {
      const exists = prev.find((s) => s.id === student.id)
      if (exists) {
        return prev.filter((s) => s.id !== student.id)
      }
      return [...prev, student]
    })
  }

  const toggleAllStudents = (studentsList: Profile[]) => {
    const allSelected = studentsList.every((s) => selectedStudents.some((sel) => sel.id === s.id))
    if (allSelected) {
      setSelectedStudents((prev) => prev.filter((s) => !studentsList.some((ls) => ls.id === s.id)))
    } else {
      setSelectedStudents((prev) => {
        const newSelection = [...prev]
        studentsList.forEach((s) => {
          if (!newSelection.some((ns) => ns.id === s.id)) {
            newSelection.push(s)
          }
        })
        return newSelection
      })
    }
  }

  const toggleFavorite = (reasonId: string) => {
    setFavoriteReasons((prev) => {
      const newFavorites = prev.includes(reasonId)
        ? prev.filter((id) => id !== reasonId)
        : [...prev, reasonId]
      localStorage.setItem('penalty_favorite_reasons', JSON.stringify(newFavorites))
      return newFavorites
    })
  }

  const handleDirectInput = () => {
    if (!directInputText.trim()) return
    const query = directInputText.trim().toLowerCase()
    const found = students.find(
      (s) =>
        s.student_number?.toLowerCase() === query ||
        s.name.toLowerCase() === query
    )
    if (found) {
      if (!directInputStudents.some((s) => s.id === found.id)) {
        setDirectInputStudents((prev) => [...prev, found])
      }
      setDirectInputText('')
    } else {
      alert('학생을 찾을 수 없습니다.')
    }
  }

  const applyCustomReason = () => {
    if (!customReason.trim() || !customPoints) {
      alert('사유와 점수를 모두 입력하세요.')
      return
    }
    const points = parseInt(customPoints)
    if (isNaN(points)) {
      alert('점수는 숫자로 입력하세요.')
      return
    }
    setSelectedReason({ title: customReason, points })
    setShowReasonDropdown(false)
  }

  const handleSubmit = async () => {
    if (!user || !selectedReason || selectedStudents.length === 0 || submitting) return

    if (!confirm(`${selectedStudents.length}명에게 "${selectedReason.title}" (${selectedReason.points > 0 ? '+' : ''}${selectedReason.points}점)을 부과하시겠습니까?`)) {
      return
    }

    setSubmitting(true)

    try {
      const { data: record, error: recordError } = await supabase
        .from('penalty_records')
        .insert({
          reason_id: selectedReason.id || null,
          issued_by: user.id,
          points: selectedReason.points,
          description: selectedReason.id ? null : selectedReason.title,
        })
        .select()
        .single()

      if (recordError) throw recordError

      const targets = selectedStudents.map((student) => ({
        record_id: record.id,
        user_id: student.id,
      }))

      const { error: targetsError } = await supabase
        .from('penalty_record_targets')
        .insert(targets)

      if (targetsError) throw targetsError

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

  const resetStudentSelection = () => {
    setSelectedStudents([])
    setDirectInputStudents([])
  }

  // Generate email from student number
  const getStudentEmail = (studentNumber: string | null) => {
    if (!studentNumber) return ''
    return `${studentNumber.slice(0, 2)}th${studentNumber.slice(2)}@djshs.djsch.kr`
  }

  if (!isTeacher) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-foreground-secondary">교사만 접근할 수 있는 페이지입니다.</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">벌점 부여</h1>

      {/* Target Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">대상</label>
        <button
          onClick={() => setShowStudentModal(true)}
          className={cn(
            'w-full p-4 rounded-lg border text-center transition-colors',
            selectedStudents.length > 0
              ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400'
              : 'border-border bg-background-secondary hover:border-accent text-foreground-secondary'
          )}
        >
          {selectedStudents.length > 0 ? (
            <span className="font-medium">
              {selectedStudents.map((s) => `${s.student_number} ${s.name}`).join(', ')}
            </span>
          ) : (
            '클릭해서 대상 선택...'
          )}
        </button>
      </div>

      {/* Reason Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">사유</label>
        <button
          onClick={() => setShowReasonDropdown(!showReasonDropdown)}
          className={cn(
            'w-full p-4 rounded-lg border text-center transition-colors',
            selectedReason
              ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400'
              : 'border-border bg-background-secondary hover:border-accent text-foreground-secondary'
          )}
        >
          {selectedReason ? (
            <span className="font-medium">
              {selectedReason.title} ({selectedReason.points > 0 ? '+' : ''}{selectedReason.points}점)
            </span>
          ) : (
            '클릭해서 사유 선택...'
          )}
        </button>

        {/* Inline Reason Dropdown */}
        {showReasonDropdown && (
          <div className="mt-2 border border-border rounded-lg bg-background overflow-hidden">
            {/* Tabs */}
            <div className="flex border-b border-border">
              {[
                { id: 'favorites', label: '☆' },
                { id: 'list', label: '목록' },
                { id: 'direct', label: '직접 입력' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setReasonTab(tab.id as ReasonTab)}
                  className={cn(
                    'flex-1 py-2 text-center text-sm font-medium transition-colors',
                    reasonTab === tab.id
                      ? 'bg-accent text-white'
                      : 'hover:bg-background-secondary'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="p-3">
              {reasonTab === 'favorites' && (
                <>
                  {favoriteReasonsList.length === 0 ? (
                    <p className="text-foreground-secondary text-center py-4 text-sm">
                      즐겨찾기한 사유가 없습니다.
                    </p>
                  ) : (
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {favoriteReasonsList.map((reason) => (
                        <button
                          key={reason.id}
                          onClick={() => {
                            setSelectedReason({ title: reason.title, points: reason.points, id: reason.id })
                            setShowReasonDropdown(false)
                          }}
                          className="w-full flex items-center justify-between p-2 rounded hover:bg-background-secondary transition-colors text-sm"
                        >
                          <div className="flex items-center gap-2">
                            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                            <span>{reason.title}</span>
                          </div>
                          <span>{reason.points}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}

              {reasonTab === 'list' && (
                <>
                  <Input
                    placeholder="내용 또는 점수로 검색"
                    value={reasonSearchQuery}
                    onChange={(e) => setReasonSearchQuery(e.target.value)}
                    className="mb-3 text-sm"
                  />

                  {/* Table Header */}
                  <div className="flex items-center py-2 px-2 border-b border-border text-xs text-foreground-secondary">
                    <div className="w-6">☆</div>
                    <div className="flex-1">내용</div>
                    <div className="w-12 text-right">점수</div>
                  </div>

                  {/* Table Body */}
                  <div className="max-h-48 overflow-y-auto">
                    {filteredReasons.map((reason) => {
                      const isFavorite = favoriteReasons.includes(reason.id)
                      return (
                        <button
                          key={reason.id}
                          onClick={() => {
                            setSelectedReason({ title: reason.title, points: reason.points, id: reason.id })
                            setShowReasonDropdown(false)
                          }}
                          className="w-full flex items-center py-2 px-2 border-b border-border hover:bg-background-secondary transition-colors text-sm"
                        >
                          <div className="w-6">
                            <Star
                              className={cn(
                                'h-3 w-3 cursor-pointer',
                                isFavorite ? 'text-yellow-500 fill-yellow-500' : 'text-foreground-secondary'
                              )}
                              onClick={(e) => {
                                e.stopPropagation()
                                toggleFavorite(reason.id)
                              }}
                            />
                          </div>
                          <div className="flex-1 text-left">{reason.title}</div>
                          <div className="w-12 text-right">{reason.points}</div>
                        </button>
                      )
                    })}
                  </div>
                </>
              )}

              {reasonTab === 'direct' && (
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <Input
                      placeholder="사유"
                      value={customReason}
                      onChange={(e) => setCustomReason(e.target.value)}
                      className="flex-1 text-sm"
                    />
                    <Input
                      type="number"
                      placeholder="점수"
                      value={customPoints}
                      onChange={(e) => setCustomPoints(e.target.value)}
                      className="w-20 text-sm"
                    />
                  </div>
                  <div className="flex justify-end">
                    <Button size="sm" onClick={applyCustomReason}>
                      적용
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Preview Toggle */}
      <label className="flex items-center gap-2 mb-6 cursor-pointer">
        <input
          type="checkbox"
          checked={showPreview}
          onChange={(e) => setShowPreview(e.target.checked)}
          className="rounded border-border"
        />
        <span className="text-sm">미리보기 표시</span>
      </label>

      {/* Preview */}
      {showPreview && selectedStudents.length > 0 && selectedReason && (
        <div className="mb-6 p-4 rounded-lg border border-border bg-background-secondary">
          <p className="text-sm text-foreground-secondary mb-2">미리보기</p>
          <p className="font-medium">{selectedStudents.length}명에게</p>
          <p className="text-lg">
            "{selectedReason.title}"
            <Badge className={cn(
              'ml-2',
              selectedReason.points > 0
                ? 'bg-red-500/10 text-red-500 border-red-500/20'
                : 'bg-green-500/10 text-green-500 border-green-500/20'
            )}>
              {selectedReason.points > 0 ? '+' : ''}{selectedReason.points}점
            </Badge>
          </p>
        </div>
      )}

      {/* Submit Button */}
      <Button
        className="w-auto px-6 bg-red-600 hover:bg-red-700 text-white"
        onClick={handleSubmit}
        disabled={submitting || selectedStudents.length === 0 || !selectedReason}
      >
        {submitting ? (
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-2" />
        ) : null}
        벌점 부여
      </Button>

      {/* Validation Message */}
      {(selectedStudents.length === 0 || !selectedReason) && (
        <p className="text-sm text-red-500 mt-4">
          대상과 사유를 입력하세요.
        </p>
      )}

      {/* Student Selection Modal */}
      {showStudentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-background rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
            {/* Tabs */}
            <div className="flex border-b border-border">
              {[
                { id: 'list', label: '목록' },
                { id: 'direct', label: '직접 입력' },
                { id: 'search', label: '검색' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setStudentModalTab(tab.id as StudentModalTab)}
                  className={cn(
                    'flex-1 py-3 text-center font-medium transition-colors',
                    studentModalTab === tab.id
                      ? 'bg-accent text-white'
                      : 'hover:bg-background-secondary'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-4">
              {studentModalTab === 'list' && (
                <>
                  {/* Grade Filter */}
                  <div className="flex items-center gap-4 mb-4">
                    <span className="text-sm font-medium">학년</span>
                    <div className="flex gap-1">
                      {[1, 2, 3].map((grade) => (
                        <button
                          key={grade}
                          onClick={() => setSelectedGrade(grade)}
                          className={cn(
                            'w-8 h-8 rounded text-sm font-medium',
                            selectedGrade === grade
                              ? 'bg-accent text-white'
                              : 'bg-background-secondary hover:bg-background-secondary/80'
                          )}
                        >
                          {grade}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Class Filter */}
                  <div className="flex items-center gap-4 mb-4">
                    <span className="text-sm font-medium">반</span>
                    <div className="flex gap-1">
                      {(['*', 1, 2, 3, 4, 5, 6] as (number | '*')[]).map((cls) => (
                        <button
                          key={cls}
                          onClick={() => setSelectedClass(cls)}
                          className={cn(
                            'w-8 h-8 rounded text-sm font-medium',
                            selectedClass === cls
                              ? 'bg-accent text-white'
                              : 'bg-background-secondary hover:bg-background-secondary/80'
                          )}
                        >
                          {cls}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Select All */}
                  <label className="flex items-center gap-2 mb-4 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filteredStudentsForList.length > 0 && filteredStudentsForList.every((s) => selectedStudents.some((sel) => sel.id === s.id))}
                      onChange={() => toggleAllStudents(filteredStudentsForList)}
                      className="rounded border-border"
                    />
                    <span className="text-sm">모두 선택({filteredStudentsForList.length})</span>
                  </label>

                  {/* Student Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 max-h-[400px] overflow-y-auto border border-border rounded-lg p-2">
                    {filteredStudentsForList.map((student) => {
                      const isSelected = selectedStudents.some((s) => s.id === student.id)
                      return (
                        <button
                          key={student.id}
                          onClick={() => toggleStudent(student)}
                          className={cn(
                            'flex items-center gap-2 p-2 rounded-lg text-left transition-colors',
                            isSelected
                              ? 'bg-accent/20 border border-accent'
                              : 'hover:bg-background-secondary border border-transparent'
                          )}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {}}
                            className="rounded border-border flex-shrink-0"
                          />
                          <div className={cn(
                            'h-8 w-8 rounded-full bg-gradient-to-br flex items-center justify-center text-white text-xs font-bold flex-shrink-0',
                            getAvatarColor(student.student_number)
                          )}>
                            {student.name[0]}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{student.student_number} {student.name}</p>
                            <p className="text-xs text-foreground-secondary truncate">
                              {getStudentEmail(student.student_number)}
                            </p>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </>
              )}

              {studentModalTab === 'direct' && (
                <>
                  {directInputStudents.length === 0 ? (
                    <p className="text-foreground-secondary text-center py-8">
                      추가된 학생이 없습니다. 하단 입력창에 학번 또는 이름을 입력해 학생을 추가하세요.
                    </p>
                  ) : (
                    <div className="space-y-2 mb-4">
                      {directInputStudents.map((student) => (
                        <div
                          key={student.id}
                          className="flex items-center justify-between p-2 rounded-lg bg-background-secondary"
                        >
                          <span>{student.student_number} {student.name}</span>
                          <button
                            onClick={() => setDirectInputStudents((prev) => prev.filter((s) => s.id !== student.id))}
                            className="text-red-500 hover:text-red-600"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}

              {studentModalTab === 'search' && (
                <>
                  <Input
                    placeholder="학번 또는 이름 입력"
                    value={studentSearchQuery}
                    onChange={(e) => setStudentSearchQuery(e.target.value)}
                    className="mb-4"
                  />

                  {!studentSearchQuery.trim() ? (
                    <p className="text-foreground-secondary text-center py-8">
                      검색어를 입력하세요.
                    </p>
                  ) : filteredStudentsForSearch.length === 0 ? (
                    <p className="text-foreground-secondary text-center py-8">
                      검색 결과가 없습니다.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {filteredStudentsForSearch.map((student) => {
                        const isSelected = selectedStudents.some((s) => s.id === student.id)
                        return (
                          <button
                            key={student.id}
                            onClick={() => toggleStudent(student)}
                            className={cn(
                              'w-full flex items-center justify-between p-3 rounded-lg transition-colors',
                              isSelected
                                ? 'bg-accent text-white'
                                : 'bg-background-secondary hover:bg-background-secondary/80'
                            )}
                          >
                            <span>{student.student_number} {student.name}</span>
                            {isSelected && <Check className="h-4 w-4" />}
                          </button>
                        )
                      })}
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Footer - Direct input field */}
            {studentModalTab === 'direct' && (
              <div className="px-4 pb-2">
                <Input
                  placeholder="학번 또는 이름 입력"
                  value={directInputText}
                  onChange={(e) => setDirectInputText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleDirectInput()}
                />
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between p-4 border-t border-border">
              <span className="text-sm">{selectedStudents.length}명 선택됨</span>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={resetStudentSelection}>
                  초기화
                </Button>
                <Button onClick={() => {
                  if (studentModalTab === 'direct') {
                    directInputStudents.forEach((s) => {
                      if (!selectedStudents.some((sel) => sel.id === s.id)) {
                        setSelectedStudents((prev) => [...prev, s])
                      }
                    })
                  }
                  setShowStudentModal(false)
                }}>
                  닫기
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

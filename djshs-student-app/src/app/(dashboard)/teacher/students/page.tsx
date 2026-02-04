'use client'

import { useState, useEffect, useMemo } from 'react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { Users, Search, ChevronLeft, ChevronRight, SlidersHorizontal, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { Profile } from '@/types/database'

interface StudentWithStats extends Profile {
  study_location?: string | null
}

type SortField = 'student_number' | 'name' | 'total_penalty'
type SortOrder = 'asc' | 'desc'

const ITEMS_PER_PAGE = 20

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

const getStudentEmail = (studentNumber: string | null) => {
  if (!studentNumber) return ''
  return `${studentNumber.slice(0, 2)}th${studentNumber.slice(2)}@djshs.djsch.kr`
}

export default function StudentListPage() {
  const { profile } = useAuth()
  const [students, setStudents] = useState<StudentWithStats[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedStudent, setSelectedStudent] = useState<StudentWithStats | null>(null)
  const [sortField, setSortField] = useState<SortField>('student_number')
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')
  const [showSortMenu, setShowSortMenu] = useState(false)

  const supabase = createClient()
  const today = format(new Date(), 'yyyy-MM-dd')
  const isTeacher = profile?.role === 'teacher' || profile?.role === 'admin'

  useEffect(() => {
    if (isTeacher) {
      fetchStudents()
    }
  }, [isTeacher])

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (target.closest('[data-dropdown-menu]')) return
      setShowSortMenu(false)
    }

    if (showSortMenu) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showSortMenu])

  const fetchStudents = async () => {
    setLoading(true)

    try {
      // Fetch all students
      const { data: studentsData, error: studentsError } = await supabase
        .from('profiles')
        .select('*')
        .eq('role', 'student')
        .order('student_number')

      if (studentsError) throw studentsError

      // Fetch today's study applications
      const { data: studyData } = await supabase
        .from('study_applications')
        .select(`
          user_id,
          seat:study_seats (room_name, seat_number)
        `)
        .eq('date', today)
        .in('status', ['pending', 'approved'])

      // Map study locations to students
      const studentsWithStats = studentsData?.map((student) => {
        const studyApp = studyData?.find((s) => s.user_id === student.id)
        return {
          ...student,
          study_location: studyApp?.seat
            ? `${(studyApp.seat as unknown as { room_name: string; seat_number: string }).room_name} ${(studyApp.seat as unknown as { room_name: string; seat_number: string }).seat_number}`
            : null,
        }
      }) || []

      setStudents(studentsWithStats)
    } catch (error) {
      console.error('Error fetching students:', error)
    } finally {
      setLoading(false)
    }
  }

  // Filter and sort students
  const filteredAndSortedStudents = useMemo(() => {
    let result = [...students]

    // Filter
    if (searchQuery.trim() && searchQuery !== '*') {
      const query = searchQuery.toLowerCase().trim()
      result = result.filter(
        (student) =>
          student.name.toLowerCase().includes(query) ||
          student.student_number?.toLowerCase().includes(query)
      )
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0

      switch (sortField) {
        case 'student_number':
          comparison = (a.student_number || '').localeCompare(b.student_number || '')
          break
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'total_penalty':
          comparison = (a.total_penalty || 0) - (b.total_penalty || 0)
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return result
  }, [students, searchQuery, sortField, sortOrder])

  // Reset page when filter changes
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, sortField, sortOrder])

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedStudents.length / ITEMS_PER_PAGE)
  const paginatedStudents = filteredAndSortedStudents.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  if (!isTeacher) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-foreground-secondary">교사만 접근할 수 있는 페이지입니다.</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Search and Sort */}
      <div className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
          <Input
            type="search"
            placeholder="학번, 이름으로 검색(모두 검색하려면 *)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-background-secondary border-border"
          />
        </div>
        <div className="relative" data-dropdown-menu>
          <Button
            variant="ghost"
            onClick={() => setShowSortMenu(!showSortMenu)}
            className="px-3 bg-background-secondary hover:bg-background-secondary/80"
          >
            <SlidersHorizontal className="h-4 w-4" />
          </Button>

          {/* Sort Menu */}
          {showSortMenu && (
            <div className="absolute right-0 top-full mt-2 w-40 bg-background-secondary border border-border rounded-lg shadow-lg z-50 p-3">
              <p className="text-sm font-medium mb-2 text-foreground-secondary">정렬 기준</p>
              <div className="space-y-1 mb-3">
                {[
                  { value: 'student_number', label: '학번' },
                  { value: 'name', label: '이름' },
                  { value: 'total_penalty', label: '총 벌점' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setSortField(option.value as SortField)}
                    className="w-full text-left px-2 py-1 rounded text-sm hover:bg-background flex items-center gap-2"
                  >
                    <span className="w-3 text-accent">
                      {sortField === option.value && '•'}
                    </span>
                    {option.label}
                  </button>
                ))}
              </div>

              <p className="text-sm font-medium mb-2 text-foreground-secondary">정렬 순서</p>
              <div className="space-y-1">
                {[
                  { value: 'asc', label: '오름차순' },
                  { value: 'desc', label: '내림차순' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setSortOrder(option.value as SortOrder)}
                    className="w-full text-left px-2 py-1 rounded text-sm hover:bg-background flex items-center gap-2"
                  >
                    <span className="w-3 text-accent">
                      {sortOrder === option.value && '•'}
                    </span>
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Table Headers */}
      <div className="grid grid-cols-3 gap-4 px-4 py-2 text-sm text-foreground-secondary border-b border-border">
        <div>정보</div>
        <div className="text-center">총 벌점</div>
        <div>자습 장소</div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </div>
      ) : !searchQuery.trim() ? (
        <div className="flex flex-col items-center justify-center py-16 text-accent">
          <p>검색어를 입력하세요. (*를 입력해 모두 선택)</p>
        </div>
      ) : paginatedStudents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-foreground-secondary">
          <Users className="h-12 w-12 mb-4 opacity-50" />
          <p>검색 결과가 없습니다</p>
        </div>
      ) : (
        <>
          {/* Student List */}
          <div className="divide-y divide-border">
            {paginatedStudents.map((student) => (
              <div
                key={student.id}
                className="grid grid-cols-3 gap-4 px-4 py-3 hover:bg-background-secondary/50 cursor-pointer transition-colors"
                onClick={() => setSelectedStudent(student)}
              >
                <div>
                  <p className="font-medium">{student.student_number} {student.name}</p>
                  <p className="text-xs text-foreground-secondary">
                    {student.email || getStudentEmail(student.student_number)}
                  </p>
                </div>
                <div className="flex items-center justify-center">
                  <Badge
                    className={
                      (student.total_penalty || 0) > 0
                        ? 'bg-red-500/10 text-red-500 border-red-500/20'
                        : (student.total_penalty || 0) < 0
                          ? 'bg-green-500/10 text-green-500 border-green-500/20'
                          : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                    }
                  >
                    {student.total_penalty || 0}
                  </Badge>
                </div>
                <div className="flex items-center">
                  {student.study_location ? (
                    <span className="text-sm">{student.study_location}</span>
                  ) : (
                    <span className="text-sm text-foreground-secondary">-</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-border mt-4 px-4">
              <p className="text-sm text-foreground-secondary">
                {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, filteredAndSortedStudents.length)} / {filteredAndSortedStudents.length}
              </p>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Student Detail Modal */}
      {selectedStudent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background border border-border rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className={`h-14 w-14 rounded-full bg-gradient-to-br ${getAvatarColor(selectedStudent.student_number)} flex items-center justify-center`}>
                    <span className="text-xl font-bold text-white">
                      {selectedStudent.name[0]}
                    </span>
                  </div>
                  <div>
                    <p className="font-bold text-lg">{selectedStudent.name}</p>
                    <p className="text-sm text-foreground-secondary">{selectedStudent.student_number}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedStudent(null)}
                  className="p-1 hover:bg-background-secondary rounded"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Info */}
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-2 border-b border-border">
                  <span className="text-foreground-secondary">이메일</span>
                  <span className="text-right">{selectedStudent.email || getStudentEmail(selectedStudent.student_number)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-border">
                  <span className="text-foreground-secondary">성별</span>
                  <span>{selectedStudent.gender || '-'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-border">
                  <span className="text-foreground-secondary">전화번호</span>
                  <span>{selectedStudent.phone || '-'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-border">
                  <span className="text-foreground-secondary">부모님 전화번호</span>
                  <span>{selectedStudent.parent_phone || '-'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-border">
                  <span className="text-foreground-secondary">등록 년도</span>
                  <span>{selectedStudent.registration_year || '-'}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span className="text-foreground-secondary">총 벌점</span>
                  <Badge
                    className={
                      (selectedStudent.total_penalty || 0) > 0
                        ? 'bg-red-500/10 text-red-500 border-red-500/20'
                        : (selectedStudent.total_penalty || 0) < 0
                          ? 'bg-green-500/10 text-green-500 border-green-500/20'
                          : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                    }
                  >
                    {selectedStudent.total_penalty || 0}
                  </Badge>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-foreground-secondary">오늘 자습 장소</span>
                  <span>{selectedStudent.study_location || '-'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

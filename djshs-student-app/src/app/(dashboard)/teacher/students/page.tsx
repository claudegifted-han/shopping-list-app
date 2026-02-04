'use client'

import { useState, useEffect, useMemo } from 'react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { Users, Search, Download, ChevronLeft, ChevronRight, Eye, SlidersHorizontal } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
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

  const handleExport = () => {
    if (filteredAndSortedStudents.length === 0) {
      alert('내보낼 데이터가 없습니다.')
      return
    }

    const headers = ['학번', '이름', '총 벌점', '자습 장소']
    const rows = filteredAndSortedStudents.map((s) => [
      s.student_number || '',
      s.name,
      s.total_penalty?.toString() || '0',
      s.study_location || '-',
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n')

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `학생목록_${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

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
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Users className="h-6 w-6" />
          학생 목록
        </h1>
        <Button variant="default" onClick={handleExport} disabled={filteredAndSortedStudents.length === 0}>
          <Download className="h-4 w-4 mr-2" />
          내보내기
        </Button>
      </div>

      {/* Search and Sort */}
      <div className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
          <Input
            type="search"
            placeholder="학번, 이름으로 검색 (모두 검색하려면 * 입력)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="relative">
          <Button
            variant="default"
            onClick={() => setShowSortMenu(!showSortMenu)}
          >
            <SlidersHorizontal className="h-4 w-4" />
          </Button>

          {/* Sort Menu */}
          {showSortMenu && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-background border border-border rounded-lg shadow-lg z-10 p-3">
              <p className="text-sm font-medium mb-2">정렬 기준</p>
              <div className="space-y-1 mb-3">
                {[
                  { value: 'student_number', label: '학번' },
                  { value: 'name', label: '이름' },
                  { value: 'total_penalty', label: '총 벌점' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setSortField(option.value as SortField)}
                    className={`w-full text-left px-2 py-1 rounded text-sm ${
                      sortField === option.value
                        ? 'bg-accent text-white'
                        : 'hover:bg-background-secondary'
                    }`}
                  >
                    {sortField === option.value && '• '}
                    {option.label}
                  </button>
                ))}
              </div>

              <p className="text-sm font-medium mb-2">정렬 순서</p>
              <div className="space-y-1">
                {[
                  { value: 'asc', label: '오름차순' },
                  { value: 'desc', label: '내림차순' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setSortOrder(option.value as SortOrder)}
                    className={`w-full text-left px-2 py-1 rounded text-sm ${
                      sortOrder === option.value
                        ? 'bg-accent text-white'
                        : 'hover:bg-background-secondary'
                    }`}
                  >
                    {sortOrder === option.value && '• '}
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Click outside to close sort menu */}
      {showSortMenu && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setShowSortMenu(false)}
        />
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">학생 목록</CardTitle>
                  <CardDescription>
                    {format(new Date(), 'M월 d일', { locale: ko })} 기준
                  </CardDescription>
                </div>
                <p className="text-sm text-foreground-secondary">
                  {filteredAndSortedStudents.length}명
                </p>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
              ) : !searchQuery.trim() ? (
                <div className="flex flex-col items-center justify-center py-12 text-foreground-secondary">
                  <Search className="h-12 w-12 mb-4 opacity-50" />
                  <p>검색어를 입력하세요.</p>
                  <p className="text-sm">(*를 입력해 모두 선택)</p>
                </div>
              ) : paginatedStudents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-foreground-secondary">
                  <Users className="h-12 w-12 mb-4 opacity-50" />
                  <p>검색 결과가 없습니다</p>
                </div>
              ) : (
                <>
                  {/* Table */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left py-3 px-2 font-medium text-foreground-secondary">정보</th>
                          <th className="text-center py-3 px-2 font-medium text-foreground-secondary">총 벌점</th>
                          <th className="text-left py-3 px-2 font-medium text-foreground-secondary">자습 장소</th>
                          <th className="text-center py-3 px-2 font-medium text-foreground-secondary">상세</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paginatedStudents.map((student) => (
                          <tr
                            key={student.id}
                            className="border-b border-border last:border-0 hover:bg-background-secondary/50 cursor-pointer"
                            onClick={() => setSelectedStudent(student)}
                          >
                            <td className="py-3 px-2">
                              <div>
                                <p className="font-medium">{student.student_number} {student.name}</p>
                                {student.email && (
                                  <p className="text-xs text-foreground-secondary">{student.email}</p>
                                )}
                              </div>
                            </td>
                            <td className="text-center py-3 px-2">
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
                            </td>
                            <td className="py-3 px-2">
                              {student.study_location ? (
                                <span className="text-sm">{student.study_location}</span>
                              ) : (
                                <span className="text-sm text-foreground-secondary">-</span>
                              )}
                            </td>
                            <td className="text-center py-3 px-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedStudent(student)
                                }}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between pt-4 border-t border-border mt-4">
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
            </CardContent>
          </Card>
        </div>

        {/* Detail Panel */}
        <div>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">학생 상세 정보</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedStudent ? (
                <div className="space-y-4">
                  {/* Avatar & Name */}
                  <div className="flex items-center gap-4">
                    <div className="h-16 w-16 rounded-full bg-accent/10 flex items-center justify-center">
                      <span className="text-2xl font-bold text-accent">
                        {selectedStudent.name[0]}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-lg">{selectedStudent.name}</p>
                      <p className="text-sm text-foreground-secondary">{selectedStudent.student_number}</p>
                    </div>
                  </div>

                  {/* Info */}
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between py-2 border-b border-border">
                      <span className="text-foreground-secondary">이메일</span>
                      <span>{selectedStudent.email || '-'}</span>
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
                    <div className="flex justify-between py-2 border-b border-border">
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
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-foreground-secondary">
                  <p>학생을 선택하면</p>
                  <p>상세 정보를 볼 수 있습니다</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

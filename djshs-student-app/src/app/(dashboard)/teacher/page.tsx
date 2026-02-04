'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import {
  DoorOpen,
  Users,
  AlertTriangle,
  ClipboardList,
  BookOpen,
  HelpCircle,
  Download,
  RefreshCw,
  Bell,
  Utensils,
} from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Meal, MealType, OutingType } from '@/types/database'

const outingTypeLabels: Record<OutingType, string> = {
  special_room: '특별실',
  general_outing: '일반외출',
  general_overnight: '일반외박',
  research_outing: '연구외출',
  research_overnight: '연구외박',
}

const quickLinks = [
  { title: '외출 신청', href: '/outing', icon: DoorOpen, color: 'bg-blue-500' },
  { title: '학생 조회', href: '/teacher/students', icon: Users, color: 'bg-green-500' },
  { title: '벌점 부여', href: '/penalties/give', icon: AlertTriangle, color: 'bg-red-500' },
  { title: '벌점 기록', href: '/penalties', icon: ClipboardList, color: 'bg-orange-500' },
  { title: '자습 신청', href: '/study', icon: BookOpen, color: 'bg-purple-500' },
  { title: '도움말', href: '/help', icon: HelpCircle, color: 'bg-gray-500' },
]

const mealTypeLabels: Record<MealType, string> = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
}

interface ExportStats {
  studyToday: number
  dormToday: number
  dormTomorrow: number
  outingToday: number
}

export default function TeacherHomePage() {
  const { profile } = useAuth()
  const [todayMeals, setTodayMeals] = useState<Meal[]>([])
  const [loading, setLoading] = useState(true)
  const [exportStats, setExportStats] = useState<ExportStats>({
    studyToday: 0,
    dormToday: 0,
    dormTomorrow: 0,
    outingToday: 0,
  })
  const [exporting, setExporting] = useState<string | null>(null)

  const supabase = createClient()
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const todayStr = format(today, 'yyyy-MM-dd')
  const tomorrowStr = format(tomorrow, 'yyyy-MM-dd')

  const isTeacher = profile?.role === 'teacher' || profile?.role === 'admin'

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    await Promise.all([fetchTodayMeals(), fetchExportStats()])
    setLoading(false)
  }

  const fetchTodayMeals = async () => {
    const { data } = await supabase
      .from('meals')
      .select('*')
      .eq('date', todayStr)
      .order('meal_type')

    setTodayMeals(data || [])
  }

  const fetchExportStats = async () => {
    // Fetch study applications count for today
    const { count: studyCount } = await supabase
      .from('study_applications')
      .select('*', { count: 'exact', head: true })
      .eq('date', todayStr)
      .in('status', ['pending', 'approved'])

    // Fetch dormitory applications for today
    const { count: dormTodayCount } = await supabase
      .from('dormitory_applications')
      .select('*', { count: 'exact', head: true })
      .eq('date', todayStr)
      .in('status', ['pending', 'approved'])

    // Fetch dormitory applications for tomorrow
    const { count: dormTomorrowCount } = await supabase
      .from('dormitory_applications')
      .select('*', { count: 'exact', head: true })
      .eq('date', tomorrowStr)
      .in('status', ['pending', 'approved'])

    // Fetch outing applications for today
    const { count: outingCount } = await supabase
      .from('outing_applications')
      .select('*', { count: 'exact', head: true })
      .eq('date', todayStr)
      .in('status', ['pending', 'approved'])

    setExportStats({
      studyToday: studyCount || 0,
      dormToday: dormTodayCount || 0,
      dormTomorrow: dormTomorrowCount || 0,
      outingToday: outingCount || 0,
    })
  }

  const getNextMeal = (): { type: MealType; meal: Meal | null } | null => {
    const hour = today.getHours()

    if (hour < 8) {
      return { type: 'breakfast', meal: todayMeals.find((m) => m.meal_type === 'breakfast') || null }
    } else if (hour < 13) {
      return { type: 'lunch', meal: todayMeals.find((m) => m.meal_type === 'lunch') || null }
    } else if (hour < 19) {
      return { type: 'dinner', meal: todayMeals.find((m) => m.meal_type === 'dinner') || null }
    }
    return null
  }

  const downloadCSV = (filename: string, headers: string[], rows: string[][]) => {
    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n')

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleExport = async (type: string) => {
    setExporting(type)

    try {
      if (type === 'study_today') {
        const { data } = await supabase
          .from('study_applications')
          .select(`
            *,
            user:profiles!study_applications_user_id_fkey (name, student_number),
            seat:study_seats (room_name, seat_number)
          `)
          .eq('date', todayStr)
          .in('status', ['pending', 'approved'])
          .order('created_at')

        if (data && data.length > 0) {
          const headers = ['학번', '이름', '독서실', '좌석', '상태', '신청시간']
          const rows = data.map((app) => [
            (app.user as { student_number: string }).student_number || '',
            (app.user as { name: string }).name,
            (app.seat as { room_name: string }).room_name,
            (app.seat as { seat_number: string }).seat_number,
            app.status === 'approved' ? '승인됨' : '대기중',
            format(new Date(app.created_at), 'yyyy-MM-dd HH:mm'),
          ])
          downloadCSV(`자습신청_${format(today, 'yyyyMMdd')}.csv`, headers, rows)
        } else {
          alert('내보낼 데이터가 없습니다.')
        }
      } else if (type === 'dorm_today' || type === 'dorm_tomorrow') {
        const targetDate = type === 'dorm_today' ? todayStr : tomorrowStr
        const { data } = await supabase
          .from('dormitory_applications')
          .select(`
            *,
            user:profiles!dormitory_applications_user_id_fkey (name, student_number)
          `)
          .eq('date', targetDate)
          .in('status', ['pending', 'approved'])
          .order('created_at')

        if (data && data.length > 0) {
          const headers = ['학번', '이름', '상태', '신청시간']
          const rows = data.map((app) => [
            (app.user as { student_number: string }).student_number || '',
            (app.user as { name: string }).name,
            app.status === 'approved' ? '승인됨' : '대기중',
            format(new Date(app.created_at), 'yyyy-MM-dd HH:mm'),
          ])
          const dateLabel = type === 'dorm_today' ? '오늘' : '내일'
          downloadCSV(`기숙사신청_${dateLabel}_${format(today, 'yyyyMMdd')}.csv`, headers, rows)
        } else {
          alert('내보낼 데이터가 없습니다.')
        }
      } else if (type === 'outing_today') {
        const { data } = await supabase
          .from('outing_applications')
          .select(`
            *,
            user:profiles!outing_applications_user_id_fkey (name, student_number)
          `)
          .eq('date', todayStr)
          .in('status', ['pending', 'approved'])
          .order('start_time')

        if (data && data.length > 0) {
          const headers = ['학번', '이름', '유형', '장소', '사유', '시작시간', '종료시간', '상태']
          const rows = data.map((app) => [
            (app.user as { student_number: string }).student_number || '',
            (app.user as { name: string }).name,
            outingTypeLabels[app.type as OutingType] || app.type,
            app.location || '',
            app.reason || '',
            format(new Date(app.start_time), 'HH:mm'),
            format(new Date(app.end_time), 'HH:mm'),
            app.status === 'approved' ? '승인됨' : '대기중',
          ])
          downloadCSV(`외출신청_${format(today, 'yyyyMMdd')}.csv`, headers, rows)
        } else {
          alert('내보낼 데이터가 없습니다.')
        }
      } else if (type === 'penalties_all') {
        // Fetch all penalty records
        const { data: recordsData } = await supabase
          .from('penalty_records')
          .select(`
            id,
            issued_date,
            points,
            reason:penalty_reasons (title, category),
            issuer:profiles!penalty_records_issued_by_fkey (name)
          `)
          .order('issued_date', { ascending: false })

        if (recordsData && recordsData.length > 0) {
          // Fetch targets for all records
          const recordIds = recordsData.map((r) => r.id)
          const { data: targetsData } = await supabase
            .from('penalty_record_targets')
            .select(`
              record_id,
              user:profiles (name, student_number)
            `)
            .in('record_id', recordIds)

          const headers = ['날짜', '사유', '카테고리', '점수', '부과자', '대상']
          const rows = recordsData.map((record) => {
            const targets = targetsData
              ?.filter((t) => t.record_id === record.id)
              .map((t) => {
                const user = t.user as unknown as { student_number: string; name: string }
                return `${user.student_number || ''} ${user.name}`
              })
              .join('; ') || ''
            const reason = record.reason as unknown as { title: string; category: string } | null
            const issuer = record.issuer as unknown as { name: string }
            return [
              record.issued_date,
              reason?.title || '',
              reason?.category || '',
              record.points.toString(),
              issuer.name,
              targets,
            ]
          })
          downloadCSV(`벌점기록_전체_${format(today, 'yyyyMMdd')}.csv`, headers, rows)
        } else {
          alert('내보낼 데이터가 없습니다.')
        }
      }
    } catch (error) {
      console.error('Export error:', error)
      alert('내보내기 중 오류가 발생했습니다.')
    } finally {
      setExporting(null)
    }
  }

  const nextMeal = getNextMeal()

  if (!isTeacher) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-foreground-secondary">교사만 접근할 수 있는 페이지입니다.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">교사 홈</h1>
        <p className="text-foreground-secondary">
          {format(today, 'yyyy년 M월 d일 EEEE', { locale: ko })}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick Links */}
          <div>
            <h2 className="text-lg font-semibold mb-4">빠른 바로가기</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {quickLinks.map((link) => {
                const Icon = link.icon
                return (
                  <Link key={link.href} href={link.href}>
                    <Card className="h-full hover:border-border-accent transition-colors cursor-pointer">
                      <CardContent className="flex flex-col items-center justify-center py-6">
                        <div className={`${link.color} p-3 rounded-lg mb-3`}>
                          <Icon className="h-6 w-6 text-white" />
                        </div>
                        <span className="text-sm font-medium">{link.title}</span>
                      </CardContent>
                    </Card>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Notifications */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                알림
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-foreground-secondary text-center py-4">
                알림이 없습니다
              </p>
            </CardContent>
          </Card>

          {/* Next Meal */}
          {nextMeal && (
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Utensils className="h-5 w-5" />
                    다음 급식 ({mealTypeLabels[nextMeal.type]})
                  </CardTitle>
                  <Link href="/meals">
                    <Button variant="ghost" size="sm">
                      전체 급식 보기
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center py-4">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                  </div>
                ) : nextMeal.meal?.menu ? (
                  <p className="text-sm text-foreground-secondary">
                    {nextMeal.meal.menu}
                  </p>
                ) : (
                  <p className="text-sm text-foreground-secondary">
                    급식 정보가 없습니다
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar - Export Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  내보내기
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={fetchExportStats}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-foreground-secondary">
                기준일: {format(today, 'yyyy년 M월 d일', { locale: ko })}
              </p>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="default"
                size="sm"
                className="w-full justify-between"
                onClick={() => handleExport('study_today')}
                disabled={exporting === 'study_today'}
              >
                <span className="flex items-center">
                  <Download className="h-4 w-4 mr-2" />
                  오늘 자습 신청
                </span>
                <Badge variant="secondary" className="ml-2">{exportStats.studyToday}</Badge>
              </Button>

              <Button
                variant="default"
                size="sm"
                className="w-full justify-between"
                onClick={() => handleExport('dorm_today')}
                disabled={exporting === 'dorm_today'}
              >
                <span className="flex items-center">
                  <Download className="h-4 w-4 mr-2" />
                  오늘 기숙사 신청
                </span>
                <Badge variant="secondary" className="ml-2">{exportStats.dormToday}</Badge>
              </Button>

              <Button
                variant="default"
                size="sm"
                className="w-full justify-between"
                onClick={() => handleExport('dorm_tomorrow')}
                disabled={exporting === 'dorm_tomorrow'}
              >
                <span className="flex items-center">
                  <Download className="h-4 w-4 mr-2" />
                  내일 기숙사 신청
                </span>
                <Badge variant="secondary" className="ml-2">{exportStats.dormTomorrow}</Badge>
              </Button>

              <Button
                variant="default"
                size="sm"
                className="w-full justify-between"
                onClick={() => handleExport('outing_today')}
                disabled={exporting === 'outing_today'}
              >
                <span className="flex items-center">
                  <Download className="h-4 w-4 mr-2" />
                  오늘 외출 신청
                </span>
                <Badge variant="secondary" className="ml-2">{exportStats.outingToday}</Badge>
              </Button>

              <Button
                variant="default"
                size="sm"
                className="w-full justify-between"
                onClick={() => handleExport('penalties_all')}
                disabled={exporting === 'penalties_all'}
              >
                <span className="flex items-center">
                  <Download className="h-4 w-4 mr-2" />
                  전체 벌점 기록
                </span>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

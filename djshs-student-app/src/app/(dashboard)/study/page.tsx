'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { BookOpen, Calendar, MapPin, Clock, Check, X, Users } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { StudySeat, StudyApplication, ApplicationStatus } from '@/types/database'

interface SeatWithApplication extends StudySeat {
  application?: {
    id: string
    user_id: string
    status: ApplicationStatus
    user?: {
      name: string
      student_number: string | null
    }
  } | null
}

const statusLabels: Record<ApplicationStatus, string> = {
  pending: '대기중',
  approved: '승인됨',
  rejected: '거절됨',
  cancelled: '취소됨',
  completed: '완료됨',
}

const statusColors: Record<ApplicationStatus, string> = {
  pending: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  approved: 'bg-green-500/10 text-green-500 border-green-500/20',
  rejected: 'bg-red-500/10 text-red-500 border-red-500/20',
  cancelled: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  completed: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
}

export default function StudyPage() {
  const { user } = useAuth()
  const [selectedDate] = useState(new Date())
  const [seats, setSeats] = useState<SeatWithApplication[]>([])
  const [myApplication, setMyApplication] = useState<(StudyApplication & { seat: StudySeat }) | null>(null)
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  const [selectedSeat, setSelectedSeat] = useState<string | null>(null)
  const [showStatus, setShowStatus] = useState(false)

  const supabase = createClient()
  const dateStr = format(selectedDate, 'yyyy-MM-dd')

  useEffect(() => {
    fetchData()
  }, [selectedDate, user])

  const fetchData = async () => {
    if (!user) return
    setLoading(true)

    try {
      // Fetch all seats
      const { data: seatsData, error: seatsError } = await supabase
        .from('study_seats')
        .select('*')
        .eq('is_available', true)
        .order('room_name')
        .order('seat_number')

      if (seatsError) throw seatsError

      // Fetch today's applications
      const { data: applicationsData, error: applicationsError } = await supabase
        .from('study_applications')
        .select(`
          id,
          user_id,
          seat_id,
          status,
          profiles:user_id (name, student_number)
        `)
        .eq('date', dateStr)

      if (applicationsError) throw applicationsError

      // Map applications to seats
      const seatsWithApplications = seatsData?.map((seat) => {
        const app = applicationsData?.find((a) => a.seat_id === seat.id)
        return {
          ...seat,
          application: app ? {
            id: app.id,
            user_id: app.user_id,
            status: app.status,
            user: app.profiles as unknown as { name: string; student_number: string | null }
          } : null,
        }
      }) || []

      setSeats(seatsWithApplications)

      // Find my application
      const myApp = applicationsData?.find((a) => a.user_id === user.id)
      if (myApp) {
        const seat = seatsData?.find((s) => s.id === myApp.seat_id)
        if (seat) {
          setMyApplication({
            id: myApp.id,
            user_id: myApp.user_id,
            seat_id: myApp.seat_id,
            date: dateStr,
            status: myApp.status,
            created_at: '',
            updated_at: '',
            seat,
          })
        }
      } else {
        setMyApplication(null)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApply = async (seatId: string) => {
    if (!user || applying) return
    setApplying(true)

    try {
      const { error } = await supabase
        .from('study_applications')
        .insert({
          user_id: user.id,
          seat_id: seatId,
          date: dateStr,
          status: 'pending',
        })

      if (error) {
        if (error.code === '23505') {
          alert('이미 신청한 좌석이 있거나 해당 좌석은 이미 신청되었습니다.')
        } else {
          throw error
        }
      } else {
        await fetchData()
        setSelectedSeat(null)
      }
    } catch (error) {
      console.error('Error applying:', error)
      alert('신청 중 오류가 발생했습니다.')
    } finally {
      setApplying(false)
    }
  }

  const handleCancel = async () => {
    if (!myApplication || applying) return
    if (!confirm('자습 신청을 취소하시겠습니까?')) return
    setApplying(true)

    try {
      const { error } = await supabase
        .from('study_applications')
        .update({ status: 'cancelled' })
        .eq('id', myApplication.id)

      if (error) throw error
      await fetchData()
    } catch (error) {
      console.error('Error cancelling:', error)
      alert('취소 중 오류가 발생했습니다.')
    } finally {
      setApplying(false)
    }
  }

  // Group seats by room
  const seatsByRoom = seats.reduce((acc, seat) => {
    if (!acc[seat.room_name]) {
      acc[seat.room_name] = []
    }
    acc[seat.room_name].push(seat)
    return acc
  }, {} as Record<string, SeatWithApplication[]>)

  const canApply = !myApplication || myApplication.status === 'cancelled' || myApplication.status === 'rejected'

  if (showStatus) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Users className="h-6 w-6" />
              자습 신청 현황
            </h1>
            <p className="text-foreground-secondary mt-1">
              {format(selectedDate, 'M월 d일', { locale: ko })}
            </p>
          </div>
          <Button variant="ghost" onClick={() => setShowStatus(false)}>
            돌아가기
          </Button>
        </div>

        <div className="space-y-6">
          {Object.entries(seatsByRoom).map(([roomName, roomSeats]) => (
            <Card key={roomName}>
              <CardHeader>
                <CardTitle>{roomName}</CardTitle>
                <CardDescription>
                  {roomSeats.filter((s) => s.application && s.application.status !== 'cancelled').length} / {roomSeats.length} 신청됨
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                  {roomSeats.map((seat) => {
                    const isOccupied = !!(seat.application && seat.application.status !== 'cancelled')
                    return (
                      <div
                        key={seat.id}
                        className={`p-3 rounded-lg border text-center ${
                          isOccupied
                            ? 'bg-accent/10 border-accent'
                            : 'bg-background-secondary border-border'
                        }`}
                      >
                        <p className="font-medium">{seat.seat_number}</p>
                        {isOccupied && seat.application?.user && (
                          <p className="text-xs text-foreground-secondary mt-1">
                            {seat.application.user.student_number} {seat.application.user.name}
                          </p>
                        )}
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BookOpen className="h-6 w-6" />
            자습 신청
          </h1>
          <p className="text-foreground-secondary mt-1">
            {format(selectedDate, 'M월 d일', { locale: ko })}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* My Application */}
          <Card>
            <CardHeader>
              <CardTitle>신청한 좌석</CardTitle>
              <CardDescription>오늘 신청한 자습 좌석입니다</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
              ) : myApplication && myApplication.status !== 'cancelled' ? (
                <div className="flex items-center justify-between p-4 bg-background-secondary rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-accent/10 flex items-center justify-center">
                      <MapPin className="h-6 w-6 text-accent" />
                    </div>
                    <div>
                      <p className="font-medium">{myApplication.seat.room_name}</p>
                      <p className="text-sm text-foreground-secondary">좌석 {myApplication.seat.seat_number}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge className={statusColors[myApplication.status]}>
                      {statusLabels[myApplication.status]}
                    </Badge>
                    {myApplication.status === 'pending' && (
                      <Button variant="ghost" size="sm" onClick={handleCancel} disabled={applying}>
                        <X className="h-4 w-4 mr-1" />
                        취소
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-foreground-secondary">
                  <MapPin className="h-12 w-12 mb-4 opacity-50" />
                  <p>신청한 좌석이 없습니다</p>
                  <p className="text-sm mt-1">아래에서 좌석을 선택하여 신청하세요</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Seat Selection */}
          {canApply && (
            <Card>
              <CardHeader>
                <CardTitle>좌석 선택</CardTitle>
                <CardDescription>신청할 좌석을 선택하세요</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                  </div>
                ) : (
                  Object.entries(seatsByRoom).map(([roomName, roomSeats]) => (
                    <div key={roomName}>
                      <h3 className="font-medium mb-3">{roomName}</h3>
                      <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
                        {roomSeats.map((seat) => {
                          const isOccupied = !!(seat.application && seat.application.status !== 'cancelled')
                          const isSelected = selectedSeat === seat.id
                          return (
                            <button
                              key={seat.id}
                              onClick={() => !isOccupied && setSelectedSeat(isSelected ? null : seat.id)}
                              disabled={isOccupied}
                              className={`
                                p-2 rounded-lg border text-sm font-medium transition-colors
                                ${isOccupied
                                  ? 'bg-foreground-secondary/10 text-foreground-secondary cursor-not-allowed'
                                  : isSelected
                                    ? 'bg-accent text-white border-accent'
                                    : 'bg-background-secondary border-border hover:border-accent'
                                }
                              `}
                            >
                              {seat.seat_number}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  ))
                )}

                {selectedSeat && (
                  <div className="flex items-center justify-between pt-4 border-t border-border">
                    <div>
                      <p className="text-sm text-foreground-secondary">선택한 좌석</p>
                      <p className="font-medium">
                        {seats.find((s) => s.id === selectedSeat)?.room_name}{' '}
                        {seats.find((s) => s.id === selectedSeat)?.seat_number}
                      </p>
                    </div>
                    <Button onClick={() => handleApply(selectedSeat)} disabled={applying}>
                      {applying ? (
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-2" />
                      ) : (
                        <Check className="h-4 w-4 mr-2" />
                      )}
                      신청하기
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Actions */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">액션</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="default" className="w-full justify-start" onClick={() => setShowStatus(true)}>
                <Calendar className="h-4 w-4 mr-2" />
                신청 현황 보기
              </Button>
              <Button variant="default" className="w-full justify-start">
                <Clock className="h-4 w-4 mr-2" />
                과거 기록 조회
              </Button>
            </CardContent>
          </Card>

          {/* Legend */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">범례</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded bg-background-secondary border border-border" />
                  <span>빈 좌석</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded bg-accent" />
                  <span>선택됨</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded bg-foreground-secondary/10" />
                  <span>신청됨</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">안내</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-foreground-secondary">
                <li>• 자습 신청은 당일 오전까지 가능합니다</li>
                <li>• 신청 후 취소는 자습 시작 전까지 가능합니다</li>
                <li>• 무단 불참 시 벌점이 부과될 수 있습니다</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

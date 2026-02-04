'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { ChevronLeft, ChevronRight, MapPin, X, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { ApplicationStatus } from '@/types/database'

// 건물 탭 타입
type BuildingTab = 'A' | 'B' | 'S'

// 좌석 데이터 타입
interface Seat {
  id: string
  room_name: string
  seat_number: string
  is_available: boolean
}

interface SeatWithApplication extends Seat {
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

// 영역 정보 타입
interface AreaInfo {
  name: string
  current: number
  max: number
  seats: SeatWithApplication[]
}

// 건물별 영역 구성
const buildingAreas: Record<BuildingTab, string[]> = {
  A: ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8'],
  B: ['b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9'],
  S: ['s1', 's2', 's3', 's4', 's5', 's6'],
}

// 영역별 좌석 수 설정
const areaCapacity: Record<string, number> = {
  a1: 15, a2: 18, a3: 8, a4: 18, a5: 10, a6: 15, a7: 16, a8: 23,
  b1: 14, b2: 8, b3: 12, b4: 4, b5: 11, b6: 6, b7: 24, b8: 19, b9: 4,
  s1: 18, s2: 18, s3: 18, s4: 18, s5: 18, s6: 8,
}

export default function StudyPage() {
  const { user } = useAuth()
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [selectedTab, setSelectedTab] = useState<BuildingTab>('A')
  const [seats, setSeats] = useState<SeatWithApplication[]>([])
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  const [selectedArea, setSelectedArea] = useState<string | null>(null)
  const [selectedSeat, setSelectedSeat] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [myApplication, setMyApplication] = useState<{
    seat_id: string
    room_name: string
    seat_number: string
    status: ApplicationStatus
  } | null>(null)

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
        .neq('status', 'cancelled')

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
            seat_id: myApp.seat_id,
            room_name: seat.room_name,
            seat_number: seat.seat_number,
            status: myApp.status,
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
        setSelectedArea(null)
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
        .eq('seat_id', myApplication.seat_id)
        .eq('date', dateStr)

      if (error) throw error
      await fetchData()
    } catch (error) {
      console.error('Error cancelling:', error)
      alert('취소 중 오류가 발생했습니다.')
    } finally {
      setApplying(false)
    }
  }

  // 날짜 변경
  const changeDate = (delta: number) => {
    const newDate = new Date(selectedDate)
    newDate.setDate(newDate.getDate() + delta)
    setSelectedDate(newDate)
  }

  // 건물별 좌석 필터링
  const getSeatsForBuilding = (building: BuildingTab) => {
    const prefix = building.toLowerCase()
    return seats.filter((seat) => seat.room_name.toLowerCase().startsWith(prefix))
  }

  // 영역별 정보 계산
  const getAreaInfo = (areaName: string): AreaInfo => {
    const areaSeats = seats.filter((seat) => seat.room_name.toLowerCase() === areaName)
    const occupiedCount = areaSeats.filter(
      (s) => s.application && s.application.status !== 'cancelled'
    ).length
    return {
      name: areaName,
      current: occupiedCount,
      max: areaSeats.length || areaCapacity[areaName] || 0,
      seats: areaSeats,
    }
  }

  // 모달에서 좌석 선택
  const handleSeatSelect = (seatId: string) => {
    if (myApplication) return
    setSelectedSeat(selectedSeat === seatId ? null : seatId)
  }

  // 모달 닫기
  const closeModal = () => {
    setSelectedArea(null)
    setSelectedSeat(null)
  }

  // S건물 열 데이터 생성
  const getSColumnSeats = (columnName: string) => {
    return seats
      .filter((seat) => seat.room_name.toLowerCase() === columnName)
      .sort((a, b) => {
        const numA = parseInt(a.seat_number.replace(/\D/g, ''))
        const numB = parseInt(b.seat_number.replace(/\D/g, ''))
        return numA - numB
      })
  }

  const canApply = !myApplication

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => changeDate(-1)}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="font-medium">
            {format(selectedDate, 'M월 d일', { locale: ko }) === format(new Date(), 'M월 d일', { locale: ko })
              ? '오늘'
              : format(selectedDate, 'M월 d일', { locale: ko })}
          </span>
          <Button variant="ghost" size="sm" onClick={() => changeDate(1)}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {/* 내 신청 현황 */}
        {myApplication && (
          <div className="flex items-center gap-2 text-sm">
            <MapPin className="h-4 w-4 text-accent" />
            <span>{myApplication.room_name} {myApplication.seat_number}</span>
            <Button variant="ghost" size="sm" onClick={handleCancel} disabled={applying}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Building Tabs */}
      <div className="flex border-b border-border">
        {(['A', 'B', 'S'] as BuildingTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`flex-1 py-3 text-center font-medium transition-colors ${
              selectedTab === tab
                ? 'bg-background-secondary text-foreground border-b-2 border-accent'
                : 'text-foreground-secondary hover:text-foreground'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Search Bar */}
      <div className="px-4 py-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
          <Input
            type="search"
            placeholder="학생, 좌석 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          </div>
        ) : selectedTab === 'S' ? (
          /* S Building - Column Layout */
          <div className="overflow-x-auto">
            <div className="inline-flex gap-4 min-w-full pb-4">
              {buildingAreas.S.map((columnName) => {
                const columnSeats = getSColumnSeats(columnName)
                return (
                  <div key={columnName} className="flex-shrink-0 w-24">
                    <div className="text-center font-bold text-lg mb-3">{columnName}</div>
                    <div className="space-y-2">
                      {columnSeats.map((seat) => {
                        const isOccupied = !!(seat.application && seat.application.status !== 'cancelled')
                        const isMine = myApplication?.seat_id === seat.id
                        const isSelected = selectedSeat === seat.id
                        return (
                          <button
                            key={seat.id}
                            onClick={() => canApply && !isOccupied && handleSeatSelect(seat.id)}
                            disabled={isOccupied || !canApply}
                            className={`w-full py-2 px-3 rounded text-sm font-medium transition-colors ${
                              isMine
                                ? 'bg-accent text-white'
                                : isOccupied
                                  ? 'bg-foreground-secondary/20 text-foreground-secondary cursor-not-allowed'
                                  : isSelected
                                    ? 'bg-accent text-white'
                                    : 'bg-background-secondary hover:bg-accent/20'
                            }`}
                          >
                            {seat.seat_number}
                          </button>
                        )
                      })}
                    </div>
                    <div className="text-center text-xs text-foreground-secondary mt-2">↓ 복도</div>
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          /* A, B Buildings - Area Cards */
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {buildingAreas[selectedTab].map((areaName) => {
              const areaInfo = getAreaInfo(areaName)
              const isFull = areaInfo.current >= areaInfo.max
              return (
                <button
                  key={areaName}
                  onClick={() => setSelectedArea(areaName)}
                  className={`p-4 rounded-lg border transition-colors text-left ${
                    isFull
                      ? 'bg-foreground-secondary/10 border-border'
                      : 'bg-background-secondary border-border hover:border-accent'
                  }`}
                >
                  <div className="text-2xl font-bold">{areaName}</div>
                  <div className="text-sm text-foreground-secondary mt-1">
                    {areaInfo.current}/{areaInfo.max}
                  </div>
                  <div className="mt-2 h-1 bg-background rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${isFull ? 'bg-foreground-secondary' : 'bg-accent'}`}
                      style={{ width: `${areaInfo.max > 0 ? (areaInfo.current / areaInfo.max) * 100 : 0}%` }}
                    />
                  </div>
                </button>
              )
            })}
          </div>
        )}

        {/* S Building - Apply Button */}
        {selectedTab === 'S' && selectedSeat && canApply && (
          <div className="fixed bottom-20 left-0 right-0 p-4 bg-background border-t border-border">
            <Button
              onClick={() => handleApply(selectedSeat)}
              disabled={applying}
              className="w-full"
            >
              {applying ? '신청 중...' : '신청하기'}
            </Button>
          </div>
        )}
      </div>

      {/* Area Modal */}
      {selectedArea && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={closeModal}>
          <div
            className="bg-background rounded-lg p-6 max-w-md w-full mx-4 max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">{selectedArea} 좌석 선택</h3>
              <Button variant="ghost" size="sm" onClick={closeModal}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="grid grid-cols-4 gap-2">
              {getAreaInfo(selectedArea).seats.map((seat) => {
                const isOccupied = !!(seat.application && seat.application.status !== 'cancelled')
                const isMine = myApplication?.seat_id === seat.id
                const isSelected = selectedSeat === seat.id
                return (
                  <button
                    key={seat.id}
                    onClick={() => canApply && !isOccupied && handleSeatSelect(seat.id)}
                    disabled={isOccupied || !canApply}
                    className={`py-3 px-2 rounded text-sm font-medium transition-colors ${
                      isMine
                        ? 'bg-accent text-white'
                        : isOccupied
                          ? 'bg-foreground-secondary/20 text-foreground-secondary cursor-not-allowed'
                          : isSelected
                            ? 'bg-accent text-white'
                            : 'bg-background-secondary hover:bg-accent/20'
                    }`}
                  >
                    {seat.seat_number}
                  </button>
                )
              })}
            </div>

            {selectedSeat && canApply && (
              <div className="mt-4 pt-4 border-t border-border">
                <Button
                  onClick={() => handleApply(selectedSeat)}
                  disabled={applying}
                  className="w-full"
                >
                  {applying ? '신청 중...' : '신청하기'}
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

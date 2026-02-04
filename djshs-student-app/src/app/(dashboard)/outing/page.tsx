'use client'

import { useState, useEffect, useRef } from 'react'
import { format, addDays } from 'date-fns'
import { ko } from 'date-fns/locale'
import {
  Search, Plus, Clock, CheckCircle, Globe, X, Check,
  ChevronLeft, ChevronRight, Calendar as CalendarIcon, ChevronDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { OutingApplication, OutingType, ApplicationStatus, ShareType, Profile } from '@/types/database'

type TabType = 'my' | 'completed' | 'public'

interface OutingWithUser extends OutingApplication {
  user: Pick<Profile, 'name' | 'student_number'>
  approver?: Pick<Profile, 'name'> | null
}

const tabs: { id: TabType; label: string }[] = [
  { id: 'my', label: '내 신청' },
  { id: 'completed', label: '종료된 신청' },
  { id: 'public', label: '공개된 신청' },
]

const outingTypes: { value: OutingType; label: string }[] = [
  { value: 'special_room', label: '특별실 신청' },
  { value: 'general_outing', label: '일반외출' },
  { value: 'general_overnight', label: '일반외박' },
  { value: 'research_outing', label: '연구외출' },
  { value: 'research_overnight', label: '연구외박' },
]

interface LocationCategory {
  id: string
  label: string
  items?: string[]
}

const locationCategories: LocationCategory[] = [
  { id: 'favorites', label: '즐겨찾기', items: [] },
  { id: 'classroom', label: '교실', items: ['1학년 1반', '1학년 2반', '1학년 3반', '2학년 1반', '2학년 2반', '2학년 3반', '3학년 1반', '3학년 2반', '3학년 3반'] },
  { id: 'dasan', label: '다산관', items: ['다산1', '다산2', '다산3', '다산4', '세미나실'] },
  { id: 'ilsin', label: '일신관', items: ['과학실1', '과학실2', '컴퓨터실', '음악실', '미술실'] },
  { id: 'tamui', label: '탐의관', items: ['탐의1', '탐의2', '탐의3', '대강당'] },
  { id: 'other', label: '기타', items: ['도서관', '체육관', '운동장'] },
]

const shareTypes: { value: ShareType; label: string }[] = [
  { value: 'private', label: '비공개' },
  { value: 'link', label: '링크 공유' },
  { value: 'public', label: '전체 공개' },
]

const typeLabels: Record<OutingType, string> = {
  special_room: '특별실',
  general_outing: '일반외출',
  general_overnight: '일반외박',
  research_outing: '연구외출',
  research_overnight: '연구외박',
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

export default function OutingPage() {
  const { user, profile } = useAuth()
  const [activeTab, setActiveTab] = useState<TabType>('my')
  const [searchQuery, setSearchQuery] = useState('')
  const [applications, setApplications] = useState<OutingWithUser[]>([])
  const [selectedApp, setSelectedApp] = useState<OutingWithUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [processing, setProcessing] = useState(false)

  // Form state
  const [formType, setFormType] = useState<OutingType>('special_room')
  const [formLocation, setFormLocation] = useState('')
  const [formLocationSearch, setFormLocationSearch] = useState('')
  const [formReason, setFormReason] = useState('')
  const [formDate, setFormDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [formEndDate, setFormEndDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [formIsLongTerm, setFormIsLongTerm] = useState(false)
  const [formStartTime, setFormStartTime] = useState('19:10')
  const [formEndTime, setFormEndTime] = useState('23:30')
  const [formShareType, setFormShareType] = useState<ShareType>('link')

  // Dropdown states
  const [showTypeDropdown, setShowTypeDropdown] = useState(false)
  const [showLocationDropdown, setShowLocationDropdown] = useState(false)
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null)
  const [showShareDropdown, setShowShareDropdown] = useState(false)
  const [showCalendar, setShowCalendar] = useState(false)
  const [calendarMonth, setCalendarMonth] = useState(new Date())
  const [selectingEndDate, setSelectingEndDate] = useState(false)

  // Refs for click outside
  const typeDropdownRef = useRef<HTMLDivElement>(null)
  const locationDropdownRef = useRef<HTMLDivElement>(null)
  const shareDropdownRef = useRef<HTMLDivElement>(null)

  const supabase = createClient()
  const isTeacher = profile?.role === 'teacher' || profile?.role === 'admin'

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      // Skip if clicking inside a dropdown menu
      if (target.closest('[data-dropdown-menu]')) return

      if (typeDropdownRef.current && !typeDropdownRef.current.contains(e.target as Node)) {
        setShowTypeDropdown(false)
      }
      if (locationDropdownRef.current && !locationDropdownRef.current.contains(e.target as Node)) {
        setShowLocationDropdown(false)
        setExpandedCategory(null)
      }
      if (shareDropdownRef.current && !shareDropdownRef.current.contains(e.target as Node)) {
        setShowShareDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    fetchApplications()
  }, [activeTab, user])

  const fetchApplications = async () => {
    if (!user) return
    setLoading(true)

    try {
      let query = supabase
        .from('outing_applications')
        .select(`
          *,
          user:profiles!outing_applications_user_id_fkey (name, student_number),
          approver:profiles!outing_applications_approved_by_fkey (name)
        `)
        .order('created_at', { ascending: false })

      if (activeTab === 'my') {
        query = query.eq('user_id', user.id).in('status', ['pending', 'approved'])
      } else if (activeTab === 'completed') {
        if (isTeacher) {
          query = query.in('status', ['completed', 'rejected', 'cancelled'])
        } else {
          query = query.eq('user_id', user.id).in('status', ['completed', 'rejected', 'cancelled'])
        }
      } else if (activeTab === 'public') {
        query = query.in('share_type', ['public', 'link']).in('status', ['pending', 'approved'])
      }

      const { data, error } = await query

      if (error) throw error
      setApplications((data as OutingWithUser[]) || [])
    } catch (error) {
      console.error('Error fetching applications:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!user || processing) return

    if (!formLocation.trim()) {
      alert('장소를 입력해주세요.')
      return
    }

    setProcessing(true)

    try {
      const { error } = await supabase.from('outing_applications').insert({
        user_id: user.id,
        type: formType,
        location: formLocation.trim(),
        reason: formReason.trim() || null,
        date: formDate,
        start_time: `${formDate}T${formStartTime}:00`,
        end_time: `${formIsLongTerm ? formEndDate : formDate}T${formEndTime}:00`,
        share_type: formShareType,
        status: 'pending',
      })

      if (error) throw error

      resetForm()
      setShowForm(false)
      setActiveTab('my')
      await fetchApplications()
    } catch (error) {
      console.error('Error submitting:', error)
      alert('신청 중 오류가 발생했습니다.')
    } finally {
      setProcessing(false)
    }
  }

  const resetForm = () => {
    setFormType('special_room')
    setFormLocation('')
    setFormLocationSearch('')
    setFormReason('')
    setFormDate(format(new Date(), 'yyyy-MM-dd'))
    setFormEndDate(format(new Date(), 'yyyy-MM-dd'))
    setFormIsLongTerm(false)
    setFormStartTime('19:10')
    setFormEndTime('23:30')
    setFormShareType('link')
  }

  const handleCancel = async (appId: string) => {
    if (!confirm('신청을 취소하시겠습니까?')) return
    setProcessing(true)

    try {
      const { error } = await supabase
        .from('outing_applications')
        .update({ status: 'cancelled' })
        .eq('id', appId)

      if (error) throw error
      await fetchApplications()
      setSelectedApp(null)
      setShowForm(false)
    } catch (error) {
      console.error('Error cancelling:', error)
      alert('취소 중 오류가 발생했습니다.')
    } finally {
      setProcessing(false)
    }
  }

  const handleApprove = async (appId: string, approve: boolean) => {
    if (!user) return
    setProcessing(true)

    try {
      const { error } = await supabase
        .from('outing_applications')
        .update({
          status: approve ? 'approved' : 'rejected',
          approved_by: user.id,
        })
        .eq('id', appId)

      if (error) throw error
      await fetchApplications()
      setSelectedApp(null)
    } catch (error) {
      console.error('Error updating:', error)
      alert('처리 중 오류가 발생했습니다.')
    } finally {
      setProcessing(false)
    }
  }

  const filteredApplications = applications.filter(
    (app) =>
      app.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.user.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Calendar helpers
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const days: (number | null)[] = []

    for (let i = 0; i < firstDay.getDay(); i++) {
      days.push(null)
    }

    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(i)
    }

    return days
  }

  const selectDate = (day: number) => {
    const newDate = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), day)
    const dateStr = format(newDate, 'yyyy-MM-dd')

    if (formIsLongTerm && selectingEndDate) {
      setFormEndDate(dateStr)
    } else {
      setFormDate(dateStr)
      if (formIsLongTerm) {
        setSelectingEndDate(true)
        return
      }
    }
    setShowCalendar(false)
    setSelectingEndDate(false)
  }

  const selectLocation = (location: string) => {
    setFormLocation(location)
    setShowLocationDropdown(false)
    setExpandedCategory(null)
  }

  // Form Panel Component
  const FormPanel = ({ isMobile = false }: { isMobile?: boolean }) => (
    <div className={cn("space-y-4", isMobile && "pb-4")}>
      {/* Type */}
      <div ref={!isMobile ? typeDropdownRef : undefined}>
        <label className="block text-sm text-foreground-secondary mb-2">항목</label>
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowTypeDropdown(!showTypeDropdown)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-border bg-background-secondary text-sm"
          >
            <span>{outingTypes.find(t => t.value === formType)?.label}</span>
            <ChevronDown className={cn("h-4 w-4 transition-transform", showTypeDropdown && "rotate-180")} />
          </button>
          {showTypeDropdown && (
            <div data-dropdown-menu className="absolute z-10 top-full left-0 right-0 mt-1 bg-background border border-border rounded-lg shadow-lg overflow-hidden">
              {outingTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => { setFormType(type.value); setShowTypeDropdown(false); }}
                  className={cn(
                    "w-full px-3 py-2 text-left text-sm hover:bg-background-secondary",
                    formType === type.value && "bg-accent/10 text-accent"
                  )}
                >
                  {formType === type.value && <Check className="inline h-4 w-4 mr-2" />}
                  {type.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Location */}
      <div ref={!isMobile ? locationDropdownRef : undefined}>
        <label className="block text-sm text-foreground-secondary mb-2">장소</label>
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowLocationDropdown(!showLocationDropdown)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-border bg-background-secondary text-sm"
          >
            <span className={formLocation ? '' : 'text-foreground-secondary'}>
              {formLocation || '장소 선택...'}
            </span>
            <ChevronDown className={cn("h-4 w-4 transition-transform", showLocationDropdown && "rotate-180")} />
          </button>
          {showLocationDropdown && (
            <div data-dropdown-menu className="absolute z-10 top-full left-0 right-0 mt-1 bg-background border border-border rounded-lg shadow-lg overflow-hidden max-h-64 overflow-y-auto">
              {/* Search/Direct input */}
              <div className="p-2 border-b border-border">
                <Input
                  placeholder="검색/직접 입력"
                  value={formLocationSearch}
                  onChange={(e) => {
                    setFormLocationSearch(e.target.value)
                    setFormLocation(e.target.value)
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && formLocationSearch) {
                      selectLocation(formLocationSearch)
                    }
                  }}
                  className="text-sm"
                />
              </div>
              {/* Categories */}
              {locationCategories.map((cat) => (
                <div key={cat.id}>
                  <button
                    onMouseDown={(e) => e.stopPropagation()}
                    onClick={(e) => {
                      e.stopPropagation()
                      if (cat.items && cat.items.length > 0) {
                        setExpandedCategory(expandedCategory === cat.id ? null : cat.id)
                      } else {
                        selectLocation(cat.label)
                      }
                    }}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-background-secondary flex items-center justify-between"
                  >
                    <span>{cat.label}</span>
                    {cat.items && cat.items.length > 0 && (
                      <ChevronRight className={cn("h-4 w-4 transition-transform", expandedCategory === cat.id && "rotate-90")} />
                    )}
                  </button>
                  {expandedCategory === cat.id && cat.items && (
                    <div className="bg-background-secondary">
                      {cat.items.map((item) => (
                        <button
                          key={item}
                          onMouseDown={(e) => e.stopPropagation()}
                          onClick={(e) => {
                            e.stopPropagation()
                            selectLocation(item)
                          }}
                          className="w-full px-6 py-2 text-left text-sm hover:bg-accent/10"
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Reason */}
      <div>
        <label className="block text-sm text-foreground-secondary mb-2">사유</label>
        <Input
          value={formReason}
          onChange={(e) => setFormReason(e.target.value)}
          placeholder=""
        />
      </div>

      {/* Long Term Checkbox */}
      <div
        className="flex items-center gap-2 cursor-pointer"
        onClick={() => {
          setFormIsLongTerm(!formIsLongTerm)
          if (!formIsLongTerm) {
            setFormEndDate(format(addDays(new Date(formDate), 1), 'yyyy-MM-dd'))
          }
        }}
      >
        <input
          type="checkbox"
          checked={formIsLongTerm}
          onChange={() => {}}
          className="h-4 w-4 rounded border-border"
        />
        <span className="text-sm">장기간</span>
      </div>

      {/* Date */}
      <div>
        <div className="relative">
          <button
            type="button"
            onClick={() => { setShowCalendar(!showCalendar); setSelectingEndDate(false); }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-border bg-background-secondary text-sm"
          >
            <CalendarIcon className="h-4 w-4" />
            {formIsLongTerm
              ? `${format(new Date(formDate), 'yyyy. M. d.')} ~ ${format(new Date(formEndDate), 'yyyy. M. d.')}`
              : format(new Date(formDate), 'yyyy. M. d.')
            }
          </button>
          {showCalendar && (
            <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-background border border-border rounded-lg shadow-lg p-4">
              {formIsLongTerm && (
                <div className="text-center text-sm mb-2 text-foreground-secondary">
                  {selectingEndDate ? '종료일 선택' : '시작일 선택'}
                </div>
              )}
              <div className="flex items-center justify-between mb-4">
                <button onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() - 1))}>
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm font-medium">
                  {format(calendarMonth, 'yyyy년 M월', { locale: ko })}
                </span>
                <button onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1))}>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
              <div className="grid grid-cols-7 gap-1 text-center text-xs">
                {['일', '월', '화', '수', '목', '금', '토'].map((d) => (
                  <div key={d} className="py-1 text-foreground-secondary">{d}</div>
                ))}
                {getDaysInMonth(calendarMonth).map((day, i) => {
                  const dateStr = day ? format(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), day), 'yyyy-MM-dd') : ''
                  const isStartDate = dateStr === formDate
                  const isEndDate = formIsLongTerm && dateStr === formEndDate
                  const isInRange = formIsLongTerm && day && dateStr > formDate && dateStr < formEndDate

                  return (
                    <button
                      key={i}
                      onClick={() => day && selectDate(day)}
                      disabled={!day}
                      className={cn(
                        "py-1 rounded text-sm",
                        day && "hover:bg-accent/20",
                        isStartDate && "bg-accent text-white",
                        isEndDate && "bg-accent text-white",
                        isInRange && "bg-accent/20"
                      )}
                    >
                      {day}
                    </button>
                  )
                })}
              </div>
              <div className="mt-4 flex justify-end">
                <Button size="sm" variant="ghost" onClick={() => { setShowCalendar(false); setSelectingEndDate(false); }}>
                  닫기
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Time */}
      <div className="flex items-center gap-2">
        <Input
          type="time"
          value={formStartTime}
          onChange={(e) => setFormStartTime(e.target.value)}
          className="flex-1"
        />
        <span className="text-foreground-secondary">~</span>
        <Input
          type="time"
          value={formEndTime}
          onChange={(e) => setFormEndTime(e.target.value)}
          className="flex-1"
        />
      </div>

      {/* Share Type */}
      <div ref={!isMobile ? shareDropdownRef : undefined}>
        <label className="block text-sm text-foreground-secondary mb-2">공유</label>
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowShareDropdown(!showShareDropdown)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-border bg-background-secondary text-sm"
          >
            <span>{shareTypes.find(s => s.value === formShareType)?.label}</span>
            <ChevronDown className={cn("h-4 w-4 transition-transform", showShareDropdown && "rotate-180")} />
          </button>
          {showShareDropdown && (
            <div data-dropdown-menu className="absolute z-10 top-full left-0 right-0 mt-1 bg-background border border-border rounded-lg shadow-lg overflow-hidden">
              {shareTypes.map((share) => (
                <button
                  key={share.value}
                  onClick={() => { setFormShareType(share.value); setShowShareDropdown(false); }}
                  className={cn(
                    "w-full px-3 py-2 text-left text-sm hover:bg-background-secondary",
                    formShareType === share.value && "bg-accent/10 text-accent"
                  )}
                >
                  {formShareType === share.value && <Check className="inline h-4 w-4 mr-2" />}
                  {share.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Buttons */}
      <div className="flex gap-2 pt-4">
        <Button
          variant="ghost"
          className="flex-1 bg-red-500/10 text-red-500 hover:bg-red-500/20"
          onClick={() => setShowForm(false)}
        >
          취소
        </Button>
        <Button
          variant="default"
          className="flex-1"
          onClick={handleSubmit}
          disabled={processing}
        >
          {processing ? '신청 중...' : '신청'}
        </Button>
      </div>
    </div>
  )

  return (
    <div className="h-full flex">
      {/* Main List Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Search Bar */}
        <div className="p-4 flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
            <Input
              type="search"
              placeholder="신청 검색"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button onClick={() => { setShowForm(true); setSelectedApp(null); resetForm(); }}>
            <Plus className="h-4 w-4 mr-2" />
            신규 신청
          </Button>
        </div>

        {/* Tabs */}
        <div className="px-4 pb-4">
          <div className="border border-border rounded-lg overflow-hidden">
            <div className="flex border-b border-border bg-background-secondary">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setSelectedApp(null); }}
                  className={cn(
                    'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                    activeTab === tab.id
                      ? 'bg-background text-foreground'
                      : 'text-foreground-secondary hover:text-foreground'
                  )}
                >
                  {tab.id === 'my' && <Clock className="h-4 w-4" />}
                  {tab.id === 'completed' && <CheckCircle className="h-4 w-4" />}
                  {tab.id === 'public' && <Globe className="h-4 w-4" />}
                  {tab.label}
                </button>
              ))}
            </div>

            {/* List Content */}
            <div className="min-h-[300px] max-h-[calc(100vh-280px)] overflow-auto">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
              ) : filteredApplications.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-foreground-secondary">
                  <p>검색된 항목이 없습니다.</p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {filteredApplications.map((app) => (
                    <button
                      key={app.id}
                      onClick={() => { setSelectedApp(app); setShowForm(false); }}
                      className={cn(
                        'w-full p-4 text-left transition-colors hover:bg-background-secondary',
                        selectedApp?.id === app.id && 'bg-accent/5'
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="default" className="text-xs">
                              {typeLabels[app.type]}
                            </Badge>
                            <Badge className={cn('text-xs', statusColors[app.status])}>
                              {statusLabels[app.status]}
                            </Badge>
                          </div>
                          <p className="font-medium truncate">{app.location}</p>
                          <p className="text-xs text-foreground-secondary mt-1">
                            {app.user.student_number} {app.user.name} · {format(new Date(app.date), 'M월 d일', { locale: ko })}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Form or Detail */}
      <div className="w-80 border-l border-border flex-shrink-0 hidden lg:block">
        {showForm ? (
          <div className="p-4">
            <FormPanel />
          </div>
        ) : selectedApp ? (
          /* Detail View */
          <div className="p-4 space-y-4">
            <div className="flex items-center gap-2">
              <Badge variant="default">{typeLabels[selectedApp.type]}</Badge>
              <Badge className={statusColors[selectedApp.status]}>
                {statusLabels[selectedApp.status]}
              </Badge>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <span className="text-foreground-secondary">장소</span>
                <p className="font-medium">{selectedApp.location}</p>
              </div>
              {selectedApp.reason && (
                <div>
                  <span className="text-foreground-secondary">사유</span>
                  <p>{selectedApp.reason}</p>
                </div>
              )}
              <div>
                <span className="text-foreground-secondary">신청자</span>
                <p>{selectedApp.user.student_number} {selectedApp.user.name}</p>
              </div>
              <div>
                <span className="text-foreground-secondary">날짜</span>
                <p>{format(new Date(selectedApp.date), 'yyyy년 M월 d일', { locale: ko })}</p>
              </div>
              <div>
                <span className="text-foreground-secondary">시간</span>
                <p>{format(new Date(selectedApp.start_time), 'HH:mm')} ~ {format(new Date(selectedApp.end_time), 'HH:mm')}</p>
              </div>
              {selectedApp.approver && (
                <div>
                  <span className="text-foreground-secondary">처리자</span>
                  <p>{selectedApp.approver.name}</p>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-4 border-t border-border">
              {selectedApp.user_id === user?.id && selectedApp.status === 'pending' && (
                <Button
                  variant="ghost"
                  className="flex-1 bg-red-500/10 text-red-500 hover:bg-red-500/20"
                  onClick={() => handleCancel(selectedApp.id)}
                  disabled={processing}
                >
                  취소
                </Button>
              )}
              {isTeacher && selectedApp.status === 'pending' && (
                <>
                  <Button
                    variant="ghost"
                    className="flex-1 bg-red-500/10 text-red-500 hover:bg-red-500/20"
                    onClick={() => handleApprove(selectedApp.id, false)}
                    disabled={processing}
                  >
                    거절
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => handleApprove(selectedApp.id, true)}
                    disabled={processing}
                  >
                    승인
                  </Button>
                </>
              )}
            </div>
          </div>
        ) : (
          /* Empty State */
          <div className="flex items-center justify-center h-full text-foreground-secondary text-sm text-center p-4">
            목록에서 항목을 선택하거나<br />신규 신청을 클릭하세요
          </div>
        )}
      </div>

      {/* Mobile Form Modal */}
      {showForm && (
        <div className="lg:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setShowForm(false)}>
          <div
            className="absolute bottom-0 left-0 right-0 bg-background rounded-t-2xl p-4 max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold">신규 신청</h3>
              <button onClick={() => setShowForm(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <FormPanel isMobile />
          </div>
        </div>
      )}
    </div>
  )
}

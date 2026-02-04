'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { DoorOpen, Plus, Search, Clock, CheckCircle, Globe, X, Check, ArrowLeft } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/providers/auth-provider'
import type { OutingApplication, OutingType, ApplicationStatus, Profile } from '@/types/database'

type TabType = 'my' | 'completed' | 'public'

interface OutingWithUser extends OutingApplication {
  user: Pick<Profile, 'name' | 'student_number'>
  approver?: Pick<Profile, 'name'> | null
}

const tabs: { id: TabType; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'my', label: '내 신청', icon: Clock },
  { id: 'completed', label: '종료된 신청', icon: CheckCircle },
  { id: 'public', label: '공개된 신청', icon: Globe },
]

const typeLabels: Record<OutingType, string> = {
  outing: '외출',
  special_room: '특별실',
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
  const [showNewForm, setShowNewForm] = useState(false)
  const [processing, setProcessing] = useState(false)

  // Form state
  const [formType, setFormType] = useState<OutingType>('outing')
  const [formTitle, setFormTitle] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formStartTime, setFormStartTime] = useState('')
  const [formEndTime, setFormEndTime] = useState('')
  const [formIsPublic, setFormIsPublic] = useState(false)

  const supabase = createClient()
  const isTeacher = profile?.role === 'teacher' || profile?.role === 'admin'

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
        query = query.eq('is_public', true).in('status', ['pending', 'approved'])
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user || processing) return

    if (!formTitle.trim() || !formStartTime || !formEndTime) {
      alert('필수 항목을 모두 입력해주세요.')
      return
    }

    setProcessing(true)

    try {
      const { error } = await supabase.from('outing_applications').insert({
        user_id: user.id,
        type: formType,
        title: formTitle.trim(),
        description: formDescription.trim() || null,
        start_time: formStartTime,
        end_time: formEndTime,
        is_public: formIsPublic,
        status: 'pending',
      })

      if (error) throw error

      // Reset form
      setFormType('outing')
      setFormTitle('')
      setFormDescription('')
      setFormStartTime('')
      setFormEndTime('')
      setFormIsPublic(false)
      setShowNewForm(false)
      setActiveTab('my')
      await fetchApplications()
    } catch (error) {
      console.error('Error submitting:', error)
      alert('신청 중 오류가 발생했습니다.')
    } finally {
      setProcessing(false)
    }
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
      app.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.user.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (showNewForm) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={() => setShowNewForm(false)}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            돌아가기
          </Button>
          <h1 className="text-2xl font-bold">신규 신청</h1>
        </div>

        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Type */}
              <div>
                <label className="block text-sm font-medium mb-2">유형 *</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setFormType('outing')}
                    className={cn(
                      'flex-1 py-2 px-4 rounded-lg border text-sm font-medium transition-colors',
                      formType === 'outing'
                        ? 'bg-accent text-white border-accent'
                        : 'bg-background-secondary border-border hover:border-accent'
                    )}
                  >
                    외출
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormType('special_room')}
                    className={cn(
                      'flex-1 py-2 px-4 rounded-lg border text-sm font-medium transition-colors',
                      formType === 'special_room'
                        ? 'bg-accent text-white border-accent'
                        : 'bg-background-secondary border-border hover:border-accent'
                    )}
                  >
                    특별실
                  </button>
                </div>
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium mb-2">제목 *</label>
                <Input
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  placeholder="신청 제목을 입력하세요"
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium mb-2">내용</label>
                <textarea
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="상세 내용을 입력하세요"
                  rows={4}
                  className="w-full rounded-lg border border-border bg-background-secondary px-3 py-2 text-sm placeholder:text-foreground-secondary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              {/* Time */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">시작 시간 *</label>
                  <Input
                    type="datetime-local"
                    value={formStartTime}
                    onChange={(e) => setFormStartTime(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">종료 시간 *</label>
                  <Input
                    type="datetime-local"
                    value={formEndTime}
                    onChange={(e) => setFormEndTime(e.target.value)}
                    required
                  />
                </div>
              </div>

              {/* Public */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="isPublic"
                  checked={formIsPublic}
                  onChange={(e) => setFormIsPublic(e.target.checked)}
                  className="rounded border-border"
                />
                <label htmlFor="isPublic" className="text-sm">
                  다른 사용자에게 공개
                </label>
              </div>

              {/* Submit */}
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="ghost" onClick={() => setShowNewForm(false)}>
                  취소
                </Button>
                <Button type="submit" disabled={processing}>
                  {processing ? (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-2" />
                  ) : (
                    <Plus className="h-4 w-4 mr-2" />
                  )}
                  신청하기
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <DoorOpen className="h-6 w-6" />
          외출/특별실 신청
        </h1>
        <Button variant="primary" onClick={() => setShowNewForm(true)}>
          <Plus className="h-4 w-4 mr-2" />
          신규 신청
        </Button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
        <Input
          type="search"
          placeholder="신청 검색..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-lg bg-background-card mb-6">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id)
                setSelectedApp(null)
              }}
              className={cn(
                'flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
                activeTab === tab.id
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-foreground-secondary hover:text-foreground'
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* List */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">신청 목록</CardTitle>
            <CardDescription>
              {filteredApplications.length}개의 신청
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
              </div>
            ) : filteredApplications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-foreground-secondary">
                <DoorOpen className="h-12 w-12 mb-4 opacity-50" />
                <p>신청 내역이 없습니다</p>
                <p className="text-sm mt-1">+ 신규 신청 버튼을 눌러 신청하세요</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredApplications.map((app) => (
                  <button
                    key={app.id}
                    onClick={() => setSelectedApp(app)}
                    className={cn(
                      'w-full p-3 rounded-lg border text-left transition-colors',
                      selectedApp?.id === app.id
                        ? 'border-accent bg-accent/5'
                        : 'border-border bg-background-secondary hover:border-accent/50'
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="secondary" className="text-xs">
                            {typeLabels[app.type]}
                          </Badge>
                          <Badge className={cn('text-xs', statusColors[app.status])}>
                            {statusLabels[app.status]}
                          </Badge>
                        </div>
                        <p className="font-medium truncate">{app.title}</p>
                        <p className="text-xs text-foreground-secondary mt-1">
                          {app.user.student_number} {app.user.name} · {format(new Date(app.start_time), 'M/d HH:mm', { locale: ko })}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Detail */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">상세 정보</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedApp ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{typeLabels[selectedApp.type]}</Badge>
                  <Badge className={statusColors[selectedApp.status]}>
                    {statusLabels[selectedApp.status]}
                  </Badge>
                </div>

                <div>
                  <h3 className="font-medium text-lg">{selectedApp.title}</h3>
                  {selectedApp.description && (
                    <p className="text-sm text-foreground-secondary mt-2 whitespace-pre-wrap">
                      {selectedApp.description}
                    </p>
                  )}
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-foreground-secondary">신청자</span>
                    <span>{selectedApp.user.student_number} {selectedApp.user.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-foreground-secondary">시작</span>
                    <span>{format(new Date(selectedApp.start_time), 'yyyy-MM-dd HH:mm', { locale: ko })}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-foreground-secondary">종료</span>
                    <span>{format(new Date(selectedApp.end_time), 'yyyy-MM-dd HH:mm', { locale: ko })}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-foreground-secondary">공개 여부</span>
                    <span>{selectedApp.is_public ? '공개' : '비공개'}</span>
                  </div>
                  {selectedApp.approver && (
                    <div className="flex justify-between">
                      <span className="text-foreground-secondary">처리자</span>
                      <span>{selectedApp.approver.name}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-foreground-secondary">신청일</span>
                    <span>{format(new Date(selectedApp.created_at), 'yyyy-MM-dd HH:mm', { locale: ko })}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t border-border">
                  {selectedApp.user_id === user?.id && selectedApp.status === 'pending' && (
                    <Button
                      variant="ghost"
                      className="flex-1"
                      onClick={() => handleCancel(selectedApp.id)}
                      disabled={processing}
                    >
                      <X className="h-4 w-4 mr-2" />
                      취소
                    </Button>
                  )}
                  {isTeacher && selectedApp.status === 'pending' && (
                    <>
                      <Button
                        variant="ghost"
                        className="flex-1 text-red-500 hover:text-red-600"
                        onClick={() => handleApprove(selectedApp.id, false)}
                        disabled={processing}
                      >
                        <X className="h-4 w-4 mr-2" />
                        거절
                      </Button>
                      <Button
                        className="flex-1"
                        onClick={() => handleApprove(selectedApp.id, true)}
                        disabled={processing}
                      >
                        <Check className="h-4 w-4 mr-2" />
                        승인
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-foreground-secondary">
                <p>목록에서 항목을 선택하거나</p>
                <p>신규 신청을 클릭하세요</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

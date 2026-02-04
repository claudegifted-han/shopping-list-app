'use client'

import { useState } from 'react'
import { MessageSquare, AlertTriangle, Lightbulb, Loader2, ExternalLink } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const feedbackTypes = [
  { value: 'bug', label: '버그', icon: AlertTriangle },
  { value: 'feature', label: '기능 요청', icon: Lightbulb },
  { value: 'other', label: '기타', icon: MessageSquare },
]

export default function FeedbackPage() {
  const [type, setType] = useState('bug')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    // TODO: Implement GitHub issue creation via API
    await new Promise((resolve) => setTimeout(resolve, 1000))

    setLoading(false)
    setSuccess(true)
    setTitle('')
    setContent('')
  }

  if (success) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="h-16 w-16 rounded-full bg-success-bg flex items-center justify-center mb-4">
              <MessageSquare className="h-8 w-8 text-success" />
            </div>
            <h2 className="text-xl font-bold mb-2">피드백이 제출되었습니다</h2>
            <p className="text-foreground-secondary text-center mb-6">
              소중한 의견 감사합니다.
              <br />
              검토 후 반영하겠습니다.
            </p>
            <Button variant="default" onClick={() => setSuccess(false)}>
              새 피드백 작성
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">피드백</h1>

      <Card>
        <CardHeader>
          <CardTitle>피드백 보내기</CardTitle>
          <CardDescription>
            피드백은 GitHub 리포지토리에 익명으로 제출됩니다.
            <br />
            개인정보를 포함하지 마세요.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Feedback Type */}
            <div className="space-y-2">
              <label className="text-sm font-medium">항목</label>
              <div className="grid grid-cols-3 gap-3">
                {feedbackTypes.map((option) => {
                  const Icon = option.icon
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setType(option.value)}
                      className={`flex flex-col items-center gap-2 p-4 rounded-lg border transition-colors ${
                        type === option.value
                          ? 'border-accent bg-accent/10'
                          : 'border-border hover:border-border-accent'
                      }`}
                    >
                      <Icon className={`h-5 w-5 ${type === option.value ? 'text-accent' : 'text-foreground-secondary'}`} />
                      <span className="text-sm">{option.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Title */}
            <div className="space-y-2">
              <label htmlFor="title" className="text-sm font-medium">
                제목
              </label>
              <Input
                id="title"
                type="text"
                placeholder="간단한 제목을 입력하세요"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            {/* Content */}
            <div className="space-y-2">
              <label htmlFor="content" className="text-sm font-medium">
                내용
              </label>
              <textarea
                id="content"
                placeholder="자세한 내용을 입력하세요"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                rows={6}
                className="flex w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm placeholder:text-foreground-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:border-transparent transition-colors resize-none"
              />
            </div>

            {/* Info */}
            <div className="rounded-lg bg-background-secondary p-3 text-xs text-foreground-secondary">
              <p>
                피드백에는 암호화된 사용자 ID가 포함됩니다.
                <br />
                이메일, 이름 등 개인정보는 포함하지 마세요.
              </p>
            </div>

            {/* Submit */}
            <Button type="submit" variant="primary" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  제출 중...
                </>
              ) : (
                '피드백 제출'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* GitHub Link */}
      <p className="text-xs text-foreground-secondary text-center mt-6">
        GitHub에서 직접 이슈를 확인하려면{' '}
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-link hover:underline inline-flex items-center gap-1"
        >
          여기를 클릭하세요
          <ExternalLink className="h-3 w-3" />
        </a>
      </p>
    </div>
  )
}

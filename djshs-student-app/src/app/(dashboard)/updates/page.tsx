'use client'

import { History, Tag } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface UpdateEntry {
  version: string
  date: string
  changes: string[]
  type: 'major' | 'minor' | 'patch'
}

const updates: UpdateEntry[] = [
  {
    version: 'v1.0.0',
    date: '2026-02-04',
    type: 'major',
    changes: [
      '초기 릴리스',
      'Supabase 기반 인증 시스템',
      '다크/라이트/시스템 테마 지원',
      '급식 조회 기능',
      '프로필 및 설정 페이지',
      '패스키(WebAuthn) 관리',
    ],
  },
]

const typeColors = {
  major: 'bg-accent text-white',
  minor: 'bg-blue-500 text-white',
  patch: 'bg-gray-500 text-white',
}

export default function UpdatesPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <History className="h-6 w-6" />
        <h1 className="text-2xl font-bold">업데이트 내역</h1>
      </div>

      <div className="space-y-4">
        {updates.map((update) => (
          <Card key={update.version}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-3">
                  <Tag className="h-5 w-5 text-foreground-secondary" />
                  {update.version}
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge className={typeColors[update.type]}>
                    {update.type}
                  </Badge>
                  <span className="text-sm text-foreground-secondary">
                    {update.date}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {update.changes.map((change, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="text-accent mt-1.5">•</span>
                    <span>{change}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      <p className="text-xs text-foreground-secondary text-center mt-8">
        DSHS.APP v1.0.0 - 대전과학고등학교 학생현황관리시스템
      </p>
    </div>
  )
}

'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Utensils } from 'lucide-react'
import { format, addDays, subDays, parseISO } from 'date-fns'
import { ko } from 'date-fns/locale'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import type { Meal, MealType } from '@/types/database'

const mealTypeLabels: Record<MealType, string> = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
}

const mealTypeIcons: Record<MealType, string> = {
  breakfast: '🌅',
  lunch: '☀️',
  dinner: '🌙',
}

export default function MealsPage() {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [meals, setMeals] = useState<Meal[]>([])
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  useEffect(() => {
    fetchMeals()
  }, [selectedDate])

  const fetchMeals = async () => {
    setLoading(true)
    const dateStr = format(selectedDate, 'yyyy-MM-dd')

    const { data, error } = await supabase
      .from('meals')
      .select('*')
      .eq('date', dateStr)
      .order('meal_type')

    if (error) {
      console.error('Error fetching meals:', error)
    } else {
      setMeals(data || [])
    }
    setLoading(false)
  }

  const goToPreviousDay = () => setSelectedDate(subDays(selectedDate, 1))
  const goToNextDay = () => setSelectedDate(addDays(selectedDate, 1))
  const goToToday = () => setSelectedDate(new Date())

  const getMealByType = (type: MealType) => {
    return meals.find((meal) => meal.meal_type === type)
  }

  const formatMenu = (menu: string | null) => {
    if (!menu) return null
    return menu.split(',').map((item) => item.trim())
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Utensils className="h-6 w-6" />
          급식
        </h1>
      </div>

      {/* Date Navigation */}
      <div className="flex items-center justify-center gap-4 mb-8">
        <Button variant="ghost" size="sm" onClick={goToPreviousDay}>
          <ChevronLeft className="h-5 w-5" />
        </Button>

        <div className="text-center">
          <p className="text-lg font-semibold">
            {format(selectedDate, 'yyyy년 M월 d일', { locale: ko })}
          </p>
          <p className="text-sm text-foreground-secondary">
            {format(selectedDate, 'EEEE', { locale: ko })}
          </p>
        </div>

        <Button variant="ghost" size="sm" onClick={goToNextDay}>
          <ChevronRight className="h-5 w-5" />
        </Button>
      </div>

      {/* Today Button */}
      {format(selectedDate, 'yyyy-MM-dd') !== format(new Date(), 'yyyy-MM-dd') && (
        <div className="flex justify-center mb-6">
          <Button variant="default" size="sm" onClick={goToToday}>
            오늘로 이동
          </Button>
        </div>
      )}

      {/* Meal Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {(['breakfast', 'lunch', 'dinner'] as MealType[]).map((type) => {
          const meal = getMealByType(type)
          const menuItems = formatMenu(meal?.menu ?? null)

          return (
            <Card key={type} className="h-full">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <span>{mealTypeIcons[type]}</span>
                  {mealTypeLabels[type]}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                  </div>
                ) : menuItems && menuItems.length > 0 ? (
                  <ul className="space-y-1.5">
                    {menuItems.map((item, index) => (
                      <li key={index} className="text-sm text-foreground-secondary">
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-foreground-secondary text-center py-4">
                    급식 정보가 없습니다
                  </p>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Info */}
      <p className="text-xs text-foreground-secondary text-center mt-8">
        급식 정보는 학교에서 제공하는 데이터를 기반으로 합니다.
        <br />
        실제 급식과 다를 수 있습니다.
      </p>
    </div>
  )
}

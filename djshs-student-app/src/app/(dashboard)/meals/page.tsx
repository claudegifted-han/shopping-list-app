'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { format, addDays, subDays } from 'date-fns'
import { ko } from 'date-fns/locale'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils/cn'
import type { Meal, MealType } from '@/types/database'

const mealTypeLabels: Record<MealType, string> = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
}

export default function MealsPage() {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [meals, setMeals] = useState<Meal[]>([])
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  const isToday = format(selectedDate, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')

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

  // Get current meal time
  const getCurrentMealType = (): MealType | null => {
    const hour = new Date().getHours()
    if (hour < 9) return 'breakfast'
    if (hour < 14) return 'lunch'
    if (hour < 20) return 'dinner'
    return null
  }

  const currentMealType = isToday ? getCurrentMealType() : null

  return (
    <div className="max-w-4xl mx-auto">
      {/* Date Navigation */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={goToPreviousDay}
          className="p-2 rounded-lg hover:bg-background-secondary transition-colors"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>

        <div className="text-center">
          <div className="flex items-center justify-center gap-2">
            <p className="text-lg font-semibold">
              {format(selectedDate, 'M월 d일', { locale: ko })}
            </p>
            <span className="text-foreground-secondary">
              {format(selectedDate, 'EEEE', { locale: ko })}
            </span>
            {isToday && (
              <span className="text-xs bg-accent text-white px-2 py-0.5 rounded">오늘</span>
            )}
          </div>
        </div>

        <button
          onClick={goToNextDay}
          className="p-2 rounded-lg hover:bg-background-secondary transition-colors"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>

      {/* Today Button */}
      {!isToday && (
        <div className="flex justify-center mb-6">
          <button
            onClick={goToToday}
            className="px-4 py-2 rounded-lg border border-border hover:border-accent transition-colors text-sm"
          >
            오늘로 이동
          </button>
        </div>
      )}

      {/* Meal Cards */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {(['breakfast', 'lunch', 'dinner'] as MealType[]).map((type) => {
            const meal = getMealByType(type)
            const menuItems = formatMenu(meal?.menu ?? null)
            const isCurrent = currentMealType === type

            return (
              <div
                key={type}
                className={cn(
                  'rounded-lg border p-4 transition-colors',
                  isCurrent
                    ? 'border-accent bg-accent/5'
                    : 'border-border bg-background-secondary'
                )}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className={cn(
                    'font-medium',
                    isCurrent && 'text-accent'
                  )}>
                    {mealTypeLabels[type]}
                  </h3>
                  {isCurrent && (
                    <span className="text-xs bg-accent text-white px-2 py-0.5 rounded">현재</span>
                  )}
                </div>

                {menuItems && menuItems.length > 0 ? (
                  <ul className="space-y-1">
                    {menuItems.map((item, index) => (
                      <li key={index} className="text-sm text-foreground-secondary">
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-foreground-secondary text-center py-4">
                    없음
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Info */}
      <p className="text-xs text-foreground-secondary text-center mt-8">
        급식 정보는 학교에서 제공하는 데이터를 기반으로 합니다.
      </p>
    </div>
  )
}

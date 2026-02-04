import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils/cn'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'success' | 'danger' | 'warning'
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border',
        variant === 'default' && 'bg-background-card text-foreground border-border',
        variant === 'secondary' && 'bg-background-secondary text-foreground-secondary border-border',
        variant === 'success' && 'bg-success-bg text-success border-success/20',
        variant === 'danger' && 'bg-danger-bg text-danger border-danger/20',
        variant === 'warning' && 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 border-amber-200 dark:border-amber-800',
        className
      )}
      {...props}
    />
  )
}

export { Badge }

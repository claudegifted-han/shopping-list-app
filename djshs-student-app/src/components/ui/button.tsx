import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils/cn'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'danger' | 'ghost' | 'link'
  size?: 'sm' | 'md' | 'lg'
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          // Variants
          variant === 'default' && [
            'bg-background-card text-foreground border border-border',
            'hover:bg-background-secondary hover:border-border-accent',
          ],
          variant === 'primary' && [
            'bg-accent text-white',
            'hover:bg-accent-hover',
          ],
          variant === 'danger' && [
            'bg-danger text-white',
            'hover:bg-red-700 dark:hover:bg-red-600',
          ],
          variant === 'ghost' && [
            'bg-transparent text-foreground',
            'hover:bg-background-card',
          ],
          variant === 'link' && [
            'bg-transparent text-link underline-offset-4',
            'hover:underline',
          ],
          // Sizes
          size === 'sm' && 'h-8 px-3 text-sm',
          size === 'md' && 'h-10 px-4 text-sm',
          size === 'lg' && 'h-12 px-6 text-base',
          className
        )}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'

export { Button }

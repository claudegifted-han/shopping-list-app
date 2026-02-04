'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Search, Menu, X } from 'lucide-react'
import { ProfileDropdown } from './profile-dropdown'
import { MobileNav } from './mobile-nav'
import { NotificationBell } from './notification-bell'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background px-4 lg:px-6">
        {/* Mobile Menu Button */}
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden"
          onClick={() => setMobileMenuOpen(true)}
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">메뉴 열기</span>
        </Button>

        {/* Mobile Logo */}
        <Link href="/" className="flex items-center gap-2 lg:hidden">
          <div className="h-8 w-8 rounded-lg bg-accent flex items-center justify-center">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <span className="font-bold">DSHS.APP</span>
        </Link>

        {/* Search Bar */}
        <div className="flex-1 max-w-md hidden md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
            <Input
              type="search"
              placeholder="학생, 독서실 좌석 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* Spacer */}
        <div className="flex-1 md:hidden" />

        {/* Notification Bell */}
        <NotificationBell />

        {/* Profile Dropdown */}
        <ProfileDropdown />
      </header>

      {/* Mobile Navigation Drawer */}
      <MobileNav open={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
    </>
  )
}

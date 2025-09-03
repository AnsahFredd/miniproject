// FilterDropdown.tsx
import { useState } from "react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "../ui/Dropdown-menu"
import { Badge } from "../ui/Badge"
import { ChevronDown, Filter, X } from "lucide-react"
import { LEGAL_CATEGORIES, type LegalCategory } from "../../types/news"

interface FilterDropdownProps {
  selectedCategory?: string
  onCategoryChange: (category: string | undefined) => void
}

export function FilterDropdown({ selectedCategory, onCategoryChange }: FilterDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)

  const formatCategoryName = (category: string) => {
    return category
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  }

  const handleCategorySelect = (category: LegalCategory | undefined) => {
    onCategoryChange(category)
    setIsOpen(false)
  }

  return (
    <div className="flex items-center gap-2">
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <button className="btn btn-outline-accent flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Practice Area
            <ChevronDown className="h-4 w-4" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56 card animate-slide-up">
          <DropdownMenuItem
            onClick={() => handleCategorySelect(undefined)}
            className="hover:bg-slate-50 cursor-pointer p-3 rounded-md transition-colors"
          >
            All Categories
          </DropdownMenuItem>
          <DropdownMenuSeparator className="border-gray-200" />
          {LEGAL_CATEGORIES.map((category) => (
            <DropdownMenuItem
              key={category}
              onClick={() => handleCategorySelect(category)}
              className="hover:bg-slate-50 cursor-pointer p-3 rounded-md transition-colors"
            >
              {formatCategoryName(category)}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {selectedCategory && (
        <div className="badge badge-accent flex items-center gap-2 animate-pop">
          {formatCategoryName(selectedCategory)}
          <button
            onClick={() => handleCategorySelect(undefined)}
            className="btn-ghost h-4 w-4 p-0 hover:bg-white/20 rounded-full"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      )}
    </div>
  )
}
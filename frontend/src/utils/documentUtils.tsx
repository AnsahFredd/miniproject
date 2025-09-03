// src/utils/documentUtils.ts
import React from "react";
import { Calendar, DollarSign, RefreshCw, Users, AlertTriangle, Scale, FileText, Wrench, Building, Shield, Zap, Heart, BookOpen } from "lucide-react"
import type { LucideIcon } from "lucide-react"

export const truncateText = (text: string, maxLength = 150) => {
  if (text.length <= maxLength) return text
  const truncated = text.substring(0, maxLength)
  const lastSpaceIndex = truncated.lastIndexOf(" ")
  const finalText = lastSpaceIndex > maxLength * 0.7 ? truncated.substring(0, lastSpaceIndex) : truncated
  return finalText + "..."
}

export const needsTruncation = (text: string, maxLength = 150) => text.length > maxLength

export const formatCurrency = (amount: number | string | undefined) => {
  if (!amount) return "Not specified"
  const numAmount = typeof amount === "string" ? Number.parseFloat(amount.replace(/[^0-9.]/g, "")) : amount
  return `$${numAmount.toLocaleString()}/month`
}

export const formatTerm = (term: string | number | undefined) => {
  if (!term) return "Not specified"
  return typeof term === "string" ? term : `${term} years`
}
export const getClauseIcon = (type: string): React.ReactElement => {
  const iconMap: Record<string, LucideIcon> = {
    lease_term: Calendar,
    rent: DollarSign,
    renewal: RefreshCw,
    maintenance: Users,
    tool: Wrench,
    improvements: Building,
    termination: AlertTriangle,
    dispute: Scale,
    regulations: FileText,
    users: Users,
    shield: Shield,
    zap: Zap,
    heart: Heart,
    "book-open": BookOpen,
    default: FileText,
  }
  const Icon = iconMap[type] || iconMap.default
  return <Icon className="w-4 h-4 text-[var(--color-secondary)]" />
}


import type React from "react"
import {
  FileText,
  Calendar,
  DollarSign,
  RefreshCw,
  Users,
  AlertTriangle,
  Scale,
  Building,
  Wrench,
  Shield,
  Zap,
  Heart,
  BookOpen,
} from "lucide-react"
import type { ClauseItem, AnalysisData, DocumentData } from "../types/documentTypes"
import { formatCurrency, formatTerm } from "./formatting"

export const getClauseIcon = (type: string) => {
  const iconMap: Record<string, React.FC<{ className?: string }>> = {
    lease_term: Calendar,
    calendar: Calendar,
    rent: DollarSign,
    "dollar-sign": DollarSign,
    renewal: RefreshCw,
    maintenance: Users,
    tool: Wrench,
    improvements: Building,
    termination: AlertTriangle,
    "x-circle": AlertTriangle,
    dispute: Scale,
    regulations: FileText,
    "file-text": FileText,
    users: Users,
    shield: Shield,
    zap: Zap,
    heart: Heart,
    "book-open": BookOpen,
    default: FileText,
  }

  const IconComponent = iconMap[type] || iconMap["default"]
  return <IconComponent className="w-4 h-4 text-muted-foreground" />
}

export const extractKeyData = (analysis: AnalysisData | null, document: DocumentData | null): ClauseItem[] => {
  // Debug logging to see what data we're receiving
  console.log("=== DEBUG extractKeyData ===")
  console.log("analysis:", analysis)
  console.log("document:", document)
  console.log("analysis.clause_overview:", analysis?.clause_overview)
  console.log("document.analysis_results:", document?.analysis_results)
  console.log("document.analysis_results.clause_overview:", document?.analysis_results?.clause_overview)

  // First check if we have clauses from the analysis endpoint
  if (analysis && analysis.clause_overview && analysis.clause_overview.length > 0) {
    console.log("Using analysis.clause_overview")
    return analysis.clause_overview.map((clause) => ({
      ...clause,
      title: clause.title || clause.type || "Unknown",
      subtitle: clause.subtitle || clause.category || "General",
      icon: clause.icon || clause.type || "default",
    }))
  }

  // Then check if we have clauses from the document's stored analysis_results
  if (document?.analysis_results?.clause_overview && document.analysis_results.clause_overview.length > 0) {
    console.log("Using document.analysis_results.clause_overview")
    return document.analysis_results.clause_overview.map((clause) => ({
      ...clause,
      title: clause.title || clause.type || "Unknown",
      subtitle: clause.subtitle || clause.category || "General",
      icon: clause.icon || clause.type || "default",
    }))
  }

  // Then check if we have clauses directly from the document
  if (document?.clause_overview && document.clause_overview.length > 0) {
    console.log("Using document.clause_overview")
    return document.clause_overview.map((clause) => ({
      ...clause,
      title: clause.title || clause.type || "Unknown",
      subtitle: clause.subtitle || clause.category || "General",
      icon: clause.icon || clause.type || "default",
    }))
  }

  console.log("No clause data found, falling back to extracted data")

  // Fallback: extract basic info from analysis if available
  if (!analysis) return []

  const financial = analysis.financial_summary || {}
  const terms = analysis.term_information || {}

  const keyItems: ClauseItem[] = []

  if (terms.lease_duration || terms.primary_term) {
    keyItems.push({
      icon: "lease_term",
      title: formatTerm(terms.lease_duration || terms.primary_term),
      subtitle: "Lease Term",
      value: terms.lease_duration || terms.primary_term,
    })
  }

  if (financial.rent_amount) {
    keyItems.push({
      icon: "rent",
      title: formatCurrency(financial.rent_amount),
      subtitle: "Rent Amount",
      value: financial.rent_amount,
    })
  }

  if (terms.renewal_term || terms.renewal_option) {
    keyItems.push({
      icon: "renewal",
      title: formatTerm(terms.renewal_term || terms.renewal_option),
      subtitle: "Renewal Option",
      value: terms.renewal_option || terms.renewal_term,
    })
  }

  const standardClauses: ClauseItem[] = [
    { icon: "maintenance", title: "Shared", subtitle: "Maintenance", value: "shared" },
    { icon: "improvements", title: "Tenant", subtitle: "Improvements", value: "permitted" },
    { icon: "termination", title: "Conditions Apply", subtitle: "Early Termination", value: "conditional" },
    { icon: "dispute", title: "Mediation", subtitle: "Dispute Resolution", value: "mediation" },
    { icon: "regulations", title: "Local Regulations", subtitle: "Compliance", value: "required" },
  ]

  return [...keyItems, ...standardClauses]
}

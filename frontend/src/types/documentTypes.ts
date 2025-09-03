export type ClauseItem = {
  icon?: string
  title?: string
  subtitle?: string
  value?: any
  type?: string
  category?: string
  content?: string
}

export type ProcessingStatus = {
  processing_status: "pending" | "processing" | "completed" | "failed"
  task_id?: string
  task_state?: string
  task_info?: {
    stage?: string
    progress?: number
    message?: string
  }
  processing_error?: string
}

export type AnalysisData = {
  document_info?: { content: string }
  financial_summary?: {
    rent_amount?: number
    deposit?: number
    other_fees?: string[]
  }
  term_information?: {
    lease_duration?: string
    primary_term?: string
    renewal_option?: string
    renewal_term?: string
  }
  summary?: { text: string }
  clause_overview?: any[]
}

export type DocumentData = {
  id: string
  filename: string
  processing_status: "pending" | "processing" | "completed" | "failed"
  summary?: string
  classification_result?: any
  tags?: string[]
  content?: string
  processed?: boolean
  analysis_results?: {
    clause_overview?: any[]
    summary?: { text: string }
    classification?: any
    processed_at?: string
  }
  clause_overview?: any[]
}

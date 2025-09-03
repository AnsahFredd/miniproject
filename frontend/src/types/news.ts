export interface NewsAPIArticle {
  source: {
    id: string | null
    name: string
  }
  author: string | null
  title: string
  description: string | null
  url: string
  urlToImage: string | null
  publishedAt: string
  content: string | null
}

export interface NewsAPIResponse {
  status: string
  totalResults: number
  articles: NewsAPIArticle[]
}

export interface LegalNewsItem {
  id: string
  title: string
  summary: string
  publishedDate: string
  source: string
  url: string
  imageUrl?: string
  category: string
  author?: string
}

export interface NewsSearchParams {
  category?: string
  search?: string
  page?: number
  pageSize?: number
}

export interface NewsResponse {
  articles: LegalNewsItem[]
  totalResults: number
  page: number
  pageSize: number
  totalPages: number
}

export interface ApiError {
  message: string
  status: number
}

// Legal practice area categories
export const LEGAL_CATEGORIES = [
  "business",
  "employment",
  "contracts",
  "litigation",
  "corporate",
  "intellectual-property",
  "real-estate",
  "tax",
  "criminal",
  "family",
] as const

export type LegalCategory = (typeof LEGAL_CATEGORIES)[number]

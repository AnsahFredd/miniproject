import { useState, useEffect, useCallback } from "react"
import axios, { AxiosError } from "axios"
import type { LegalNewsItem, NewsSearchParams, NewsResponse } from "../types/news"
import { NewsList } from "../components/contract/NewsList"
import { SearchBar } from "../components/contract/SearchBar"
import { FilterDropdown } from "../components/contract/FilterDropdown"
import { Pagination } from "../components/contract/Pagination"
import { ErrorMessage } from "../components/contract/ErrorMessage"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { Badge } from "../components/ui/Badge"
import { Separator } from "../components/ui/Separator"
import { Scale, Newspaper, Filter, RefreshCw } from "lucide-react"

interface NewsFeedState {
  articles: LegalNewsItem[]
  loading: boolean
  error: string | null
  totalPages: number
  currentPage: number
  totalResults: number
}

const API = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const NewsFeed = () => {
  // State management
  const [newsState, setNewsState] = useState<NewsFeedState>({
    articles: [],
    loading: true,
    error: null,
    totalPages: 0,
    currentPage: 1,
    totalResults: 0,
  })

  const [searchParams, setSearchParams] = useState<NewsSearchParams>({
    search: "",
    category: undefined,
    page: 1,
    pageSize: 12,
  })

  const [searchInput, setSearchInput] = useState("")

  const fetchNews = useCallback(async (params: NewsSearchParams) => {
    setNewsState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      // Build query parameters
      const queryParams: Record<string, string | number> = {
        page: params.page || 1,
        page_size: params.pageSize || 12
      }
      console.log(`${API}/news`)
      console.log("With params", queryParams)

      if (params.search?.trim()) {
        queryParams.search = params.search.trim()
      } 

      if (params.category) {
        queryParams.category = params.category
      }

      // Correct API endpoint construction
      const response = await axios.get<NewsResponse>(`${API}/news`, {
        params: queryParams,
        timeout: 30000 // 30 seconds
      })

      console.log("Response received:", response.data)

      setNewsState({
        articles: response.data.articles,
        loading: false,
        error: null,
        totalPages: response.data.totalPages,
        currentPage: response.data.page,
        totalResults: response.data.totalResults,
      })
      
      console.log("Response received:", response.data)

    } catch (error) {
      console.error("[NewsFeed] Error fetching news:", error)
      
      let errorMessage = "Failed to fetch news articles"
      
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<{ detail?: string; message?: string }>
        
        if (axiosError.response) {
          // Server responded with error status
          errorMessage = axiosError.response.data?.detail || 
                        axiosError.response.data?.message || 
                        `Server error: ${axiosError.response.status} ${axiosError.response.statusText}`
        } else if (axiosError.request) {
          // Request was made but no response received
          errorMessage = "Unable to connect to the news server. Please check your connection."
        } else {
          // Something else happened
          errorMessage = axiosError.message || "An unexpected error occurred"
        }
      } else if (error instanceof Error) {
        errorMessage = error.message
      }

      setNewsState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }))
    }
  }, [])

  // Initial load
  useEffect(() => {
    fetchNews(searchParams)
  }, [fetchNews, searchParams])

  // Handle search
  const handleSearch = (query: string) => {
    const newParams = { ...searchParams, search: query, page: 1 }
    setSearchParams(newParams)
    setSearchInput(query)
  }

  // Handle category filter changes
  const handleCategoryChange = (category: string | undefined) => {
    const newParams = { ...searchParams, category, page: 1 }
    setSearchParams(newParams)
  }

  // Handle pagination
  const handlePageChange = (page: number) => {
    const newParams = { ...searchParams, page }
    setSearchParams(newParams)
  }

  // Handle retry
  const handleRetry = () => {
    fetchNews(searchParams)
  }

  // Clear filters
  const clearFilters = () => {
    const newParams = { ...searchParams, search: "", category: undefined, page: 1 }
    setSearchParams(newParams)
    setSearchInput("")
  }

  const hasActiveFilters = searchParams.search || searchParams.category

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-soft)' }}>
      {/* Header - Fixed styling without backdrop blur */}
      <header className="nav-elevated sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg" 
                   style={{ background: 'var(--color-accent)', color: 'white' }}>
                <Scale className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold" style={{ color: 'var(--color-primary)' }}>
                  LegalLens
                </h1>
                <p className="text-sm" style={{ color: 'var(--color-secondary)' }}>
                  Professional Legal News Feed
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="badge badge-accent hidden sm:flex items-center gap-1">
                <Newspaper className="h-3 w-3" />
                {newsState.totalResults} Articles
              </div>
              <button
                onClick={() => fetchNews(searchParams)}
                disabled={newsState.loading}
                className="btn btn-ghost hidden sm:flex items-center gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${newsState.loading ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Search and Filters */}
        <div className="card mb-8 animate-slide-up">
          <div className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="h-5 w-5" style={{ color: 'var(--color-accent)' }} />
              <h2 className="text-lg font-semibold" style={{ color: 'var(--color-primary)' }}>
                Search & Filter
              </h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <SearchBar
                    onSearch={handleSearch}
                    placeholder="Search legal news, cases, regulations..."
                    initialValue={searchInput}
                  />
                </div>
                <FilterDropdown 
                  selectedCategory={searchParams.category} 
                  onCategoryChange={handleCategoryChange} 
                />
              </div>

              {hasActiveFilters && (
                <div className="flex items-center justify-between pt-4 border-t" 
                     style={{ borderColor: '#E2E8F0' }}>
                  <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-secondary)' }}>
                    <span>Active filters:</span>
                    {searchParams.search && (
                      <div className="badge badge-primary">
                        Search: "{searchParams.search}"
                      </div>
                    )}
                    {searchParams.category && (
                      <div className="badge badge-accent">
                        {searchParams.category.replace("-", " ").toUpperCase()}
                      </div>
                    )}
                  </div>
                  <button 
                    onClick={clearFilters}
                    className="link-accent text-sm"
                  >
                    Clear All
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Results Summary */}
        {!newsState.loading && !newsState.error && (
          <div className="flex items-center justify-between mb-6 animate-fade-in">
            <div className="text-sm" style={{ color: 'var(--color-secondary)' }}>
              Showing {newsState.articles.length} of {newsState.totalResults} articles
              {newsState.totalPages > 1 && (
                <span>
                  {" "}
                  • Page {newsState.currentPage} of {newsState.totalPages}
                </span>
              )}
            </div>
          </div>
        )}

        <div className="w-full h-px mb-6" style={{ background: '#E2E8F0' }}></div>

        {/* News Articles */}
        {newsState.error ? (
          <div className="animate-slide-up">
            <ErrorMessage message={newsState.error} onRetry={handleRetry} />
          </div>
        ) : (
          <div className="animate-slide-up">
            <NewsList articles={newsState.articles} loading={newsState.loading} />

            {/* Pagination */}
            {!newsState.loading && !newsState.error && newsState.totalPages > 1 && (
              <Pagination
                currentPage={newsState.currentPage}
                totalPages={newsState.totalPages}
                onPageChange={handlePageChange}
              />
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default NewsFeed
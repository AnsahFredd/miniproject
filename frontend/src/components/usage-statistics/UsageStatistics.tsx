"use client"

import type React from "react"
import { useState, useEffect } from "react"
import type { UsageStatisticsProps, DailyUsage, StatusData } from "../../types/usagestatsTypes"
import { fetchUsageStatistics, getLast7Days } from "../../utils/usagestatsUtils"
import Header from "./Header"
import Summary from "./Summary"
import DailyUploadsChart from "./charts/DailyUploadsChart"
import Loading from "./Loading"
import ErrorMessage from "./ErrorMessage"

const UsageStatistics: React.FC<UsageStatisticsProps> = ({ token }) => {
  const [usageData, setUsageData] = useState<DailyUsage[]>([])
  const [statusData, setStatusData] = useState<StatusData[]>([])
  const [totalProcessed, setTotalProcessed] = useState<number>(0)
  const [percentageChange, setPercentageChange] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const handleFetchData = async () => {
    if (!token) {
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      const stats = await fetchUsageStatistics(token)

      setUsageData(stats.usageData)
      setStatusData(stats.statusData)
      setTotalProcessed(stats.totalProcessed)
      setPercentageChange(stats.percentageChange)
    } catch (err: any) {
      console.error("Error fetching usage statistics:", err)
      let errorMessage = "Failed to load usage statistics"

      if (err.code === "ECONNABORTED") {
        errorMessage = "Request timeout - please try again"
      } else if (err.response?.status === 401) {
        errorMessage = "Session expired - please log in again"
      } else if (err.response?.status === 403) {
        errorMessage = "Access denied"
      } else if (err.response?.status >= 500) {
        errorMessage = "Server error - please try again later"
      } else if (!navigator.onLine) {
        errorMessage = "No internet connection"
      } else if (err.message && err.message !== "Network Error") {
        errorMessage = err.message
      }

      setError(errorMessage)
      setUsageData(getLast7Days())
      setStatusData([])
      setTotalProcessed(0)
      setPercentageChange(0)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    handleFetchData()
  }, [token])

  if (!token) return null

  return (
    <div className="space-y-6">
      <div className="p-6 bg-white border border-gray-200 rounded-lg shadow-lg card">
        <Header onRefresh={handleFetchData} isLoading={isLoading} />

        {isLoading ? (
          <Loading />
        ) : error ? (
          <ErrorMessage error={error} onRetry={handleFetchData} />
        ) : (
          <>
            <Summary totalProcessed={totalProcessed} percentageChange={percentageChange} statusData={statusData} />

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <DailyUploadsChart data={usageData} />
             
            </div>

            <p className="text-xs text-[var(--color-secondary)] text-center mt-6">
              Statistics are updated in real-time and show your document processing activity
            </p>
          </>
        )}
      </div>
    </div>
  )
}

export default UsageStatistics

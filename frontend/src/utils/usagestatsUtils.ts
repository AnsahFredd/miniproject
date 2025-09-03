import axios from "axios"
import type { DailyUsage, UsageStats } from "../types/usagestatsTypes"

const API = import.meta.env.VITE_API_BASE_URL

export const getLast7Days = (): DailyUsage[] => {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
  const result: DailyUsage[] = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, "0")
    const day = String(date.getDate()).padStart(2, "0")
    const localDateString = `${year}-${month}-${day}`
    result.push({
      date: localDateString,
      count: 0,
      dayName: days[date.getDay()],
    })
  }
  return result
}

export const getLocalDateString = (dateInput: any): string => {
  let date: Date
  if (dateInput instanceof Date) {
    date = dateInput
  } else if (typeof dateInput === "string" || typeof dateInput === "number") {
    date = new Date(dateInput)
  } else {
    return ""
  }
  if (isNaN(date.getTime())) return ""
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

export const mapApiStatusToDisplayStatus = (apiStatus: string): string => {
  const status = apiStatus?.toLowerCase()
  switch (status) {
    case "completed":
    case "complete":
    case "done":
    case "finished":
    case "processed":
    case "ready":
    case "success":
    case "successful":
      return "Completed"
    case "processing":
    case "in_progress":
    case "analyzing":
      return "Processing"
    case "failed":
    case "error":
    case "cancelled":
    case "canceled":
      return "Failed"
    case "uploaded":
    case "pending":
      return "Uploaded"
    default:
      return "Other"
  }
}

export const fetchUsageStatistics = async (token: string): Promise<UsageStats> => {
  if (!API) throw new Error("API URL not configured")

  const response = await axios.get(`${API}/documents/`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  })

  let documents: any[] = []
  if (response.data && Array.isArray(response.data.data)) {
    documents = response.data.data
  } else if (Array.isArray(response.data)) {
    documents = response.data
  } else {
    console.warn("Unexpected response format:", response.data)
    documents = []
  }

  if (documents.length === 0) {
    return {
      usageData: getLast7Days(),
      statusData: [],
      totalProcessed: 0,
      percentageChange: 0,
    }
  }

  const last7Days = getLast7Days()
  const dailyCounts: { [key: string]: number } = {}
  const statusCounts: { [key: string]: number } = {}
  let totalLast30Days = 0
  let totalPrevious30Days = 0

  const now = new Date()
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 86400000)
  const sixtyDaysAgo = new Date(now.getTime() - 60 * 86400000)

  documents.forEach((doc: any) => {
    const dateValue = doc.upload_date || doc.created_at || doc.uploaded_at || doc.createdAt || doc.date || doc.timestamp

    if (dateValue) {
      const localDateString = getLocalDateString(dateValue)
      if (localDateString) {
        const uploadDate = new Date(dateValue)

        if (uploadDate >= new Date(now.getTime() - 7 * 86400000)) {
          dailyCounts[localDateString] = (dailyCounts[localDateString] || 0) + 1
        }

        if (uploadDate >= thirtyDaysAgo) {
          totalLast30Days++
        } else if (uploadDate >= sixtyDaysAgo) {
          totalPrevious30Days++
        }
      }
    }

    const status = mapApiStatusToDisplayStatus(doc.status || doc.processing_status || doc.state)
    statusCounts[status] = (statusCounts[status] || 0) + 1
  })

  const chartData = last7Days.map((day) => ({
    ...day,
    count: dailyCounts[day.date] || 0,
  }))

  const statusColors = {
    Completed: "#10B981",
    Processing: "#3B82F6",
    Failed: "#EF4444",
    Uploaded: "#F59E0B",
    Other: "#6B7280",
  }

  const statusChartData = Object.entries(statusCounts).map(([status, count]) => ({
    name: status,
    value: count,
    color: statusColors[status as keyof typeof statusColors] || "#6B7280",
  }))

  const change =
    totalPrevious30Days > 0
      ? Math.round(((totalLast30Days - totalPrevious30Days) / totalPrevious30Days) * 100)
      : totalLast30Days > 0
        ? 100
        : 0

  return {
    usageData: chartData,
    statusData: statusChartData,
    totalProcessed: totalLast30Days,
    percentageChange: change,
  }
}

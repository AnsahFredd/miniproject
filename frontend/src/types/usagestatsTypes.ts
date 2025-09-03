export interface DailyUsage {
  date: string
  count: number
  dayName: string
}

export interface StatusData {
  name: string
  value: number
  color: string
}

export interface UsageStatisticsProps {
  token: string | null
}

export interface UsageStats {
  usageData: DailyUsage[]
  statusData: StatusData[]
  totalProcessed: number
  percentageChange: number
}

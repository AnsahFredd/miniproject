import type React from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import type { DailyUsage } from "../../../types/usagestatsTypes"
import { CustomTooltip } from "../tooltips"

interface DailyUploadsChartProps {
  data: DailyUsage[]
}

const DailyUploadsChart: React.FC<DailyUploadsChartProps> = ({ data }) => {
  return (
    <div className="lg:col-span-2">
      <h3 className="text-sm font-medium text-[var(--color-secondary)] mb-4">Daily Uploads (Last 7 Days)</h3>
      <div className="h-64 p-4 bg-white border border-gray-100 rounded-md">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 20, bottom: 30, left: 0 }}>
            <CartesianGrid stroke="#F3F4F6" strokeDasharray="3 3" />
            <XAxis
              dataKey="dayName"
              tick={{ fill: "#64748B", fontSize: 12 }}
              axisLine={{ stroke: "#E5E7EB" }}
              tickLine={{ stroke: "#E5E7EB" }}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: "#64748B", fontSize: 12 }}
              axisLine={{ stroke: "#E5E7EB" }}
              tickLine={{ stroke: "#E5E7EB" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="count" fill="#14B8A6" radius={[4, 4, 0, 0]} stroke="#0FA596" strokeWidth={1} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default DailyUploadsChart

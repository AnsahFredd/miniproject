import type React from "react"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"
import type { StatusData } from "../../../types/usagestatsTypes"
import { PieTooltip } from "../tooltips"

interface StatusPieChartProps {
  data: StatusData[]
}

const StatusPieChart: React.FC<StatusPieChartProps> = ({ data }) => {
  if (data.length === 0) return null

  return (
    <div>
      <h3 className="text-sm font-medium text-[var(--color-secondary)] mb-4">Status Distribution</h3>
      <div className="h-64 p-4 bg-white border border-gray-100 rounded-md">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" outerRadius={80} dataKey="value">
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<PieTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default StatusPieChart

export const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-3 bg-white border border-gray-200 rounded-md shadow-lg">
        <p className="font-medium text-gray-800">{label}</p>
        <p className="text-sm text-gray-600">
          {`${payload[0].value} document${payload[0].value !== 1 ? "s" : ""} uploaded`}
        </p>
      </div>
    )
  }
  return null
}

export const PieTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-2 bg-white border border-gray-200 rounded-md shadow-lg">
        <p className="text-sm font-medium">{payload[0].name}</p>
        <p className="text-sm text-gray-600">{payload[0].value} documents</p>
      </div>
    )
  }
  return null
}

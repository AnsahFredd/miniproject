export const formatCurrency = (amount: number | string | undefined) => {
  if (!amount) return "Not specified"
  const numAmount = typeof amount === "string" ? Number.parseFloat(amount.replace(/[^0-9.]/g, "")) : amount
  return `$${numAmount.toLocaleString()}/month`
}

export const formatTerm = (term: string | number | undefined) => {
  if (!term) return "Not specified"
  return typeof term === "string" ? term : `${term} years`
}

export const truncateText = (text: string, maxLength = 150) => {
  if (text.length <= maxLength) return text

  // Find the last complete word within the limit
  const truncated = text.substring(0, maxLength)
  const lastSpaceIndex = truncated.lastIndexOf(" ")

  // If we found a space, cut at the word boundary, otherwise use the full truncated text
  const finalText = lastSpaceIndex > maxLength * 0.7 ? truncated.substring(0, lastSpaceIndex) : truncated

  return finalText + "..."
}

export const needsTruncation = (text: string, maxLength = 150) => {
  return text.length > maxLength
}

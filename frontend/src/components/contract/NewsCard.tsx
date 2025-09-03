import { Card, CardContent, CardHeader } from "../ui/Card"
import { Badge } from "../ui/Badge"
import { ExternalLink, Calendar, User } from "lucide-react"
import type { LegalNewsItem } from "../../types/news"

interface NewsCardProps {
  article: LegalNewsItem
}

export function NewsCard({ article }: NewsCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  const getCategoryBadge = (category: string) => {
    const categoryMap: Record<string, string> = {
      corporate: "badge-primary",
      litigation: "badge-secondary",
      employment: "badge-accent",
      "intellectual-property": "badge-primary",
      "real-estate": "badge-secondary",
      tax: "badge-accent",
      criminal: "badge-primary",
      contracts: "badge-secondary",
      business: "badge-accent",
    }
    return categoryMap[category] || "badge-primary"
  }

  return (
    <div className="card h-full flex flex-col hover:shadow-lg transition-all duration-300 hover:transform hover:-translate-y-1 animate-fade-in">
      <div className="p-6 pb-3">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className={`badge ${getCategoryBadge(article.category)} text-xs font-medium`}>
            {article.category.replace("-", " ").toUpperCase()}
          </div>
          <div className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-secondary)' }}>
            <Calendar className="h-3 w-3" />
            {formatDate(article.publishedDate)}
          </div>
        </div>

        <h3 className="font-bold text-lg leading-tight mb-3 hover:text-teal-600 transition-colors cursor-pointer">
          {article.title}
        </h3>
      </div>

      <div className="px-6 pb-6 flex-1 flex flex-col">
        {article.imageUrl && (
          <div className="mb-4 rounded-lg overflow-hidden">
            <img
              src={article.imageUrl || "/placeholder.svg"}
              alt={article.title}
              className="w-full h-32 object-cover hover:scale-105 transition-transform duration-300"
            />
          </div>
        )}

        <p className="text-sm leading-relaxed mb-4 flex-1" style={{ color: 'var(--color-secondary)' }}>
          {article.summary}
        </p>

        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--color-secondary)' }}>
            <span className="font-medium">{article.source}</span>
            {article.author && (
              <>
                <span>•</span>
                <div className="flex items-center gap-1">
                  <User className="h-3 w-3" />
                  <span>{article.author}</span>
                </div>
              </>
            )}
          </div>

          <a 
            href={article.url} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="btn btn-ghost text-sm flex items-center gap-1 link-accent"
          >
            Read More
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </div>
  )
}
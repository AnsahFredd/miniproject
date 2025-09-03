import os
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from app.schemas.news import (
    NewsAPIResponse, 
    NewsAPIArticle, 
    LegalNewsItem, 
    NewsResponse, 
    NewsSearchParams
)

from app.core.config import settings

API_KEY = settings.SECURITY.NEWS_API_KEY

class NewsService:
    """Service class for fetching legal news from external APIs"""
    
    def __init__(self):
        self.news_api_key = API_KEY
        self.news_api_base_url = "https://newsapi.org/v2"
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache
        
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY environment variable is required")
    
    async def search_news(self, params: NewsSearchParams) -> NewsResponse:
        """
        Search legal news articles from external API
        """
        try:
            print(f"DEBUG: Starting search with params: {params}")
            
            # Always try to get some articles - even for empty searches
            if not params.search and not params.category:
                print("DEBUG: Using default news strategy")
                return await self._fetch_default_legal_news(params)
            
            # Build search query
            query = self._build_search_query(params)
            print(f"DEBUG: Built query: '{query}'")
            
            # Fetch from NewsAPI
            articles_data = await self._fetch_from_newsapi(query, params)
            print(f"DEBUG: NewsAPI returned {len(articles_data.articles)} articles")
            
            # Transform articles
            legal_articles = self._transform_articles(articles_data.articles, params.category)
            print(f"DEBUG: Transformed to {len(legal_articles)} legal articles")
            
            # Apply minimal filtering - be very lenient
            filtered_articles = self._filter_legal_content_minimal(legal_articles)
            print(f"DEBUG: After filtering: {len(filtered_articles)} articles")
            
            # If we still have no results, try fallback
            if not filtered_articles:
                print("DEBUG: No articles after filtering, trying fallback")
                return await self._try_fallback_search(params)
            
            
            # Calculate pagination
            total_pages = max(1, (len(filtered_articles) + params.pageSize - 1) // params.pageSize)
            start_idx = (params.page - 1) * params.pageSize
            end_idx = start_idx + params.pageSize
            paginated_articles = filtered_articles[start_idx:end_idx]
            
            result = NewsResponse(
                articles=paginated_articles,
                totalResults=len(filtered_articles),
                page=params.page,
                pageSize=params.pageSize,
                totalPages=total_pages
            )
            
            print(f"DEBUG: Returning {len(result.articles)} articles, total: {result.totalResults}")
            return result
            
        except Exception as e:
            print(f"ERROR: Exception in search_news: {str(e)}")
            # Return fallback response instead of empty
            return await self._create_fallback_response(params)
    
    async def _fetch_default_legal_news(self, params: NewsSearchParams) -> NewsResponse:
        """Fetch default legal news - simplified approach"""
        try:
            print("DEBUG: Fetching default legal news")
            
            # Try multiple strategies in parallel
            tasks = [
                self._fetch_top_headlines(params),
                self._fetch_business_news(params),
                self._fetch_general_news_with_legal_terms(params)
            ]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all successful results
            all_articles = []
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                else:
                    print(f"DEBUG: Task failed: {result}")
            
            print(f"DEBUG: Combined {len(all_articles)} articles from all sources")
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_articles = []
            for article in all_articles:
                if str(article.url) not in seen_urls:
                    seen_urls.add(str(article.url))
                    unique_articles.append(article)
            
            # Sort by date
            unique_articles.sort(key=lambda x: x.publishedDate, reverse=True)
            
            # Apply pagination
            total_pages = max(1, (len(unique_articles) + params.pageSize - 1) // params.pageSize)
            start_idx = (params.page - 1) * params.pageSize
            end_idx = start_idx + params.pageSize
            paginated_articles = unique_articles[start_idx:end_idx]
            
            return NewsResponse(
                articles=paginated_articles,
                totalResults=len(unique_articles),
                page=params.page,
                pageSize=params.pageSize,
                totalPages=total_pages
            )
            
        except Exception as e:
            print(f"ERROR: Exception in _fetch_default_legal_news: {str(e)}")
            return await self._create_fallback_response(params)
    
    async def _fetch_top_headlines(self, params: NewsSearchParams) -> List[LegalNewsItem]:
        """Fetch top headlines"""
        try:
            url = f"{self.news_api_base_url}/top-headlines"
            headers = {"X-API-Key": self.news_api_key}
            
            api_params = {
                "category": "business",
                "language": "en",
                "country": "us",
                "pageSize": 50
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=api_params)
                response.raise_for_status()
                
                data = response.json()
                print(f"DEBUG: Top headlines API returned {data.get('totalResults', 0)} results")
                
                if data.get('status') != 'ok':
                    print(f"DEBUG: Headlines API error: {data}")
                    return []
                
                news_response = NewsAPIResponse(**data)
                return self._transform_articles(news_response.articles, None)
                
        except Exception as e:
            print(f"DEBUG: Error fetching headlines: {str(e)}")
            return []
    
    async def _fetch_business_news(self, params: NewsSearchParams) -> List[LegalNewsItem]:
        """Fetch business news which often contains legal content"""
        try:
            url = f"{self.news_api_base_url}/everything"
            headers = {"X-API-Key": self.news_api_key}
            
            api_params = {
                "q": "business",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 50,
                "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=api_params)
                response.raise_for_status()
                
                data = response.json()
                print(f"DEBUG: Business news API returned {data.get('totalResults', 0)} results")
                
                if data.get('status') != 'ok':
                    print(f"DEBUG: Business API error: {data}")
                    return []
                
                news_response = NewsAPIResponse(**data)
                return self._transform_articles(news_response.articles, "business-law")
                
        except Exception as e:
            print(f"DEBUG: Error fetching business news: {str(e)}")
            return []
    
    async def _fetch_general_news_with_legal_terms(self, params: NewsSearchParams) -> List[LegalNewsItem]:
        """Fetch general news with basic legal terms"""
        try:
            url = f"{self.news_api_base_url}/everything"
            headers = {"X-API-Key": self.news_api_key}
            
            api_params = {
                "q": "court OR law OR legal",
                "language": "en",
                "sortBy": "publishedAt", 
                "pageSize": 30,
                "from": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=api_params)
                response.raise_for_status()
                
                data = response.json()
                print(f"DEBUG: General legal news API returned {data.get('totalResults', 0)} results")
                
                if data.get('status') != 'ok':
                    print(f"DEBUG: General API error: {data}")
                    return []
                
                news_response = NewsAPIResponse(**data)
                return self._transform_articles(news_response.articles, None)
                
        except Exception as e:
            print(f"DEBUG: Error fetching general legal news: {str(e)}")
            return []
    
    async def _try_fallback_search(self, params: NewsSearchParams) -> NewsResponse:
        """Try a broader search when specific search fails"""
        try:
            print("DEBUG: Trying fallback search")
            
            # Use very broad terms
            fallback_query = "news"
            
            url = f"{self.news_api_base_url}/everything"
            headers = {"X-API-Key": self.news_api_key}
            
            api_params = {
                "q": fallback_query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 50,
                "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=api_params)
                response.raise_for_status()
                
                data = response.json()
                print(f"DEBUG: Fallback search returned {data.get('totalResults', 0)} results")
                
                if data.get('status') != 'ok':
                    print(f"DEBUG: Fallback API error: {data}")
                    return await self._create_fallback_response(params)
                
                news_response = NewsAPIResponse(**data)
                articles = self._transform_articles(news_response.articles, params.category)
                
                # Very minimal filtering for fallback
                filtered_articles = [article for article in articles if article.title and article.url]
                
                total_pages = max(1, (len(filtered_articles) + params.pageSize - 1) // params.pageSize)
                start_idx = (params.page - 1) * params.pageSize
                end_idx = start_idx + params.pageSize
                paginated_articles = filtered_articles[start_idx:end_idx]
                
                return NewsResponse(
                    articles=paginated_articles,
                    totalResults=len(filtered_articles),
                    page=params.page,
                    pageSize=params.pageSize,
                    totalPages=total_pages
                )
                
        except Exception as e:
            print(f"ERROR: Fallback search failed: {str(e)}")
            return await self._create_fallback_response(params)
    
    def _build_search_query(self, params: NewsSearchParams) -> str:
        """Build search query - simplified and more permissive"""
        
        if params.search:
            search_term = params.search.strip().lower()
            print(f"DEBUG: Building query for search term: '{search_term}'")
            
            # Don't over-complicate the queries
            if search_term in ["business", "corporate", "company"]:
                return "business"
            elif search_term in ["employment", "job", "work", "labor"]:
                return "employment"
            elif search_term in ["contract", "contracts", "agreement"]:
                return "contract"
            elif search_term in ["court", "lawsuit", "legal", "law"]:
                return search_term
            else:
                # For other terms, just use them as-is
                return search_term
        
        elif params.category:
            category_queries = {
                "business-law": "business",
                "employment-law": "employment", 
                "contracts": "contract",
                "litigation": "court",
                "corporate-law": "corporate",
                "intellectual-property": "patent",
                "criminal-law": "criminal",
                "civil-rights": "civil rights"
            }
            return category_queries.get(params.category, "legal")
        
        else:
            return "news"
    
    async def _fetch_from_newsapi(self, query: str, params: NewsSearchParams) -> NewsAPIResponse:
        """Fetch articles from NewsAPI.org - simplified"""
        
        print(f"DEBUG: Fetching from NewsAPI with query: '{query}'")
        
        url = f"{self.news_api_base_url}/everything"
        headers = {"X-API-Key": self.news_api_key}
        
        api_params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 100,  # Get maximum allowed
            "from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        }
        
        print(f"DEBUG: API request params: {api_params}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=api_params)
            print(f"DEBUG: API response status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"DEBUG: API response status: {data.get('status')}")
            print(f"DEBUG: API returned {data.get('totalResults', 0)} total results")
            print(f"DEBUG: Articles in response: {len(data.get('articles', []))}")
            
            if data.get('status') != 'ok':
                print(f"ERROR: NewsAPI error: {data}")
                # Return empty response structure
                return NewsAPIResponse(status='ok', totalResults=0, articles=[])
            
            news_response = NewsAPIResponse(**data)
            return news_response
    
    def _filter_legal_content_minimal(self, articles: List[LegalNewsItem]) -> List[LegalNewsItem]:
        """Minimal filtering - only exclude obvious spam/irrelevant content"""
        
        # Very basic exclusion list - only obvious non-news content
        exclude_keywords = [
            "download now", "click here", "subscribe", "advertisement",
            "sponsored content", "buy now", "free trial"
        ]
        
        filtered_articles = []
        
        for article in articles:
            content = f"{article.title} {article.summary}".lower()
            
            # Only exclude obvious spam/ads
            has_spam_content = any(keyword in content for keyword in exclude_keywords)
            if has_spam_content:
                continue
            
            # Keep everything else
            filtered_articles.append(article)
        
        print(f"DEBUG: Minimal filtering: {len(articles)} -> {len(filtered_articles)} articles")
        return filtered_articles
    
    def _transform_articles(self, articles: List[NewsAPIArticle], category: Optional[str]) -> List[LegalNewsItem]:
        """Transform NewsAPI articles to our LegalNewsItem format - very permissive"""
        
        legal_articles = []
        
        for article in articles:
            # Only skip articles with missing essential data
            if not article.title or not article.url:
                continue
            
            # Don't filter by content at transformation stage
            determined_category = category or "general"
            
            legal_article = LegalNewsItem(
                id=str(uuid4()),
                title=article.title,
                summary=article.description or article.title[:200] + "...",
                publishedDate=article.publishedAt,
                source=article.source.name,
                url=str(article.url),
                imageUrl=str(article.urlToImage) if article.urlToImage else None,
                category=determined_category,
                author=article.author
            )
            
            legal_articles.append(legal_article)
        
        print(f"DEBUG: Transformed {len(articles)} -> {len(legal_articles)} articles")
        return legal_articles
    
    async def _create_fallback_response(self, params: NewsSearchParams) -> NewsResponse:
        """Create a response with sample articles when API fails"""
        print("DEBUG: Creating fallback response with sample articles")
        
        sample_articles = [
            LegalNewsItem(
                id=str(uuid4()),
                title="Legal News Service Temporarily Unavailable",
                summary="We're experiencing technical difficulties fetching the latest legal news. This is a sample article to show the system is working.",
                publishedDate=datetime.now().isoformat(),
                source="System",
                url="https://example.com",
                category="system",
                author="System Administrator"
            ),
            LegalNewsItem(
                id=str(uuid4()),
                title="Sample Legal Article - Business Law Update",
                summary="This is a sample article showing how legal news would appear. In a real scenario, this would contain actual news content from legal sources.",
                publishedDate=(datetime.now() - timedelta(hours=2)).isoformat(),
                source="Sample Source",
                url="https://example.com/sample",
                category="business-law",
                author="Sample Author"
            ),
            LegalNewsItem(
                id=str(uuid4()),
                title="Sample Employment Law Case Study",
                summary="Another sample article demonstrating the news feed functionality. This would typically contain real employment law news and updates.",
                publishedDate=(datetime.now() - timedelta(hours=4)).isoformat(),
                source="Legal Times",
                url="https://example.com/sample2",
                category="employment-law",
                author="Legal Reporter"
            )
        ]
        
        return NewsResponse(
            articles=sample_articles,
            totalResults=len(sample_articles),
            page=1,
            pageSize=params.pageSize,
            totalPages=1
        )

# Global service instance
news_service = NewsService()
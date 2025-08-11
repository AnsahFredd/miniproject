from datetime import datetime, timedelta
from app.models.document import AcceptedDocument
from app.schemas.search import SearchResponse, SearchResult
from app.services.embedding_service import generate_embedding
from app.utils.similarity import cosine_similarity
from typing import List, Optional
import numpy as np


async def search_documents(
    query_embedding: List[float],
    user_id: str,
    top_k: int = 5,
    document_type: Optional[str] = None,
    legal_domain: Optional[str] = None,
    date_range: Optional[str] = None
):
       
     # Build query filter dynamically
    query_filter = {
        "user_id": user_id,
        "embedding": {"$ne": None}
    }

    if document_type:
        query_filter["file_type"] = document_type

    if legal_domain:
        query_filter["section"] = legal_domain

    if date_range:
        now = datetime.utcnow()
        if date_range == "Last 7 days":
            query_filter["upload_date"] = {"$gte": now - timedelta(days=7)}
        elif date_range == "Last 30 days":
            query_filter["upload_date"] = {"$gte": now - timedelta(days=30)}
        elif date_range == "Last 6 months":
            query_filter["upload_date"] = {"$gte": now - timedelta(days=180)}
        elif date_range == "Last year":
            query_filter["upload_date"] = {"$gte": now - timedelta(days=365)}

    documents = await AcceptedDocument.find(query_filter).to_list()

    ranked_docs = []
    
    for doc in documents:
        if not doc.embedding or not doc.content:
            continue

        score = cosine_similarity(query_embedding, doc.embedding)
        ranked_docs.append((doc, score))
    # Sort by similarity descending
    ranked_docs.sort(key=lambda x: x[1], reverse=True)

    return ranked_docs[:top_k]


async def perform_search(
        query: str, 
        top_k: int, 
        user_id: str, 
        documentType: Optional[str] = None,    # ← Change from document_type
        legalDomain: Optional[str] = None,     # ← Change from legal_domain  
        dateRange: Optional[str] = None  
        ) -> SearchResponse:
    
    query_embedding = generate_embedding(query)

    top_results = await search_documents(query_embedding, user_id, top_k, document_type=documentType, legal_domain=legalDomain, date_range=dateRange)

    return SearchResponse(results=[
        SearchResult(
            document_id=str(doc.id),
            title=doc.filename or "Untitled Document",
            section=doc.section or "No section",
            description=(doc.summary or doc.content[:300] + "...") if len(doc.content) > 300 else (doc.summary or doc.content) or "",
            similarity_score=float(score)
        )
        for doc, score in top_results
    ])

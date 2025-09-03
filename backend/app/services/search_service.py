from datetime import datetime, timedelta
import logging
from app.models.document import AcceptedDocument
from app.schemas.search import SearchResponse, SearchResult
from app.services.embedding import generate_embedding
from app.utils.similarity import cosine_similarity
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


async def search_documents(
    query_embedding: np.ndarray,
    user_id: str,
    top_k: int = 5,
    document_type: Optional[str] = None,
    legal_domain: Optional[str] = None,
    date_range: Optional[str] = None
):

    if not isinstance(query_embedding, np.ndarray):
        logger.error(f"Query embedding is not numpy array: {type(query_embedding)}")
        raise ValueError(f"Expected np.ndarray, got {type(query_embedding)}")
    
    if query_embedding.shape == ():
        logger.error("Query embedding is a scalar")
        raise ValueError("Query embedding must be a vector, not a scalar")
    
    logger.info(f"Search with query embedding shape: {query_embedding.shape}")
       
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

        try:
            # Convert document embedding to numpy array if needed
            doc_embedding = doc.embedding
            if isinstance(doc_embedding, list):
                doc_embedding = np.array(doc_embedding)
            elif not isinstance(doc_embedding, np.ndarray):
                logger.warning(f"Document {doc.id} has invalid embedding type: {type(doc_embedding)}")
                continue

            # Validate shapes match
            if doc_embedding.shape != query_embedding.shape:
                logger.error(f"Shape mismatch - query: {query_embedding.shape}, doc {doc.id}: {doc_embedding.shape}")
                continue

            score = cosine_similarity(query_embedding, doc.embedding)
            ranked_docs.append((doc, score))

        except Exception as e:
            logger.error(f"Error processing document {doc.id}: {e}")
            continue

       
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
    
    try:
    
        query_embedding = await generate_embedding(query)

        logger.info(f"Generated query embedding - type: {type(query_embedding)}, shape: {query_embedding.shape}")

        if query_embedding.shape == ():
                raise ValueError("Generated embedding is a scalar instead of vector")
            
        top_results = await search_documents(
            query_embedding, 
            user_id, 
            top_k, 
            document_type=documentType, 
            legal_domain=legalDomain, 
            date_range=dateRange
        )

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
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise
        

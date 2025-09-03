from typing import Dict, Any
from .config import DOCUMENT_TYPES, URGENCY_KEYWORDS, LEGAL_DOMAINS

class RuleBasedClassifier:
    def __init__(self):
        self.document_types = DOCUMENT_TYPES
        self.urgency_keywords = URGENCY_KEYWORDS
        self.legal_domains = LEGAL_DOMAINS

    def classify(self, content: str, filename: str = "") -> Dict[str, Any]:
        """Rule-based classification"""
        text = (content + " " + filename).lower()

        # Document type
        doc_type_scores = {}
        for doc_type, keywords in self.document_types.items():
            score = sum(1 for k in keywords if k in text)
            if score > 0:
                doc_type_scores[doc_type] = score

        best_doc_type = "general"
        doc_confidence = 0.0
        if doc_type_scores:
            best_doc_type = max(doc_type_scores.items(), key=lambda x: x[1])[0]
            doc_confidence = min(max(doc_type_scores.values()) / 3.0, 1.0)

        # Legal domain
        domain_scores = {}
        for domain, keywords in self.legal_domains.items():
            score = sum(1 for k in keywords if k in text)
            if score > 0:
                domain_scores[domain] = score

        best_domain = "general"
        domain_confidence = 0.0
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
            domain_confidence = min(max(domain_scores.values()) / 2.0, 1.0)

        # Urgency
        urgency_scores = {}
        for urgency, keywords in self.urgency_keywords.items():
            score = sum(1 for k in keywords if k in text)
            if score > 0:
                urgency_scores[urgency] = score

        best_urgency = "low"
        urgency_confidence = 0.0
        if urgency_scores:
            best_urgency = max(urgency_scores.items(), key=lambda x: x[1])[0]
            urgency_confidence = min(max(urgency_scores.values()) / 2.0, 1.0)

        return {
            "document_type": best_doc_type,
            "document_type_confidence": doc_confidence,
            "legal_domain": best_domain,
            "legal_domain_confidence": domain_confidence,
            "urgency": best_urgency,
            "urgency_confidence": urgency_confidence,
            "keyword_scores": {
                "document_types": doc_type_scores,
                "legal_domains": domain_scores,
                "urgency_levels": urgency_scores
            }
        }
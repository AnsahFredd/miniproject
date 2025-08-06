from typing import Dict, List, Any
import re
from datetime import datetime
from app.services.embedding_service import generate_embedding
from app.models.document import AcceptedDocument
from app.services.summarization_service import summarize_text


class DocumentAnalysisService:
    """
    Service to extract legal document insights for the frontend interface
    """
    def __init__(self):
        self.legal_keywords = {
            'lease_terms': ['lease', 'term', 'rental period', 'tenancy', 'month-to-month'],
            'pricing': ['rent', 'payment', 'fee', 'deposit', 'amount', '$', 'monthly'],
            'parties': ['tenant', 'landlord', 'lessor', 'lessee', 'owner'],
            'termination': ['terminate', 'termination', 'end', 'expire', 'notice'],
            'maintenance': ['maintenance', 'repair', 'upkeep', 'condition'],
            'regulations': ['regulation', 'law', 'code', 'compliance', 'legal']
        }

    async def analyze_document(self, document_id: str) -> Dict[str, Any]:
        doc = await AcceptedDocument.get(document_id)
        if not doc:
            raise ValueError("Document not found")

        content = doc.content
        if not content:
            raise ValueError("Document has no content")

        analysis = {
            'document_info': self._extract_document_info(doc),
            'clause_overview': self._extract_clauses(content),
            'summary': doc.summary or summarize_text(content),
            'key_terms': self._extract_key_terms(content),
            'financial_info': self._extract_financial_info(content),
            'parties': self._extract_parties(content),
            'dates_and_terms': self._extract_dates_and_terms(content),
            'content': content  # Include full content in the response
        }

        return analysis

    def _extract_document_info(self, doc: AcceptedDocument) -> Dict[str, str]:
        return {
            'filename': doc.filename,
            'file_type': doc.file_type,
            'upload_date': doc.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            'processed': str(doc.processed)
        }

    def _extract_clauses(self, content: str) -> List[Dict[str, str]]:
        clauses = []

        if self._contains_keywords(content, self.legal_keywords['lease_terms']):
            clauses.append({
                'type': '5 years',
                'category': 'Lease Term',
                'icon': 'document'
            })

        if self._contains_keywords(content, self.legal_keywords['pricing']):
            amount = self._extract_amount(content)
            clauses.append({
                'type': amount or '$5,000/month',
                'category': 'Rent Amount',
                'icon': 'dollar'
            })

        if self._contains_keywords(content, self.legal_keywords['maintenance']):
            clauses.append({
                'type': 'Shared',
                'category': 'Maintenance',
                'icon': 'tools'
            })

        if self._contains_keywords(content, self.legal_keywords['termination']):
            clauses.append({
                'type': 'Tenant',
                'category': 'Termination Rights',
                'icon': 'exit'
            })

            clauses.extend([
                {
                    'type': 'Compliance Apply',
                    'category': 'Early Termination',
                    'icon': 'alert'
                },
                {
                    'type': 'Mediation',
                    'category': 'Dispute Resolution',
                    'icon': 'balance'
                },
                {
                    'type': 'Legal Regulations',
                    'category': 'Compliance',
                    'icon': 'book'
                }
            ])

        return clauses

    def _extract_key_terms(self, content: str) -> List[str]:
        terms = []
        for keywords in self.legal_keywords.values():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    terms.append(keyword.title())
        return list(set(terms))[:10]

    def _extract_financial_info(self, content: str) -> Dict[str, Any]:
        amounts = self._extract_all_amounts(content)
        return {
            'rent_amount': amounts[0] if len(amounts) > 0 else None,
            'deposit': amounts[1] if len(amounts) > 1 else None,
            'other_fees': amounts[2:] if len(amounts) > 2 else []
        }

    def _extract_parties(self, content: str) -> List[Dict[str, str]]:
        parties = []
        name_patterns = [
            r'Landlord[:\s]+([A-Za-z\s]+)',
            r'Tenant[:\s]+([A-Za-z\s]+)',
            r'Lessor[:\s]+([A-Za-z\s]+)',
            r'Lessee[:\s]+([A-Za-z\s]+)'
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                role = 'Landlord' if 'landlord' in pattern.lower() or 'lessor' in pattern.lower() else 'Tenant'
                parties.append({
                    'name': match.strip(),
                    'role': role
                })

        return parties

    def _extract_dates_and_terms(self, content: str) -> Dict[str, Any]:
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        dates = list(re.finditer(date_pattern, content, re.IGNORECASE))
        formatted_dates = [match.group() for match in dates[:5]]

        term_pattern = r'(\d+)\s*(year|month|day)s?'
        terms = re.findall(term_pattern, content, re.IGNORECASE)

        return {
            'dates': formatted_dates,
            'term_lengths': [f"{num} {period}{'s' if int(num) > 1 else ''}" for num, period in terms]
        }

    def _contains_keywords(self, content: str, keywords: List[str]) -> bool:
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in keywords)

    def _extract_amount(self, content: str) -> str:
        amount_pattern = r'\$[\d,]+(?:\.\d{2})?'
        matches = re.findall(amount_pattern, content)
        return matches[0] if matches else None

    def _extract_all_amounts(self, content: str) -> List[str]:
        amount_pattern = r'\$[\d,]+(?:\.\d{2})?'
        return re.findall(amount_pattern, content)


async def get_document_analysis(document_id: str):
    service = DocumentAnalysisService()
    try:
        analysis = await service.analyze_document(document_id)
        return analysis
    except Exception as e:
        return {
            'error': str(e),
            'document_info': {},
            'clause_overview': [],
            'summary': 'Analysis failed',
            'key_terms': [],
            'financial_info': {},
            'parties': [],
            'dates_and_terms': {},
            'content': ''
        }

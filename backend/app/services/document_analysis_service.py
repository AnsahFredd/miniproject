from typing import Dict, List, Any
import re
from datetime import datetime
from app.services.embedding import generate_embedding
from app.models.document import AcceptedDocument
from app.services.summarization_service import summarize_text
import logging

logger = logging.getLogger(__name__)

class DocumentAnalysisService:
    """
    Service to extract legal document insights for the frontend interface
    """
    def __init__(self):
        self.legal_keywords = {
            'lease_terms': ['lease', 'term', 'rental period', 'tenancy', 'month-to-month', 'agreement', 'contract'],
            'pricing': ['rent', 'payment', 'fee', 'deposit', 'amount', '$', 'monthly', 'cost', 'price'],
            'parties': ['tenant', 'landlord', 'lessor', 'lessee', 'owner', 'renter', 'party', 'parties'],
            'termination': ['terminate', 'termination', 'end', 'expire', 'notice', 'cancel', 'cancellation'],
            'maintenance': ['maintenance', 'repair', 'upkeep', 'condition', 'maintain', 'fix', 'responsibility'],
            'regulations': ['regulation', 'law', 'code', 'compliance', 'legal', 'rule', 'govern'],
            'utilities': ['utilities', 'electric', 'gas', 'water', 'internet', 'cable', 'heating'],
            'pets': ['pet', 'pets', 'animal', 'dog', 'cat']
        }

    async def analyze_document(self, document_id: str) -> Dict[str, Any]:
        doc = await AcceptedDocument.get(document_id)
        if not doc:
            raise ValueError("Document not found")

        content = doc.content
        if not content:
            raise ValueError("Document has no content")

        try:
            if hasattr(doc, 'analysis_results') and doc.analysis_results:
                existing_results = doc.analysis_results
                logger.info(f"Found existing analysis results for document {document_id}")
                logger.info(f"Existing results keys: {list(existing_results.keys()) if isinstance(existing_results, dict) else 'Not a dict'}")
                
                if existing_results.get('clause_overview'):
                    logger.info(f"Using existing clause analysis for document {document_id}")
                    
                    # Safe extraction of nested data from existing results
                    existing_term_info = existing_results.get('term_information', {})
                    existing_financial = existing_results.get('financial_summary', {})
                    existing_parties = existing_results.get('parties_involved', [])
                    existing_dates = existing_results.get('important_dates', [])
                    existing_key_terms = existing_results.get('key_terms', [])
                    
                    # Handle potential malformed dates_terms structure
                    existing_dates_terms = existing_results.get('dates_terms', {})
                    if isinstance(existing_dates_terms, dict):
                        dates_from_existing = existing_dates_terms.get('dates', [])
                    else:
                        dates_from_existing = []
                    
                    # Use existing dates if available, otherwise use what's directly stored
                    final_dates = existing_dates if existing_dates else dates_from_existing
                    
                    # Return existing results with proper formatting and safe fallbacks
                    return {
                        'document_info': {
                            **self._extract_document_info(doc),
                            'content': content
                        },
                        'clause_overview': existing_results['clause_overview'],
                        'summary': existing_results.get('summary', {'text': doc.summary or "Summary not available"}),
                        'financial_summary': existing_financial if existing_financial else self._extract_financial_info(content),
                        'term_information': existing_term_info if existing_term_info else self._extract_term_information(content),
                        'parties_involved': existing_parties if existing_parties else self._extract_parties(content),
                        'important_dates': final_dates,
                        'key_terms': existing_key_terms if existing_key_terms else self._extract_key_terms(content)
                    }
            
            # Extract data (fallback if no existing results)
            logger.info(f"Extracting clauses for document {document_id}, content length: {len(content)}")
            clauses = self._extract_clauses(content)
            logger.info(f"Extracted {len(clauses)} clauses for document {document_id}")
            
            financial_info = self._extract_financial_info(content)
            dates_terms = self._extract_dates_and_terms(content)
            
            # Safe access to dates and term lengths
            important_dates = dates_terms.get('dates', []) if isinstance(dates_terms, dict) else []
            term_lengths = dates_terms.get('term_lengths', []) if isinstance(dates_terms, dict) else []
            primary_term = term_lengths[0] if term_lengths and len(term_lengths) > 0 else None
            
            # Format to match frontend expectations
            analysis = {
                'document_info': {
                    **self._extract_document_info(doc),
                    'content': content  # Frontend expects content here
                },
                'clause_overview': clauses,
                'summary': {
                    'text': doc.summary or "Summary not available"  # Frontend expects {text: string}
                },
                'financial_summary': {  # Frontend expects financial_summary, not financial_info
                    'rent_amount': financial_info.get('rent_amount'),
                    'deposit': financial_info.get('deposit'),
                    'other_fees': financial_info.get('other_fees', [])
                },
                'term_information': {  # Add missing term_information with safe access
                    'lease_duration': primary_term,
                    'primary_term': primary_term,
                    'renewal_option': "Available" if "renew" in content.lower() else "Not specified",
                    'renewal_term': "Standard" if "renew" in content.lower() else "Not specified"
                },
                'parties_involved': self._extract_parties(content),
                'important_dates': important_dates,
                'key_terms': self._extract_key_terms(content)
            }

            # Update document status
            doc.analysis_status = "completed"
            doc.contract_analyzed = True
            doc.analysis_completed_at = datetime.utcnow()
            await doc.save()

            return analysis
            
        except Exception as e:
            logger.error(f"Error in analyze_document for {document_id}: {str(e)}")
            doc.analysis_status = "failed"
            await doc.save()
            raise e

    def _extract_document_info(self, doc: AcceptedDocument) -> Dict[str, str]:
        return {
            'filename': doc.filename,
            'file_type': doc.file_type,
            'upload_date': doc.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            'processed': str(doc.processed)
        }

    def _extract_clauses(self, content: str) -> List[Dict[str, str]]:
        """
        Simplified and more reliable clause extraction with better structure matching frontend expectations
        """
        clauses = []
        content_lower = content.lower()
        
        logger.info(f"Starting clause extraction, content length: {len(content)}")
        
        # 1. Lease Term Detection
        lease_patterns = [
            r'lease.*?term.*?(\d+)\s*(year|month|day)s?',
            r'term.*?of.*?(\d+)\s*(year|month|day)s?',
            r'(\d+)\s*(year|month|day)\s*lease',
            r'tenancy.*?(\d+)\s*(year|month|day)s?'
        ]
        
        lease_term_found = False
        for pattern in lease_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                num, period = matches[0]
                term_text = f"{num} {period}{'s' if int(num) > 1 else ''}"
                clauses.append({
                    'type': term_text,
                    'category': 'Lease Term',
                    'icon': 'calendar',
                    'content': f"Lease term: {term_text}"
                })
                lease_term_found = True
                logger.info(f"Found lease term: {term_text}")
                break
        
        if not lease_term_found and any(keyword in content_lower for keyword in ['lease', 'rental', 'tenancy']):
            clauses.append({
                'type': 'Standard Term',
                'category': 'Lease Term', 
                'icon': 'calendar',
                'content': 'Standard lease term applies'
            })

        # 2. Rent Amount Detection
        rent_patterns = [
            r'\$[\d,]+(?:\.\d{2})?\s*(?:per\s*month|monthly|/month)',
            r'rent.*?\$[\d,]+(?:\.\d{2})?',
            r'monthly.*?payment.*?\$[\d,]+(?:\.\d{2})?'
        ]
        
        rent_found = False
        for pattern in rent_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                amount = re.search(r'\$[\d,]+(?:\.\d{2})?', matches[0])
                if amount:
                    clauses.append({
                        'type': f"{amount.group()}/month",
                        'category': 'Rent Amount',
                        'icon': 'dollar-sign',
                        'content': f"Monthly rent: {amount.group()}"
                    })
                    rent_found = True
                    logger.info(f"Found rent amount: {amount.group()}")
                    break
        
        if not rent_found:
            # Fallback: look for any dollar amount
            amount = self._extract_amount(content)
            if amount:
                clauses.append({
                    'type': f"{amount}/month",
                    'category': 'Rent Amount',
                    'icon': 'dollar-sign',
                    'content': f"Rent amount: {amount}"
                })
                rent_found = True

        # 3. Parties Detection
        parties = self._extract_parties(content)
        if parties:
            for party in parties[:2]:  # Limit to main parties
                clauses.append({
                    'type': f"{party['role']}: {party['name'][:30]}{'...' if len(party['name']) > 30 else ''}",
                    'category': 'Parties',
                    'icon': 'users',
                    'content': f"{party['role']}: {party['name']}"
                })
        elif any(keyword in content_lower for keyword in ['landlord', 'tenant', 'lessor', 'lessee']):
            clauses.append({
                'type': 'Landlord & Tenant',
                'category': 'Parties',
                'icon': 'users',
                'content': 'Landlord and tenant parties identified'
            })

        # 4. Security Deposit
        if any(keyword in content_lower for keyword in ['deposit', 'security deposit']):
            deposit_amount = self._extract_deposit_amount(content)
            clauses.append({
                'type': deposit_amount or 'Security Deposit Required',
                'category': 'Security Deposit',
                'icon': 'shield',
                'content': f"Security deposit: {deposit_amount or 'Amount specified in agreement'}"
            })

        # 5. Maintenance Responsibilities
        if any(keyword in content_lower for keyword in ['maintenance', 'repair', 'upkeep']):
            if 'tenant' in content_lower and any(word in content_lower for word in ['responsible', 'maintain']):
                responsibility = 'Tenant Responsible'
            elif 'landlord' in content_lower and any(word in content_lower for word in ['responsible', 'maintain']):
                responsibility = 'Landlord Responsible'
            else:
                responsibility = 'Shared Responsibility'
            
            clauses.append({
                'type': responsibility,
                'category': 'Maintenance',
                'icon': 'tool',
                'content': f"Maintenance responsibility: {responsibility}"
            })

        # 6. Termination/Notice
        if any(keyword in content_lower for keyword in ['terminate', 'notice', 'cancel', 'end']):
            notice_pattern = r'(\d+)\s*(?:day|week|month)s?\s*(?:notice|notification)'
            notice_matches = re.findall(notice_pattern, content_lower)
            
            notice_text = f"{notice_matches[0]} days notice" if notice_matches else "Notice Required"
            clauses.append({
                'type': notice_text,
                'category': 'Termination Rights',
                'icon': 'x-circle',
                'content': f"Termination notice: {notice_text}"
            })

        # 7. Utilities
        if any(keyword in content_lower for keyword in ['utilities', 'electric', 'gas', 'water']):
            clauses.append({
                'type': 'Utility Provisions',
                'category': 'Utilities',
                'icon': 'zap',
                'content': 'Utility arrangements specified'
            })

        # 8. Pet Policy
        if any(keyword in content_lower for keyword in ['pet', 'pets', 'animal']):
            if 'no pets' in content_lower:
                pet_policy = 'No Pets Allowed'
            elif 'pets allowed' in content_lower:
                pet_policy = 'Pets Allowed'
            else:
                pet_policy = 'Pet Policy Specified'
            
            clauses.append({
                'type': pet_policy,
                'category': 'Pet Policy',
                'icon': 'heart',
                'content': f"Pet policy: {pet_policy}"
            })

        # Ensure we always have some clauses for legal documents
        if not clauses and any(word in content_lower for word in ['lease', 'agreement', 'contract', 'rental']):
            clauses.extend([
                {
                    'type': 'Legal Agreement',
                    'category': 'Document Type',
                    'icon': 'file-text',
                    'content': 'Legal agreement document identified'
                },
                {
                    'type': 'Terms & Conditions',
                    'category': 'Legal Terms',
                    'icon': 'book-open',
                    'content': 'Terms and conditions apply'
                }
            ])

        logger.info(f"Clause extraction completed: {len(clauses)} clauses found")
        for clause in clauses:
            logger.info(f"  - {clause['category']}: {clause['type']}")
        
        return clauses

    def _extract_deposit_amount(self, content: str) -> str:
        """Extract security deposit amount"""
        deposit_patterns = [
            r'(?:security\s*deposit|deposit).*?\$[\d,]+(?:\.\d{2})?',
            r'\$[\d,]+(?:\.\d{2})?\s*(?:security\s*deposit|deposit)'
        ]
        
        for pattern in deposit_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                amount = re.search(r'\$[\d,]+(?:\.\d{2})?', matches[0])
                if amount:
                    return amount.group()
        return None

    def _extract_key_terms(self, content: str) -> List[str]:
        terms = []
        for keywords in self.legal_keywords.values():
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    terms.append(keyword.title())
        return list(set(terms))[:10]

    def _extract_financial_info(self, content: str) -> Dict[str, Any]:
        """Extract financial information with proper error handling"""
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
        """Extract dates and terms with proper error handling"""
        try:
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
            dates = list(re.finditer(date_pattern, content, re.IGNORECASE))
            formatted_dates = [match.group() for match in dates[:5]]

            term_pattern = r'(\d+)\s*(year|month|day)s?'
            terms = re.findall(term_pattern, content, re.IGNORECASE)

            return {
                'dates': formatted_dates,
                'term_lengths': [f"{num} {period}{'s' if int(num) > 1 else ''}" for num, period in terms]
            }
        except Exception as e:
            logger.error(f"Error extracting dates and terms: {str(e)}")
            return {
                'dates': [],
                'term_lengths': []
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

    def _extract_term_information(self, content: str) -> Dict[str, Any]:
        """Extract term information with proper error handling"""
        try:
            dates_terms = self._extract_dates_and_terms(content)
            term_lengths = dates_terms.get('term_lengths', []) if isinstance(dates_terms, dict) else []
            primary_term = term_lengths[0] if term_lengths and len(term_lengths) > 0 else None
            
            return {
                'lease_duration': primary_term,
                'primary_term': primary_term,
                'renewal_option': "Available" if "renew" in content.lower() else "Not specified",
                'renewal_term': "Standard" if "renew" in content.lower() else "Not specified"
            }
        except Exception as e:
            logger.error(f"Error extracting term information: {str(e)}")
            return {
                'lease_duration': None,
                'primary_term': None,
                'renewal_option': "Not specified",
                'renewal_term': "Not specified"
            }


async def get_document_analysis(document_id: str):
    """Get document analysis with enhanced error handling"""
    service = DocumentAnalysisService()
    try:
        logger.info(f"Starting analysis for document {document_id}")
        analysis = await service.analyze_document(document_id)
        logger.info(f"Analysis completed for {document_id}, clause_overview length: {len(analysis.get('clause_overview', []))}")
        return analysis
    except Exception as e:
        logger.error(f"Analysis failed for {document_id}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        

        return {
            'error': str(e),
            'document_info': {},
            'clause_overview': [],
            'summary': {'text': 'Analysis failed'},
            'key_terms': [],
            'financial_summary': {},
            'parties_involved': [],
            'important_dates': [],
            'term_information': {}
      }  
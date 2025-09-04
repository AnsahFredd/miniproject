"""
Configuration and constants for QA service
"""
from pathlib import Path
import torch

# Model paths and configurations
QA_NAME = "microsoft/deberta-v3-large"
QA_PATH = Path("app/ai/models/question-answering")
LEGAL_QA_NAME = "deepset/roberta-base-squad2"
LEGAL_QA_PATH = Path("app/ai/models/legal_qa")
LEGAL_NAME = "nlpaueb/legal-bert-base-uncased"
LEGAL_PATH = Path("app/ai/models/legal_name")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Legal keywords for question detection
LEGAL_KEYWORDS = {
    'contract', 'agreement', 'clause', 'legal', 'law', 'court', 'case', 'defendant',
    'plaintiff', 'liability', 'breach', 'damages', 'jurisdiction', 'statute',
    'regulation', 'compliance', 'terms', 'conditions', 'warranty', 'indemnity',
    'termination', 'penalty', 'arbitration', 'litigation', 'patent', 'copyright',
    'trademark', 'intellectual property', 'confidentiality', 'non-disclosure',
    'lawyer', 'attorney', 'legal advice', 'lawsuit', 'settlement', 'appeal',
    'parties', 'enforceability', 'consideration', 'obligations'
}

# Contract patterns for document type identification
CONTRACT_PATTERNS = {
    'professional_services': [
        r'professional\s+services?\s+agreement',
        r'service\s+provider',
        r'client.*service',
        r'scope\s+of\s+work',
        r'deliverables',
        r'consulting\s+agreement'
    ],
    'lease_agreement': [
        r'lease\s+agreement',
        r'rental\s+agreement', 
        r'landlord.*tenant',
        r'lessor.*lessee',
        r'monthly\s+rent',
        r'lease\s+term',
        r'premises'
    ],
    'employment': [
        r'employment\s+agreement',
        r'employee.*employer',
        r'job\s+description',
        r'salary',
        r'benefits'
    ],
    'nda': [
        r'non.?disclosure\s+agreement',
        r'confidentiality\s+agreement',
        r'confidential\s+information',
        r'proprietary\s+information'
    ]
}

# Essential legal elements patterns
ESSENTIAL_ELEMENTS = {
    'parties': [
        r'between\s+([A-Z][a-z\s,]+)\s+and\s+([A-Z][a-z\s,]+)',
        r'client:\s*([A-Z][a-z\s,]+)',
        r'service\s+provider:\s*([A-Z][a-z\s,]+)',
        r'landlord:\s*([A-Z][a-z\s,]+)',
        r'tenant:\s*([A-Z][a-z\s,]+)'
    ],
    'consideration': [
        r'\$[\d,]+(?:\.\d{2})?',
        r'\d+\s+dollars?',
        r'payment\s+of',
        r'monthly\s+rent',
        r'fee\s+of'
    ],
    'terms': [
        r'term\s+of\s+\d+',
        r'for\s+a\s+period\s+of',
        r'commencing\s+on',
        r'ending\s+on',
        r'shall\s+be\s+effective'
    ],
    'obligations': [
        r'shall\s+provide',
        r'agrees\s+to',
        r'responsible\s+for',
        r'obligated\s+to',
        r'duty\s+to'
    ]
}

# Legal question detection patterns
LEGAL_QUESTION_PATTERNS = [
    r'what type.{0,20}contract',
    r'enforceable|enforceability',
    r'missing.{0,10}(elements|clauses)',
    r'parties.{0,10}(involved|agreement)',
    r'legal.{0,10}(valid|binding|issues)',
    r'contract.{0,10}(valid|binding|enforceable)'
]

# Date extraction patterns
DATE_PATTERNS = [
    r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
    r'\b\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{2,4}\b',
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{2,4}\b'
]

# Custom exceptions
class QAModelError(Exception):
    """Custom exception for QA model-related errors"""
    pass

class DocumentNotFoundError(Exception):
    """Raised when document cannot be found"""
    pass

class ContextTooLongError(Exception):
    """Raised when context exceeds maximum length"""
    pass
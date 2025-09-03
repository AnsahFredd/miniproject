import os
from pathlib import Path

# Model Configuration
QA_MODEL = os.getenv("QA_MODEL", "law-ai/InLegalBERT")
QA_MODEL_PATH = os.getenv("QA_MODEL_PATH", "app/ai/models/classification")
DEVICE = "cpu"  # Force CPU for stability
MAX_LENGTH = 512

# Document type mapping
DOCUMENT_TYPES = {
    'contract': ['contract', 'agreement', 'deed', 'covenant', 'compact'],
    'lease': ['lease', 'rental', 'tenancy', 'rent'],
    'legal_brief': ['brief', 'motion', 'petition', 'complaint', 'pleading'],
    'policy': ['policy', 'procedure', 'guideline', 'standard', 'protocol'],
    'regulation': ['regulation', 'statute', 'law', 'code', 'ordinance'],
    'financial': ['invoice', 'receipt', 'financial', 'budget', 'statement'],
    'correspondence': ['letter', 'memo', 'email', 'correspondence', 'notice'],
    'report': ['report', 'analysis', 'study', 'review', 'assessment']
}

URGENCY_KEYWORDS = {
    'high': ['urgent', 'immediate', 'critical', 'emergency', 'deadline', 'expires'],
    'medium': ['important', 'priority', 'attention', 'review', 'action required'],
    'low': ['information', 'fyi', 'reference', 'notice', 'update']
}

LEGAL_DOMAINS = {
    'real_estate': ['property', 'real estate', 'lease', 'rent', 'landlord', 'tenant'],
    'corporate': ['corporation', 'company', 'business', 'merger', 'acquisition'],
    'employment': ['employment', 'employee', 'worker', 'job', 'salary', 'benefits'],
    'intellectual_property': ['patent', 'trademark', 'copyright', 'ip', 'invention'],
    'litigation': ['lawsuit', 'court', 'judge', 'trial', 'plaintiff', 'defendant'],
    'compliance': ['compliance', 'regulation', 'audit', 'violation', 'penalty']
}
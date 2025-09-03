import re
from typing import List, Dict

class EntityExtractor:
    def __init__(self):
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
        ]
        
        self.money_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'(?:USD|USD\$|dollars?)\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|USD)'
        ]
        
        self.role_patterns = {
            "party": r"(?:plaintiff|defendant|appellant|appellee|petitioner|respondent|claimant)",
            "legal_entity": r"(?:corporation|corp\.?|llc|l\.l\.c\.?|inc\.?|ltd\.?|company|co\.?|firm|partnership)",
            "court": r"(?:court|tribunal|judge|magistrate|justice|honorable|hon\.)",
            "legal_profession": r"(?:attorney|lawyer|counsel|esquire|esq\.?|barrister|solicitor)"
        }

    def extract_entities(self, content: str) -> List[Dict]:
        """Extract legal entities from text"""
        entities = []

        # Extract dates
        for pattern in self.date_patterns:
            for date in re.findall(pattern, content, re.IGNORECASE)[:5]:
                entities.append({"type": "date", "value": date.strip()})

        # Extract money amounts
        for pattern in self.money_patterns:
            for amount in re.findall(pattern, content, re.IGNORECASE)[:5]:
                entities.append({"type": "money", "value": amount.strip()})

        # Extract legal roles
        for entity_type, pattern in self.role_patterns.items():
            for match in re.findall(pattern, content, re.IGNORECASE)[:3]:
                entities.append({"type": entity_type, "value": match.strip()})

        # Extract case citations
        citation_pattern = r'\b\d+\s+[A-Z][a-z]+\s+\d+\b|\b\d+\s+[A-Z]\.?\s*\d+[a-z]?\s+\d+\b'
        for citation in re.findall(citation_pattern, content)[:3]:
            entities.append({"type": "case_citation", "value": citation.strip()})

        return entities
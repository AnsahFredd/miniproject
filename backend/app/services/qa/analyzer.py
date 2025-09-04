"""
Legal document analysis using pattern matching and AI
"""
from typing import Dict, List, Any
import re
import logging
from .config import CONTRACT_PATTERNS, ESSENTIAL_ELEMENTS
from ..legal_ai_service import legal_ai_service

logger = logging.getLogger(__name__)


class LegalDocumentAnalyzer:
    """Enhanced legal document analysis using pattern matching and AI models"""
    
    def __init__(self):
        self.contract_patterns = CONTRACT_PATTERNS
        self.essential_elements = ESSENTIAL_ELEMENTS

    def analyze_document_type(self, content: str) -> Dict[str, Any]:
        """Analyze document type using pattern matching"""
        content_lower = content.lower()
        type_scores = {}
        
        for doc_type, patterns in self.contract_patterns.items():
            score = 0
            matches = []
            for pattern in patterns:
                pattern_matches = re.findall(pattern, content_lower)
                if pattern_matches:
                    score += len(pattern_matches)
                    matches.extend(pattern_matches)
            
            if score > 0:
                type_scores[doc_type] = {
                    'score': score,
                    'matches': matches[:3]
                }
        
        if not type_scores:
            return {
                'document_type': 'unknown',
                'confidence': 0.0,
                'analysis': 'Could not identify document type'
            }
        
        best_type = max(type_scores.keys(), key=lambda x: type_scores[x]['score'])
        total_score = sum(data['score'] for data in type_scores.values())
        confidence = type_scores[best_type]['score'] / max(total_score, 1)
        
        return {
            'document_type': best_type.replace('_', ' ').title(),
            'confidence': min(confidence, 1.0),
            'analysis': f"Identified as {best_type.replace('_', ' ')} based on {type_scores[best_type]['score']} pattern matches",
            'all_scores': type_scores
        }

    def analyze_essential_elements(self, content: str) -> Dict[str, Any]:
        """Analyze essential legal elements"""
        content_lower = content.lower()
        elements_found = {}
        missing_elements = []
        
        for element_type, patterns in self.essential_elements.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, content_lower)
                if found:
                    matches.extend(found[:2])
            
            if matches:
                elements_found[element_type] = matches
            else:
                missing_elements.append(element_type)
        
        return {
            'found_elements': elements_found,
            'missing_elements': missing_elements,
            'completeness_score': len(elements_found) / len(self.essential_elements)
        }

    def analyze_enforceability_issues(self, content: str) -> List[str]:
        """Identify potential enforceability issues"""
        issues = []
        content_lower = content.lower()
        
        doc_analysis = self.analyze_document_type(content)
        if len(doc_analysis.get('all_scores', {})) > 1:
            issues.append("Document contains elements of multiple agreement types which could create enforceability issues")
        
        party_patterns = [r'between\s+[A-Z]', r'client:', r'service\s+provider:', r'landlord:', r'tenant:']
        party_matches = sum(1 for pattern in party_patterns if re.search(pattern, content_lower))
        
        if party_matches == 0:
            issues.append("No clearly identified parties found - essential for enforceability")
        elif party_matches == 1:
            issues.append("Only one party clearly identified - contracts require at least two parties")
        
        consideration_patterns = [r'\$\d', r'payment', r'rent', r'fee', r'compensation']
        if not any(re.search(pattern, content_lower) for pattern in consideration_patterns):
            issues.append("No consideration (payment/exchange of value) clearly identified")
        
        obligation_patterns = [r'shall', r'agrees?\s+to', r'responsible', r'obligated']
        if not any(re.search(pattern, content_lower) for pattern in obligation_patterns):
            issues.append("No clear obligations or duties specified")
        
        if len(content.strip()) < 200:
            issues.append("Document appears too brief for a comprehensive legal agreement")
        
        return issues


# Utility functions for external use
def analyze_document_type(content: str) -> Dict[str, Any]:
    """AI-powered document type analysis with fallback"""
    try:
        ai_result = legal_ai_service.analyze_contract_type(content)
        if ai_result.get("success"):
            analysis_data = ai_result["analysis"]
            return {
                "type": analysis_data.get("document_type", "Unknown"),
                "confidence": analysis_data.get("confidence", 0.0),
                "analysis": analysis_data.get("legal_assessment", "AI analysis completed"),
                "ai_powered": True
            }
    except Exception as e:
        logger.warning(f"AI document analysis failed, using fallback: {e}")
    
    # Fallback to pattern matching
    analyzer = LegalDocumentAnalyzer()
    result = analyzer.analyze_document_type(content)
    return {**result, "ai_powered": False}


def analyze_essential_elements(content: str) -> Dict[str, Any]:
    """AI-enhanced essential elements analysis"""  
    try:
        ai_result = legal_ai_service.analyze_contract_type(content)
        if ai_result.get("success"):
            analysis_data = ai_result["analysis"]
            return {
                "found_elements": analysis_data.get("key_characteristics", []),
                "missing_elements": analysis_data.get("missing_elements", []),
                "ai_powered": True
            }
    except Exception as e:
        logger.warning(f"AI elements analysis failed, using fallback: {e}")
    
    # Fallback to pattern matching
    analyzer = LegalDocumentAnalyzer()
    result = analyzer.analyze_essential_elements(content)
    return {**result, "ai_powered": False}


def analyze_enforceability_issues(content: str) -> List[str]:
    """AI-enhanced enforceability analysis"""
    try:
        ai_result = legal_ai_service.analyze_contract_enforceability(content)
        if ai_result.get("success"):
            analysis_data = ai_result["analysis"]
            return analysis_data.get("legal_issues", []) + analysis_data.get("enforceability_concerns", [])
    except Exception as e:
        logger.warning(f"AI enforceability analysis failed, using fallback: {e}")
    
    # Fallback to pattern matching
    analyzer = LegalDocumentAnalyzer()
    return analyzer.analyze_enforceability_issues(content)
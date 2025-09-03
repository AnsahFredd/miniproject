from typing import Dict, Any

class UtilsMixin:
    def _classify_question_type(self, question: str) -> str:
        question_lower = question.lower()
        
        if any(phrase in question_lower for phrase in ['what type', 'contract type', 'document type']):
            return "document_classification"
        elif any(phrase in question_lower for phrase in ['enforceable', 'enforceability', 'legally valid']):
            return "enforceability_analysis"
        elif any(phrase in question_lower for phrase in ['parties', 'who are', 'between whom']):
            return "party_identification"
        elif any(phrase in question_lower for phrase in ['missing', 'what is missing', 'incomplete']):
            return "completeness_analysis"
        elif any(phrase in question_lower for phrase in ['cost', 'price', 'rent', 'payment', 'fee']):
            return "financial_terms"
        elif any(phrase in question_lower for phrase in ['confidential', 'nda', 'disclosure']):
            return "confidentiality_analysis"
        else:
            return "general_legal_question"

    def _parse_ai_text_response(self, ai_response: str, content: str) -> Dict[str, Any]:
        analysis = {
            "document_type": "Unknown",
            "confidence": 0.7,
            "mixed_types": [],
            "key_characteristics": [],
            "structural_issues": [],
            "missing_elements": [],
            "enforceability_concerns": [],
            "legal_assessment": ai_response[:500] + "..." if len(ai_response) > 500 else ai_response
        }
        
        if "professional services" in ai_response.lower():
            analysis["document_type"] = "Professional Services Agreement"
        elif "lease" in ai_response.lower():
            analysis["document_type"] = "Lease Agreement"
        elif "mixed" in ai_response.lower() or "multiple" in ai_response.lower():
            analysis["document_type"] = "Mixed Document"
            analysis["mixed_types"] = ["Professional Services", "Lease"]
        
        return analysis

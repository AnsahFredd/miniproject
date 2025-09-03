import logging
from typing import Dict, Any
from .legal_doc_analyzer import LegalDocumentAnalyzer

logger = logging.getLogger(__name__)

class FallbackMixin:
    def _fallback_contract_analysis(self, content: str) -> Dict[str, Any]:
        try:
            legal_analyzer = LegalDocumentAnalyzer()
            
            doc_type_analysis = legal_analyzer.analyze_document_type(content)
            essential_elements = legal_analyzer.analyze_essential_elements(content)
            enforceability_issues = legal_analyzer.analyze_enforceability_issues(content)
            
            analysis = {
                "document_type": doc_type_analysis.get("document_type", "Unknown"),
                "confidence": doc_type_analysis.get("confidence", 0.5),
                "mixed_types": [],
                "key_characteristics": ["Pattern-based analysis (AI unavailable)"],
                "structural_issues": enforceability_issues[:5],
                "missing_elements": essential_elements.get("missing_elements", []),
                "enforceability_concerns": enforceability_issues[:3],
                "legal_assessment": f"Analysis performed using pattern matching. Document type: {doc_type_analysis.get('document_type', 'Unknown')} with {doc_type_analysis.get('confidence', 0):.1%} confidence. For comprehensive analysis, ensure AI service is properly configured."
            }
            
            return {
                "analysis": analysis,
                "success": True,
                "ai_model": "fallback_pattern_matching",
                "note": "Using enhanced pattern matching - AI service unavailable"
            }
        except Exception as e:
            logger.error(f"Even fallback analysis failed: {e}")
            return {
                "analysis": {
                    "document_type": "Analysis Failed",
                    "confidence": 0.0,
                    "mixed_types": [],
                    "key_characteristics": [],
                    "structural_issues": [],
                    "missing_elements": [],
                    "enforceability_concerns": [],
                    "legal_assessment": f"Document analysis failed: {str(e)}. Please check system configuration."
                },
                "success": False,
                "error": str(e)
            }

    def _fallback_question_answering(self, question: str, context: str) -> Dict[str, Any]:
        try:
            legal_analyzer = LegalDocumentAnalyzer()
            
            doc_type_analysis = legal_analyzer.analyze_document_type(context)
            essential_elements = legal_analyzer.analyze_essential_elements(context)
            enforceability_issues = legal_analyzer.analyze_enforceability_issues(context)
            
            question_type = self._classify_question_type(question)
            
            if question_type == "document_classification":
                answer = f"Based on pattern analysis: This appears to be a {doc_type_analysis.get('document_type', 'unknown document')} with {doc_type_analysis.get('confidence', 0):.1%} confidence. {doc_type_analysis.get('analysis', '')}"
            elif question_type == "enforceability_analysis":
                if enforceability_issues:
                    answer = f"Enforceability concerns identified: {'; '.join(enforceability_issues[:3])}. For detailed legal analysis, ensure AI service is configured."
                else:
                    answer = "Pattern analysis suggests basic enforceability elements may be present, but comprehensive AI analysis is needed for definitive assessment."
            elif question_type == "party_identification":
                parties_found = essential_elements.get("found_elements", {}).get("parties", [])
                if parties_found:
                    answer = f"Parties identified through pattern matching: {', '.join(parties_found[:3])}. Note: This is basic pattern recognition, not full legal analysis."
                else:
                    answer = "No clear party identification found through pattern matching. Professional AI analysis recommended."
            else:
                answer = f"I can provide basic pattern-based analysis, but comprehensive legal AI analysis is unavailable. For detailed legal assessment of '{question}', please ensure the AI service is properly configured with valid API keys."
            
            return {
                "answer": answer,
                "confidence": 0.4,
                "source": "Enhanced Pattern Matching",
                "model": "fallback_enhanced",
                "question_type": question_type,
                "note": "AI service unavailable - using enhanced pattern matching"
            }
        except Exception as e:
            logger.error(f"Fallback question answering failed: {e}")
            return {
                "answer": f"I encountered an error while analyzing your question: {str(e)}. Please check system configuration.",
                "confidence": 0.0,
                "source": "Error Handler",
                "model": "error",
                "question_type": "error"
            }

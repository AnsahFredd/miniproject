import json
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AnalysisMixin:
    def analyze_contract_type(self, content: str) -> Dict[str, Any]:
        if not self.openai_client:
            return self._fallback_contract_analysis(content)
        
        truncated_content = content[:self.max_context_length] if len(content) > self.max_context_length else content
        
        prompt = f"""You are an expert legal document analyzer. Analyze this document and provide detailed analysis.

Document content:
{truncated_content}

Provide analysis in JSON format with these fields:
1. "document_type": Primary document type (e.g., "Professional Services Agreement", "Commercial Lease", "Mixed Document")
2. "confidence": Confidence score (0.0 to 1.0)
3. "mixed_types": List of document types if mixed (empty array if not mixed)
4. "key_characteristics": List of 3-5 key legal characteristics found
5. "structural_issues": List of structural problems identified
6. "missing_elements": List of essential elements that are missing
7. "enforceability_concerns": List of enforceability issues
8. "legal_assessment": Overall legal assessment paragraph

Be specific about legal issues and provide professional analysis."""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert legal document analyzer with 20+ years of contract law experience. Provide detailed, professional analysis in valid JSON format only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=self.temperature
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            try:
                analysis = json.loads(ai_response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(1))
                else:
                    analysis = self._parse_ai_text_response(ai_response, truncated_content)
            
            return {
                "analysis": analysis,
                "success": True,
                "ai_model": self.model,
                "content_length": len(content),
                "truncated": len(content) > self.max_context_length
            }
        except Exception as e:
            logger.error(f"AI contract analysis failed: {e}")
            return self._fallback_contract_analysis(content)

    def analyze_contract_enforceability(self, content: str) -> Dict[str, Any]:
        if not self.openai_client:
            return {"enforceability": "Cannot analyze - AI service unavailable", "score": 0.0}
        
        truncated_content = content[:self.max_context_length] if len(content) > self.max_context_length else content
        
        prompt = f"""As a legal expert, analyze this contract's enforceability:

{truncated_content}

Provide JSON analysis with:
1. "enforceability_score": 0.0-1.0 score
2. "enforceability_level": "High", "Moderate", "Low", or "Very Low"
3. "essential_elements_present": List of present essential elements
4. "missing_essential_elements": List of missing essential elements  
5. "legal_issues": List of specific legal concerns
6. "recommendations": List of recommendations to improve enforceability
7. "summary": Brief enforceability summary

Focus on: parties, consideration, legal capacity, legality, mutual assent."""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a contract law expert. Analyze enforceability thoroughly and provide valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=self.temperature
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            try:
                analysis = json.loads(ai_response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(1))
                else:
                    analysis = {"summary": ai_response, "enforceability_score": 0.5}
            
            return {
                "analysis": analysis,
                "success": True,
                "model": self.model
            }
        except Exception as e:
            logger.error(f"AI enforceability analysis failed: {e}")
            return {"enforceability": f"Analysis failed: {e}", "score": 0.0}

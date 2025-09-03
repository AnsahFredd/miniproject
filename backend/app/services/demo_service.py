"""Dedicated demo service that showcases AI processing without database persistence."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import os
import glob

from app.services.document_validator import LegalContractValidator
from app.utils.file_utils import parse_file_content

validator = LegalContractValidator()
logger = logging.getLogger("demo_service")

class DemoService:
    """Demo service that processes sample documents without database persistence."""
    
    def __init__(self):
        # DocumentProcessor is static, no need to instantiate
        self.sample_contracts_folder = os.path.join("sample_contracts")
        self.sample_documents = {
            "employment_contract": {
                "base_filename": "employment_contract",
                "title": "Employment Contract Demo Analysis",
                "note": "Sample employment contract for demonstration"
            },
            "service_agreement": {
                "base_filename": "service_agreement", 
                "title": "Service Agreement Demo Analysis",
                "note": "Sample service agreement for demonstration"
            },
            "lease_agreement": {
                "base_filename": "lease_agreement",
                "title": "Lease Agreement Demo Analysis", 
                "note": "Sample lease agreement for demonstration"
            }
        }
    
    def _find_sample_file(self, base_filename: str) -> Optional[tuple[str, str]]:
        """
        Find a sample file with the given base filename in supported formats.
        
        Args:
            base_filename: Base name of the file to search for
            
        Returns:
            Tuple of (full_path, extension) if found, None otherwise
        """
        if not os.path.exists(self.sample_contracts_folder):
            logger.debug(f"Sample contracts folder '{self.sample_contracts_folder}' not found")
            return None
        
        # Supported file extensions in order of preference
        supported_extensions = ['txt', 'pdf', 'docx']
        
        for ext in supported_extensions:
            pattern = os.path.join(self.sample_contracts_folder, f"{base_filename}.{ext}")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                file_path = matching_files[0]  # Take the first match
                logger.info(f"Found sample file: {file_path}")
                return file_path, ext
        
        # Also check for files that start with the base filename
        for ext in supported_extensions:
            pattern = os.path.join(self.sample_contracts_folder, f"{base_filename}*.{ext}")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                file_path = matching_files[0]  # Take the first match
                logger.info(f"Found sample file with pattern: {file_path}")
                return file_path, ext
        
        logger.debug(f"No sample file found for '{base_filename}' in '{self.sample_contracts_folder}'")
        return None
    
    def _load_sample_content(self, base_filename: str) -> tuple[str, str]:
        """
        Load sample document content from files or fallback to hardcoded content.
        
        Args:
            base_filename: Base filename to search for
            
        Returns:
            Tuple of (content, actual_filename)
        """
        file_info = self._find_sample_file(base_filename)
        
        if file_info:
            file_path, ext = file_info
            actual_filename = os.path.basename(file_path)
            
            try:
                if ext == 'txt':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    logger.info(f"Loaded text file: {actual_filename}")
                    return content, actual_filename
                
                elif ext in ['pdf', 'docx']:
                    # Use the existing file parser utility
                    content = parse_file_content(file_path)
                    logger.info(f"Parsed {ext.upper()} file: {actual_filename}")
                    return content, actual_filename
                    
            except Exception as e:
                logger.warning(f"Failed to load sample file '{file_path}': {str(e)}")
                logger.info("Falling back to hardcoded content")
        
        # Fallback to hardcoded content
        fallback_content = self._get_fallback_content(f"{base_filename}.txt")
        fallback_filename = f"sample_{base_filename}.pdf"
        logger.info(f"Using fallback content for: {fallback_filename}")
        
        return fallback_content, fallback_filename
    
    def _get_fallback_content(self, filename: str) -> str:
        """Fallback sample content if files are missing."""
        fallback_content = {
            "employment_contract.txt": """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into on [DATE] between [COMPANY NAME], a corporation organized under the laws of [STATE] ("Company"), and [EMPLOYEE NAME] ("Employee").

1. POSITION AND DUTIES
Employee agrees to serve as [POSITION TITLE] and perform duties assigned by the Company.

2. COMPENSATION
Company shall pay Employee a base salary of $[AMOUNT] per year, payable in accordance with Company's standard payroll practices.

3. BENEFITS
Employee shall be entitled to participate in Company's benefit plans including health insurance, dental coverage, and retirement plans.

4. TERM OF EMPLOYMENT
This Agreement shall commence on [START DATE] and continue until terminated by either party.

5. CONFIDENTIALITY
Employee agrees to maintain confidential information and trade secrets of the Company.

6. TERMINATION
Either party may terminate this agreement with [NOTICE PERIOD] written notice.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

Company: _________________    Employee: _________________
            """,
            "service_agreement.txt": """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is made between [CLIENT NAME] ("Client") and [SERVICE PROVIDER NAME] ("Service Provider").

1. SERVICES
Service Provider agrees to provide [DESCRIPTION OF SERVICES] as detailed in Exhibit A.

2. PAYMENT TERMS
Client agrees to pay Service Provider the total amount of $[AMOUNT] according to the payment schedule outlined herein.

3. DELIVERABLES
Service Provider shall deliver the following: [LIST OF DELIVERABLES]

4. TIMELINE
Services shall be completed by [COMPLETION DATE].

5. INTELLECTUAL PROPERTY
All work product created under this agreement shall belong to Client.

6. LIABILITY AND WARRANTIES
Service Provider warrants that services will be performed in a professional manner.

7. TERMINATION
This agreement may be terminated by either party with [NOTICE PERIOD] written notice.

Signed:
Client: _________________    Service Provider: _________________
            """,
            "lease_agreement.txt": """
RESIDENTIAL LEASE AGREEMENT

This Lease Agreement is entered into between [LANDLORD NAME] ("Landlord") and [TENANT NAME] ("Tenant") for the property located at [PROPERTY ADDRESS].

1. LEASE TERM
The lease term begins on [START DATE] and ends on [END DATE].

2. RENT
Monthly rent is $[AMOUNT], due on the first day of each month.

3. SECURITY DEPOSIT
Tenant shall pay a security deposit of $[AMOUNT] before occupancy.

4. USE OF PREMISES
The premises shall be used solely as a private residence for Tenant and immediate family.

5. MAINTENANCE AND REPAIRS
Tenant is responsible for routine maintenance and minor repairs under $[AMOUNT].

6. PETS
[PET POLICY DETAILS]

7. TERMINATION
Either party may terminate with [NOTICE PERIOD] written notice as required by law.

8. GOVERNING LAW
This lease shall be governed by the laws of [STATE/JURISDICTION].

Landlord: _________________    Tenant: _________________
Date: _________________        Date: _________________
            """
        }
        return fallback_content.get(filename, "Sample legal document content for demonstration purposes.")
    
    def _generate_mock_summary(self, content: str, contract_type: str) -> str:
        """Generate a mock summary for demo purposes."""
        # Extract some basic info from content for realistic summary
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        key_terms = []
        
        # Look for common contract elements
        for line in lines:
            lower_line = line.lower()
            if any(term in lower_line for term in ['compensation', 'salary', 'payment', 'rent']):
                key_terms.append("compensation terms")
            elif any(term in lower_line for term in ['term', 'duration', 'period']):
                key_terms.append("term duration")
            elif any(term in lower_line for term in ['termination', 'end', 'expire']):
                key_terms.append("termination clauses")
            elif any(term in lower_line for term in ['confidential', 'proprietary', 'trade secret']):
                key_terms.append("confidentiality provisions")
        
        # Remove duplicates and limit
        key_terms = list(set(key_terms))[:3]
        
        if key_terms:
            terms_text = ", ".join(key_terms)
            summary = f"This {contract_type} contains {terms_text} and other standard contractual obligations. The document appears to be well-structured with clear terms and conditions."
        else:
            summary = f"This {contract_type} contains standard legal provisions and contractual terms. The document structure follows typical legal formatting conventions."
        
        return summary
    
    def _generate_mock_classification(self, content: str, contract_type: str, confidence: float) -> Dict[str, Any]:
        """Generate mock classification results for demo purposes."""
        # Mock risk assessment based on content analysis
        risk_indicators = []
        content_lower = content.lower()
        
        if 'liability' not in content_lower:
            risk_indicators.append("Missing liability clauses")
        if 'termination' not in content_lower:
            risk_indicators.append("Unclear termination terms")
        if any(term in content_lower for term in ['[', 'xxx', 'tbd', 'to be determined']):
            risk_indicators.append("Contains placeholder text")
        
        risk_level = "high" if len(risk_indicators) > 2 else "medium" if risk_indicators else "low"
        
        classification_result = {
            "document_type": contract_type,
            "confidence_score": float(confidence),
            "risk_assessment": {
                "level": risk_level,
                "indicators": risk_indicators[:3]  # Limit to 3
            },
            "key_elements": self._extract_key_elements(content),
            "completeness_score": self._calculate_completeness_score(content)
        }
        
        return classification_result
    
    def _extract_key_elements(self, content: str) -> list:
        """Extract key contractual elements from content."""
        elements = []
        content_lower = content.lower()
        
        element_mapping = {
            "parties": ["party", "between", "client", "employee", "tenant", "landlord"],
            "compensation": ["salary", "payment", "rent", "fee", "amount"],
            "term": ["term", "period", "duration", "commence", "expire"],
            "obligations": ["duties", "responsibilities", "obligations", "shall"],
            "termination": ["terminate", "termination", "end", "cancel"]
        }
        
        for element, keywords in element_mapping.items():
            if any(keyword in content_lower for keyword in keywords):
                elements.append(element)
        
        return elements
    
    def _calculate_completeness_score(self, content: str) -> float:
        """Calculate a mock completeness score based on content analysis."""
        # Simple heuristic based on content length and key elements
        base_score = min(len(content) / 1000, 0.8)  # Length factor
        
        # Bonus for having key elements
        key_elements = self._extract_key_elements(content)
        element_bonus = len(key_elements) * 0.1
        
        # Penalty for placeholders
        content_lower = content.lower()
        placeholder_penalty = 0
        if any(term in content_lower for term in ['[', 'xxx', 'tbd']):
            placeholder_penalty = 0.2
        
        score = min(base_score + element_bonus - placeholder_penalty, 1.0)
        return round(score, 2)
    
    def _generate_tags(self, classification_result: Dict[str, Any], contract_type: str) -> list:
        """Generate tags based on classification results."""
        tags = []
        
        # Add contract type tag
        tags.append(contract_type.lower().replace(' ', '_'))
        
        # Add risk level tag
        if 'risk_assessment' in classification_result:
            risk_level = classification_result['risk_assessment']['level']
            tags.append(f"risk_{risk_level}")
        
        # Add completeness tag
        if 'completeness_score' in classification_result:
            score = classification_result['completeness_score']
            if score >= 0.8:
                tags.append("complete")
            elif score >= 0.6:
                tags.append("mostly_complete")
            else:
                tags.append("incomplete")
        
        # Add element tags
        if 'key_elements' in classification_result:
            for element in classification_result['key_elements'][:3]:  # Limit to 3
                tags.append(f"has_{element}")
        
        return tags
    
    async def process_demo_document(self, document_type: str = "employment_contract") -> Dict[str, Any]:
        """
        Process a demo document through the full AI pipeline without database persistence.
        
        Args:
            document_type: Type of demo document to process
            
        Returns:
            Dict containing all analysis results
        """
        logger.info(f"[DEMO START] Processing {document_type} demo")
        
        # Get sample document
        if document_type not in self.sample_documents:
            document_type = "employment_contract"  # Default fallback
            
        sample_doc_config = self.sample_documents[document_type]
        base_filename = sample_doc_config["base_filename"]
        
        # Load content and get actual filename
        content, actual_filename = self._load_sample_content(base_filename)
        
        try:
            # Step 1: Contract Validation (same as production)
            logger.info(f"[DEMO VALIDATION] Validating {actual_filename}")
            validation_result = validator.validate(content)
            
            # Step 2: AI Processing (simplified for demo)
            if validation_result.is_valid:
                logger.info(f"[DEMO PROCESSING] Running AI analysis on {actual_filename}")
                
                # Get contract type as string
                contract_type = validation_result.contract_type.value if hasattr(validation_result.contract_type, 'value') else str(validation_result.contract_type)
                
                # Generate mock AI analysis results
                summary = self._generate_mock_summary(content, contract_type)
                classification_result = self._generate_mock_classification(content, contract_type, validation_result.confidence)
                
                # Generate tags
                tags = self._generate_tags(classification_result, contract_type)
                
                # Extract key clauses for demo
                clauses = self._extract_demo_clauses(content, classification_result)
                
                processing_success = True
                rejection_reason = None
                
            else:
                # Handle invalid contract demo
                summary = "This document did not pass our AI validation checks."
                classification_result = {}
                tags = ["validation_failed"]
                clauses = []
                processing_success = False
                rejection_reason = validation_result.message
            
            # Step 3: Build comprehensive response
            demo_response = {
                "title": sample_doc_config["title"],
                "processing_success": processing_success,
                "note": sample_doc_config.get("note"),
                "filename": actual_filename,
                "summary": summary,
                "validation": {
                    "contract_type": validation_result.contract_type.value if hasattr(validation_result.contract_type, 'value') else str(validation_result.contract_type),
                    "confidence": float(validation_result.confidence),
                    "is_valid": validation_result.is_valid
                },
                "classification": classification_result,
                "tags": tags,
                "clauses": clauses,
                "rejection_reason": rejection_reason,
                "demo_metadata": {
                    "document_type": document_type,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "is_demo": True,
                    "source": "file" if self._find_sample_file(base_filename) else "fallback"
                }
            }
            
            logger.info(f"[DEMO SUCCESS] {actual_filename} demo completed")
            logger.info(f"  - Validation: {'PASSED' if processing_success else 'FAILED'}")
            logger.info(f"  - Contract Type: {validation_result.contract_type.value if hasattr(validation_result.contract_type, 'value') else validation_result.contract_type}")
            logger.info(f"  - Confidence: {validation_result.confidence:.2%}")
            logger.info(f"  - Source: {'File' if self._find_sample_file(base_filename) else 'Fallback'}")
            
            return demo_response
            
        except Exception as e:
            logger.error(f"[DEMO ERROR] Failed to process {actual_filename}: {str(e)}")
            return {
                "title": f"Demo Error - {sample_doc_config['title']}",
                "processing_success": False,
                "rejection_reason": f"Demo processing failed: {str(e)}",
                "note": "Demo encountered an error",
                "filename": actual_filename,
                "validation": {},
                "classification": {},
                "tags": ["demo_error"],
                "clauses": [],
                "demo_metadata": {
                    "document_type": document_type,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "is_demo": True,
                    "error": str(e),
                    "source": "error"
                }
            }
    
    def _extract_demo_clauses(self, content: str, classification_result: Dict) -> list:
        """Extract key clauses for demo display."""
        # Simple clause extraction based on common contract patterns
        clauses = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered clauses or important contract terms
            if (line and 
                (line[0].isdigit() or 
                 any(keyword in line.lower() for keyword in 
                     ['compensation', 'payment', 'term', 'termination', 'confidentiality', 
                      'liability', 'warranty', 'intellectual property', 'rent', 'deposit']))):
                if len(line) < 200:  # Keep clauses concise
                    clauses.append(line)
                if len(clauses) >= 5:  # Limit to 5 key clauses
                    break
        
        return clauses[:5] if clauses else ["Key contractual terms and obligations identified"]
    
    def get_available_demos(self) -> Dict[str, Dict[str, str]]:
        """Get list of available demo document types with file status."""
        available_demos = {}
        
        for doc_type, doc_info in self.sample_documents.items():
            base_filename = doc_info["base_filename"]
            file_info = self._find_sample_file(base_filename)
            
            available_demos[doc_type] = {
                "title": doc_info["title"],
                "description": doc_info.get("note", ""),
                "has_sample_file": file_info is not None,
                "filename": file_info[0] if file_info else f"sample_{base_filename}.pdf",
                "source": "file" if file_info else "fallback"
            }
        
        return available_demos

# Global demo service instance
demo_service = DemoService()

# Convenience functions
async def process_demo_document(document_type: str = "employment_contract"):
    """Process a demo document."""
    return await demo_service.process_demo_document(document_type)

def get_available_demos():
    """Get available demo types."""
    return demo_service.get_available_demos()
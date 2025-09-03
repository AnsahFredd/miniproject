# contract_validator.py
import re
from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass
import dateparser 
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from app.core.config import settings

LEGAL_PATH = settings.AI_MODELS.LEGAL_NAME_MODEL

class ContractType(Enum):
    """Enumeration of contract types"""
    LEASE = "lease"
    SERVICE = "service"
    EMPLOYMENT = "employment"
    SALES = "sales"
    NDA = "non_disclosure"
    GENERAL = "general"
    UNKNOWN = "unknown"

@dataclass
class ValidationResult:
    """Result object for contract validation"""
    is_valid: bool
    contract_type: ContractType
    confidence: float
    message: str
    found_elements: List[str]
    missing_elements: List[str]

class LegalContractValidator:
    def __init__(self, model_path: Path = LEGAL_PATH):
        # --- Rule-based legal keywords ---
        self.key_patterns = [
            r"\bparty\b", r"\bagreement\b", r"\bhereinafter\b",
            r"\bshall\b", r"\bwhereas\b", r"\bliability\b",
            r"\bgoverning law\b", r"\bjurisdiction\b"
        ]

        try:
            # Load HuggingFace Legal-BERT Classifier from local path
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        except Exception as e:
            print(f"Warning: Could not load ML model from {model_path}: {e}")
            self.tokenizer = None
            self.model = None

    def _detect_contract_type(self, text: str) -> ContractType:
        """Detect the type of contract based on keywords"""
        text_lower = text.lower()
        
        # Lease/Rental patterns
        lease_keywords = ["lease", "rent", "tenant", "landlord", "property", "premises"]
        if any(keyword in text_lower for keyword in lease_keywords):
            return ContractType.LEASE
            
        # Employment patterns
        employment_keywords = ["employee", "employer", "employment", "job", "salary", "wages"]
        if any(keyword in text_lower for keyword in employment_keywords):
            return ContractType.EMPLOYMENT
            
        # Service patterns
        service_keywords = ["service", "services", "contractor", "client", "work performed"]
        if any(keyword in text_lower for keyword in service_keywords):
            return ContractType.SERVICE
            
        # Sales patterns
        sales_keywords = ["purchase", "sale", "buyer", "seller", "goods", "merchandise"]
        if any(keyword in text_lower for keyword in sales_keywords):
            return ContractType.SALES
            
        # NDA patterns
        nda_keywords = ["confidential", "non-disclosure", "proprietary", "trade secret"]
        if any(keyword in text_lower for keyword in nda_keywords):
            return ContractType.NDA
            
        return ContractType.GENERAL

    def _rule_based_signals(self, text: str) -> Dict[str, Any]:
        keyword_hits = sum(bool(re.search(p, text, re.IGNORECASE)) for p in self.key_patterns)
        return {"keyword_hits": keyword_hits}

    def _modern_signals(self, text: str) -> Dict[str, Any]:
        # Date extraction using dateparser
        words = text.split()
        dates = []
        for i in range(len(words)):
            phrase = " ".join(words[i:i+5])  # Check phrases of up to 5 words
            dt = dateparser.parse(phrase)
            if dt:
                dates.append(str(dt.date()))

        # --- Money extraction using regex ---
        money_terms = re.findall(r"\$\d+(?:,\d{3})*(?:\.\d+)?", text)

        # --- Company detection (simple heuristic) ---
        companies = re.findall(r"\b[A-Z][A-Za-z0-9&,. ]+(?:Inc|LLC|Corp|Ltd)\b", text)

        # --- Constraint detection (keywords) ---
        constraint_keywords = ["shall", "must", "required", "prohibited", "not allowed"]
        constraints = [kw for kw in constraint_keywords if re.search(rf"\b{kw}\b", text, re.IGNORECASE)]

        return {
            "dates": dates,
            "money_terms": money_terms,
            "companies": companies,
            "constraints": constraints
        }

    def _ml_classification(self, text: str) -> float:
        """Return probability that the text is legal using Legal-BERT"""
        if not self.tokenizer or not self.model:
            # Fallback to simple heuristic if ML model not available
            return 0.5
            
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            return float(probs[0][1])  # Assuming index 1 = "legal"
        except Exception as e:
            print(f"Warning: ML classification failed: {e}")
            return 0.5

    def _check_contract_elements(self, text: str) -> tuple[List[str], List[str]]:
        """Check for essential contract elements"""
        found_elements = []
        missing_elements = []
        
        # Check for contract formation language
        formation_patterns = [
            r"\bthis agreement\b", r"\bthis contract\b", r"\bagreement is made\b",
            r"\bcontract is entered\b", r"\bhereby agree\b"
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in formation_patterns):
            found_elements.append("contract_formation")
        else:
            missing_elements.append("contract_formation")
            
        # Check for party identification
        party_patterns = [
            r"\bbetween .+ and .+\b", r"\blandlord\b", r"\btenant\b", 
            r"\bemployer\b", r"\bemployee\b", r"\bbuyer\b", r"\bseller\b"
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in party_patterns):
            found_elements.append("party_identification")
        else:
            missing_elements.append("party_identification")
            
        # Check for legal obligations
        obligation_patterns = [
            r"\bshall pay\b", r"\bmust provide\b", r"\bis required to\b",
            r"\bobliged to\b", r"\bresponsible for\b"
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in obligation_patterns):
            found_elements.append("legal_obligations")
        else:
            missing_elements.append("legal_obligations")
            
        # Check for terms and conditions
        terms_patterns = [
            r"\bterms\b", r"\bconditions\b", r"\bpayment\b", r"\bdeposit\b",
            r"\bduration\b", r"\btermination\b"
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in terms_patterns):
            found_elements.append("substantive_terms")
        else:
            missing_elements.append("substantive_terms")
            
        return found_elements, missing_elements

    def validate(self, text: str) -> ValidationResult:
        """
        Validate if text is a legal contract and return ValidationResult object
        """
        # --- Step 1: Rule-based signals ---
        rule_signals = self._rule_based_signals(text)
        
        # --- Step 2: Modern extraction ---
        modern_signals = self._modern_signals(text)
        
        # --- Step 3: ML Classification ---
        ml_confidence = self._ml_classification(text)
        
        # --- Step 4: Check contract elements ---
        found_elements, missing_elements = self._check_contract_elements(text)
        
        # --- Step 5: Detect contract type ---
        contract_type = self._detect_contract_type(text)
        
        # --- Step 6: Calculate confidence ---
        heuristic_score = rule_signals["keyword_hits"]
        if modern_signals["dates"]: heuristic_score += 1
        if modern_signals["money_terms"]: heuristic_score += 1
        if modern_signals["companies"]: heuristic_score += 1
        if modern_signals["constraints"]: heuristic_score += 1
        
        # Bonus for found contract elements
        heuristic_score += len(found_elements)

        heuristic_conf = min(1.0, heuristic_score / 10)  # Adjusted denominator

        # Weighted combo: 40% heuristics + 60% ML
        final_conf = (0.4 * heuristic_conf) + (0.6 * ml_confidence)
        
        # --- Step 7: Determine validity ---
        # Lower threshold to 0.4 (40%) as mentioned in your requirements
        is_valid = final_conf > 0.4
        
        # Generate message
        if is_valid:
            message = f"Valid {contract_type.value} contract detected with {final_conf:.1%} confidence"
        else:
            message = f"Invalid legal contract: confidence too low ({final_conf:.1%}). Missing: {', '.join(missing_elements[:3])}"
        
        return ValidationResult(
            is_valid=is_valid,
            contract_type=contract_type,
            confidence=round(final_conf, 3),
            message=message,
            found_elements=found_elements,
            missing_elements=missing_elements
        )
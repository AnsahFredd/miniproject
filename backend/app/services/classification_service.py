import os
import re
import logging
from typing import Dict, List, Optional, Tuple

from app.utils.hf_cache import load_pipeline_with_cache
from app.core.runtime import setup_runtime

setup_runtime()
logger = logging.getLogger(__name__)

# Prefer env override; otherwise settings; else default repo id for your custom model
try:
    from core.config import settings
except Exception:
    settings = None

def resolve_primary_model() -> str:
    env_id = os.getenv("CLASSIFICATION_MODEL")
    if env_id:
        return env_id
    if settings and getattr(settings, "CLASSIFICATION_MODEL", None):
        return str(settings.CLASSIFICATION_MODEL)
    # If you had a custom repo, set it here or use a small default to avoid memory spikes
    return "distilbert-base-uncased-finetuned-sst-2-english"

def resolve_alt_model() -> str:
    env_id = os.getenv("CLASSIFICATION_MODEL_PATH")
    if env_id:
        return env_id
    if settings and getattr(settings, "CLASSIFICATION_MODEL_PATH", None):
        return str(settings.CLASSIFICATION_MODEL_PATH)
    return "nlpaueb/legal-bert-base-uncased"

PRIMARY_ID = resolve_primary_model()
FALLBACKS = [resolve_alt_model(), "nlpaueb/legal-bert-base-uncased"]

class DocumentClassificationService:
    def __init__(self):
        self.classification_pipeline = None
        self.document_types = {
            'contract': ['contract', 'agreement', 'deed', 'covenant', 'compact'],
            'lease': ['lease', 'rental', 'tenancy', 'rent'],
            'legal_brief': ['brief', 'motion', 'petition', 'complaint', 'pleading'],
            'policy': ['policy', 'procedure', 'guideline', 'standard', 'protocol'],
            'regulation': ['regulation', 'statute', 'law', 'code', 'ordinance'],
            'financial': ['invoice', 'receipt', 'financial', 'budget', 'statement'],
            'correspondence': ['letter', 'memo', 'email', 'correspondence', 'notice'],
            'report': ['report', 'analysis', 'study', 'review', 'assessment'],
            'general': []
        }
        self.urgency_keywords = {
            'high': ['urgent', 'immediate', 'critical', 'emergency', 'deadline', 'expires'],
            'medium': ['important', 'priority', 'attention', 'review', 'action required'],
            'low': ['information', 'fyi', 'reference', 'notice', 'update']
        }
        self.legal_domains = {
            'real_estate': ['property', 'real estate', 'lease', 'rent', 'landlord', 'tenant'],
            'corporate': ['corporation', 'company', 'business', 'merger', 'acquisition'],
            'employment': ['employment', 'employee', 'worker', 'job', 'salary', 'benefits'],
            'intellectual_property': ['patent', 'trademark', 'copyright', 'ip', 'invention'],
            'litigation': ['lawsuit', 'court', 'judge', 'trial', 'plaintiff', 'defendant'],
            'compliance': ['compliance', 'regulation', 'audit', 'violation', 'penalty'],
            'general': []
        }
        logger.info(f"ClassificationService initialized. Primary: {PRIMARY_ID}, fallbacks: {FALLBACKS}")

    def _ensure_model(self):
        if self.classification_pipeline is not None:
            return
        pl, used = load_pipeline_with_cache(
            "text-classification",
            PRIMARY_ID,
            fallbacks=FALLBACKS,
            device=-1,
        )
        self.classification_pipeline = pl
        if pl is None:
            logger.warning("Classification model unavailable; will use rule-based classification only.")
        elif used and used != PRIMARY_ID:
            logger.warning(f"ClassificationService fell back to {used}")

    def classify_document(self, content: str, filename: str = "") -> Dict:
        if not content or len(content.strip()) < 50:
            return self._get_fallback_classification(content or "", filename)

        self._ensure_model()

        # Try ML model, then rules as enhancement
        ml_result = {"document_type": "unknown", "document_type_confidence": 0.0}
        try:
            if self.classification_pipeline:
                truncated = content[:2000]  # keep CPU memory bounded
                result = self.classification_pipeline(truncated)
                if isinstance(result, list) and result:
                    pred = result[0]
                    label = pred.get("label", "unknown").lower()
                    score = float(pred.get("score", 0.0))
                    ml_result = {
                        "document_type": self._map_model_label_to_type(label),
                        "document_type_confidence": score,
                        "model_label": label,
                        "raw_prediction": result,
                        "classification_method": "ml_model",
                    }
        except Exception as e:
            logger.warning(f"ML classification failed: {e}")

        rule_result = self._classify_with_rules(content, filename)
        # Prefer ML if confident
        if ml_result["document_type_confidence"] > 0.7:
            ml_result.update({k: v for k, v in rule_result.items() if k not in ml_result})
            return ml_result
        # Else rely mostly on rules
        rule_result["classification_method"] = "rule_based"
        return rule_result

    def _classify_with_rules(self, content: str, filename: str = "") -> Dict:
        text = (content or "").lower() + " " + (filename or "").lower()
        # Document type
        doc_scores = {t: sum(1 for kw in kws if kw in text) for t, kws in self.document_types.items()}
        best_type = max(doc_scores.items(), key=lambda x: x[1]) if doc_scores else ("general", 0)
        doc_conf = min(best_type[1] / 3.0, 1.0)

        # Domain
        dom_scores = {t: sum(1 for kw in kws if kw in text) for t, kws in self.legal_domains.items()}
        best_dom = max(dom_scores.items(), key=lambda x: x[1]) if dom_scores else ("general", 0)
        dom_conf = min(best_dom[1] / 2.0, 1.0)

        # Urgency
        urg_scores = {t: sum(1 for kw in kws if kw in text) for t, kws in self.urgency_keywords.items()}
        best_urg = max(urg_scores.items(), key=lambda x: x[1]) if urg_scores else ("low", 0)
        urg_conf = min(best_urg[1] / 2.0, 1.0)

        entities = self._extract_legal_entities(content or "")

        return {
            "document_type": best_type[0],
            "document_type_confidence": doc_conf,
            "legal_domain": best_dom[0],
            "legal_domain_confidence": dom_conf,
            "urgency": best_urg[0],
            "urgency_confidence": urg_conf,
            "extracted_entities": entities,
        }

    def _extract_legal_entities(self, content: str) -> List[Dict]:
        entities: List[Dict] = []
        # Dates
        date_re = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        for d in re.findall(date_re, content, re.IGNORECASE)[:5]:
            entities.append({"type": "date", "value": d})
        # Money
        for m in re.findall(r'\$[\d,]+(?:\.\d{2})?', content)[:5]:
            entities.append({"type": "money", "value": m})
        # Roles
        role_patterns = {
            'party': r'(?:plaintiff|defendant|appellant|appellee|petitioner|respondent)',
            'legal_entity': r'(?:corporation|llc|inc\.|company|firm)',
            'court': r'(?:court|tribunal|judge|magistrate)'
        }
        for et, pat in role_patterns.items():
            for v in re.findall(pat, content, re.IGNORECASE)[:3]:
                entities.append({"type": et, "value": v})
        return entities

    def _map_model_label_to_type(self, label: str) -> str:
        mapping = {
            'contract': 'contract',
            'agreement': 'contract',
            'lease': 'lease',
            'brief': 'legal_brief',
            'motion': 'legal_brief',
            'policy': 'policy',
            'regulation': 'regulation',
            'financial': 'financial',
            'correspondence': 'correspondence',
            'report': 'report',
        }
        return mapping.get(label, 'general')

    def _get_fallback_classification(self, content: str, filename: str) -> Dict:
        fname = (filename or "").lower()
        if 'contract' in fname or 'agreement' in fname:
            doc_type = 'contract'
        elif 'lease' in fname:
            doc_type = 'lease'
        elif 'brief' in fname or 'motion' in fname:
            doc_type = 'legal_brief'
        elif len(content.strip()) > 5000:
            doc_type = 'report'
        else:
            doc_type = 'general'
        return {
            'document_type': doc_type,
            'document_type_confidence': 0.3,
            'legal_domain': 'general',
            'legal_domain_confidence': 0.0,
            'urgency': 'low',
            'urgency_confidence': 0.0,
            'extracted_entities': [],
            'classification_method': 'fallback'
        }

    def get_model_info(self) -> dict:
        return {
            "primary": PRIMARY_ID,
            "fallbacks": FALLBACKS,
            "loaded": self.classification_pipeline is not None,
            "task": "text-classification",
            "cache_dir": os.getenv("TRANSFORMERS_CACHE"),
        }

classification_service = DocumentClassificationService()

def classify_document(content: str, filename: str = "") -> Dict:
    return classification_service.classify_document(content, filename)
